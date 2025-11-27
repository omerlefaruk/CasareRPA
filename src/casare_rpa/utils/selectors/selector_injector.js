/**
 * CasareRPA Element Selector - Browser Injector
 * UiPath-style element picker with recording capabilities
 * Injected via Playwright for seamless integration
 */

(function() {
    'use strict';

    // Prevent double injection
    if (window.__casareRPA_selector_injected) return;
    window.__casareRPA_selector_injected = true;

    // State management
    const state = {
        active: false,
        recording: false,
        recordedActions: [],
        hoveredElement: null,
        selectedElements: [],
        overlay: null,
        highlightBox: null,
        infoPanel: null,
        recordingBadge: null,
        recordingStartTime: null
    };

    // Styles (UiPath-inspired)
    const styles = `
        .casare-selector-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.1);
            z-index: 2147483646;
            pointer-events: none;
        }

        .casare-highlight-box {
            position: absolute;
            border: 3px solid #ff6b35;
            background: rgba(255, 107, 53, 0.15);
            box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.8),
                        0 0 20px rgba(255, 107, 53, 0.6);
            pointer-events: none;
            z-index: 2147483647;
            transition: all 0.1s ease;
            box-sizing: border-box;
        }

        .casare-highlight-box.selected {
            border-color: #4caf50;
            background: rgba(76, 175, 80, 0.2);
            box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.8),
                        0 0 20px rgba(76, 175, 80, 0.6);
        }

        .casare-info-panel {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 16px 20px;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
            font-family: 'Segoe UI', Tahoma, sans-serif;
            font-size: 13px;
            z-index: 2147483647;
            min-width: 280px;
            backdrop-filter: blur(10px);
        }

        .casare-info-panel .title {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .casare-info-panel .title .icon {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.3);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
        }

        .casare-info-panel .recording-indicator {
            animation: pulse 1.5s ease-in-out infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .casare-info-panel .element-info {
            background: rgba(255, 255, 255, 0.15);
            padding: 8px 12px;
            border-radius: 6px;
            margin-top: 8px;
            font-size: 12px;
            font-family: 'Consolas', monospace;
            word-break: break-all;
        }

        .casare-info-panel .actions {
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid rgba(255, 255, 255, 0.2);
            font-size: 11px;
            line-height: 1.6;
        }

        .casare-info-panel .hotkey {
            background: rgba(255, 255, 255, 0.2);
            padding: 2px 6px;
            border-radius: 3px;
            font-family: monospace;
            font-weight: 600;
        }

        .casare-recording-badge {
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: #f44336;
            color: white;
            padding: 12px 24px;
            border-radius: 24px;
            font-family: 'Segoe UI', Tahoma, sans-serif;
            font-size: 14px;
            font-weight: 600;
            box-shadow: 0 4px 20px rgba(244, 67, 54, 0.5);
            z-index: 2147483647;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .casare-recording-badge .dot {
            width: 10px;
            height: 10px;
            background: white;
            border-radius: 50%;
            animation: pulse 1s ease-in-out infinite;
        }
    `;

    // XPath generation (optimized for uniqueness and stability)
    function generateXPath(element) {
        // Try to find unique attributes first
        if (element.id) {
            return `//*[@id="${element.id}"]`;
        }

        if (element.name && element.tagName.toLowerCase() === 'input') {
            const xpath = `//${element.tagName.toLowerCase()}[@name="${element.name}"]`;
            if (document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue === element) {
                return xpath;
            }
        }

        // Check for unique data-testid or data-test
        if (element.dataset.testid) {
            return `//*[@data-testid="${element.dataset.testid}"]`;
        }
        if (element.dataset.test) {
            return `//*[@data-test="${element.dataset.test}"]`;
        }

        // Build path from root
        const segments = [];
        let current = element;

        while (current && current.nodeType === Node.ELEMENT_NODE) {
            let index = 1;
            let sibling = current.previousSibling;

            while (sibling) {
                if (sibling.nodeType === Node.ELEMENT_NODE && sibling.tagName === current.tagName) {
                    index++;
                }
                sibling = sibling.previousSibling;
            }

            const tagName = current.tagName.toLowerCase();
            const segment = index > 1 ? `${tagName}[${index}]` : tagName;
            segments.unshift(segment);

            current = current.parentElement;

            // Stop at body to avoid full path
            if (current && current.tagName === 'BODY') {
                segments.unshift('body');
                break;
            }
        }

        return '//' + segments.join('/');
    }

    // Generate multiple selector strategies
    function generateSelectors(element) {
        const selectors = {
            xpath: generateXPath(element),
            css: null,
            aria: null,
            text: null,
            attributes: {}
        };

        // CSS selector
        try {
            let cssPath = element.tagName.toLowerCase();
            if (element.id) {
                cssPath = `#${element.id}`;
            } else if (element.className) {
                const classes = Array.from(element.classList)
                    .filter(c => c && !c.includes(' '))
                    .slice(0, 3)
                    .join('.');
                if (classes) cssPath += `.${classes}`;
            }
            selectors.css = cssPath;
        } catch (e) {
            console.error('CSS selector generation failed:', e);
        }

        // ARIA selectors
        if (element.getAttribute('role')) {
            selectors.aria = `//*[@role="${element.getAttribute('role')}"]`;
        }
        if (element.getAttribute('aria-label')) {
            selectors.attributes['aria-label'] = element.getAttribute('aria-label');
        }

        // Text content
        const text = element.textContent?.trim().substring(0, 50);
        if (text) {
            selectors.text = text;
        }

        // Collect important attributes
        ['type', 'name', 'value', 'placeholder', 'title', 'href'].forEach(attr => {
            const val = element.getAttribute(attr);
            if (val) selectors.attributes[attr] = val;
        });

        return selectors;
    }

    // Get element information
    function getElementInfo(element) {
        return {
            tagName: element.tagName.toLowerCase(),
            id: element.id || null,
            className: element.className || null,
            text: element.textContent?.trim().substring(0, 100) || null,
            attributes: Object.fromEntries(
                Array.from(element.attributes).map(attr => [attr.name, attr.value])
            ),
            rect: element.getBoundingClientRect(),
            selectors: generateSelectors(element)
        };
    }

    // Create UI elements
    function createOverlay() {
        if (state.overlay) return;

        // Inject styles
        const styleEl = document.createElement('style');
        styleEl.textContent = styles;
        document.head.appendChild(styleEl);

        // Create overlay
        state.overlay = document.createElement('div');
        state.overlay.className = 'casare-selector-overlay';
        document.body.appendChild(state.overlay);

        // Create highlight box
        state.highlightBox = document.createElement('div');
        state.highlightBox.className = 'casare-highlight-box';
        document.body.appendChild(state.highlightBox);

        // Create info panel
        state.infoPanel = document.createElement('div');
        state.infoPanel.className = 'casare-info-panel';
        state.infoPanel.innerHTML = `
            <div class="title">
                <span class="icon">🎯</span>
                <span>${state.recording ? 'Recording Actions' : 'Select Element'}</span>
            </div>
            <div class="element-info" id="casare-element-display">
                Hover over an element to inspect
            </div>
            <div class="actions">
                <div><span class="hotkey">Click</span> to select element</div>
                <div><span class="hotkey">Esc</span> to cancel</div>
                ${state.recording ? '<div><span class="hotkey">Ctrl+R</span> stop recording</div>' : ''}
            </div>
        `;
        document.body.appendChild(state.infoPanel);

        // Recording badge
        if (state.recording) {
            state.recordingBadge = document.createElement('div');
            state.recordingBadge.className = 'casare-recording-badge recording-indicator';
            state.recordingBadge.innerHTML = '<div class="dot"></div> RECORDING • 0 actions • 0:00';
            document.body.appendChild(state.recordingBadge);

            state.recordingStartTime = Date.now();

            // Update timer every second
            state.recordingTimer = setInterval(updateRecordingBadge, 1000);
        }
    }

    function removeOverlay() {
        if (state.overlay) {
            state.overlay.remove();
            state.overlay = null;
        }
        if (state.highlightBox) {
            state.highlightBox.remove();
            state.highlightBox = null;
        }
        if (state.infoPanel) {
            state.infoPanel.remove();
            state.infoPanel = null;
        }
        if (state.recordingBadge) {
            state.recordingBadge.remove();
            state.recordingBadge = null;
        }
        if (state.recordingTimer) {
            clearInterval(state.recordingTimer);
            state.recordingTimer = null;
        }
        document.querySelectorAll('.casare-recording-badge').forEach(el => el.remove());
    }

    // Update highlight position
    function updateHighlight(element) {
        if (!state.highlightBox || !element) return;

        const rect = element.getBoundingClientRect();
        const scrollX = window.pageXOffset || document.documentElement.scrollLeft;
        const scrollY = window.pageYOffset || document.documentElement.scrollTop;

        state.highlightBox.style.left = (rect.left + scrollX) + 'px';
        state.highlightBox.style.top = (rect.top + scrollY) + 'px';
        state.highlightBox.style.width = rect.width + 'px';
        state.highlightBox.style.height = rect.height + 'px';
        state.highlightBox.style.display = 'block';
    }

    // Update info panel
    function updateInfoPanel(element) {
        if (!state.infoPanel) return;

        const display = document.getElementById('casare-element-display');
        if (!display) return;

        const tag = element.tagName.toLowerCase();
        const id = element.id ? `#${element.id}` : '';
        const classes = element.className ? `.${Array.from(element.classList).slice(0, 2).join('.')}` : '';

        display.textContent = `<${tag}${id}${classes}>`;
    }

    // Event handlers
    function handleMouseMove(e) {
        if (!state.active) return;

        const element = e.target;
        if (element === state.overlay || element === state.highlightBox ||
            element === state.infoPanel || state.infoPanel?.contains(element)) {
            return;
        }

        state.hoveredElement = element;
        updateHighlight(element);
        updateInfoPanel(element);
    }

    function handleClick(e) {
        if (!state.active) return;

        e.preventDefault();
        e.stopPropagation();

        const element = state.hoveredElement;
        if (!element) return;

        const elementInfo = getElementInfo(element);

        if (state.recording) {
            // Record click action
            recordAction('click', element, elementInfo);

            // Visual feedback
            state.highlightBox.classList.add('selected');
            setTimeout(() => {
                state.highlightBox.classList.remove('selected');
            }, 300);

            // Update badge count
            updateRecordingBadge();
        } else {
            // Single selection mode - send to Python
            if (window.__casareRPA_onElementSelected) {
                window.__casareRPA_onElementSelected(elementInfo);
            }
            deactivate();
        }
    }

    // Record an action during recording mode
    function recordAction(actionType, element, elementInfo) {
        const action = {
            action: actionType,
            element: elementInfo,
            timestamp: Date.now(),
            value: null
        };

        // Capture value for input elements
        if (actionType === 'type' && (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA')) {
            action.value = element.value;
        } else if (actionType === 'select' && element.tagName === 'SELECT') {
            action.value = element.value;
        }

        state.recordedActions.push(action);

        // Notify Python of new action
        if (window.__casareRPA_onActionRecorded) {
            window.__casareRPA_onActionRecorded(action);
        }

        console.log('[CasareRPA] Recorded action:', actionType, elementInfo.selectors.xpath);
    }

    // Setup input monitoring for recording mode
    function setupInputMonitoring() {
        // Track input changes
        document.addEventListener('input', function(e) {
            if (!state.recording) return;

            const element = e.target;
            if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                // Debounce - only record after user stops typing for 500ms
                clearTimeout(element._recordingTimeout);
                element._recordingTimeout = setTimeout(() => {
                    if (element.value) {
                        const elementInfo = getElementInfo(element);
                        recordAction('type', element, elementInfo);
                    }
                }, 500);
            }
        }, true);

        // Track select changes
        document.addEventListener('change', function(e) {
            if (!state.recording) return;

            const element = e.target;
            if (element.tagName === 'SELECT') {
                const elementInfo = getElementInfo(element);
                recordAction('select', element, elementInfo);
            }
        }, true);
    }

    // Update recording badge with action count and timer
    function updateRecordingBadge() {
        if (!state.recordingBadge) return;

        const count = state.recordedActions.length;
        const duration = Math.floor((Date.now() - state.recordingStartTime) / 1000);
        const minutes = Math.floor(duration / 60);
        const seconds = duration % 60;
        const timeStr = `${minutes}:${seconds.toString().padStart(2, '0')}`;

        state.recordingBadge.innerHTML = `
            <div class="dot"></div>
            RECORDING • ${count} actions • ${timeStr}
        `;
    }

    function handleKeyDown(e) {
        if (!state.active) return;

        if (e.key === 'Escape') {
            e.preventDefault();
            if (state.recording) {
                stopRecording(false); // Cancel recording
            } else {
                deactivate();
            }
        } else if (e.ctrlKey && e.key === 'r' && state.recording) {
            e.preventDefault();
            stopRecording(true); // Save recording
        }
    }

    // Activation/Deactivation
    function activate(recordingMode = false) {
        if (state.active) return;

        state.active = true;
        state.recording = recordingMode;
        state.recordedActions = [];

        createOverlay();

        // Capture events
        document.addEventListener('mousemove', handleMouseMove, true);
        document.addEventListener('click', handleClick, true);
        document.addEventListener('keydown', handleKeyDown, true);

        // Setup input monitoring for recording mode
        if (recordingMode) {
            setupInputMonitoring();
        }

        console.log('[CasareRPA] Selector mode activated', { recording: recordingMode });
    }

    function deactivate() {
        if (!state.active) return;

        state.active = false;
        state.recording = false;
        state.hoveredElement = null;

        removeOverlay();

        document.removeEventListener('mousemove', handleMouseMove, true);
        document.removeEventListener('click', handleClick, true);
        document.removeEventListener('keydown', handleKeyDown, true);

        console.log('[CasareRPA] Selector mode deactivated');
    }

    function stopRecording(save = true) {
        if (!state.recording) return;

        const actions = save ? state.recordedActions : [];

        if (window.__casareRPA_onRecordingComplete) {
            window.__casareRPA_onRecordingComplete(actions);
        }

        deactivate();
    }

    // Expose API to window
    window.__casareRPA = {
        selector: {
            activate,
            deactivate,
            stopRecording,
            isActive: () => state.active,
            isRecording: () => state.recording
        }
    };

    console.log('[CasareRPA] Element selector injected successfully');
})();
