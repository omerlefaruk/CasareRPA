"""
Visual Nodes - Browser
"""

from casare_rpa.presentation.canvas.visual_nodes.browser.captcha import (
    VisualDetectCaptchaNode,
    VisualSolveCaptchaAINode,
    VisualSolveCaptchaNode,
)
from casare_rpa.presentation.canvas.visual_nodes.browser.evaluate_node import (
    VisualBrowserEvaluateNode,
)
from casare_rpa.presentation.canvas.visual_nodes.browser.nodes import (
    VisualClickElementNode,
    VisualCloseBrowserNode,
    VisualDetectFormsNode,
    VisualDownloadFileNode,
    VisualExtractTextNode,
    VisualFormFieldNode,
    VisualFormFillerNode,
    VisualGetAllImagesNode,
    VisualGetAttributeNode,
    VisualGoBackNode,
    VisualGoForwardNode,
    VisualGoToURLNode,
    VisualImageClickNode,
    VisualLaunchBrowserNode,
    VisualNewTabNode,
    VisualPressKeyNode,
    VisualRefreshPageNode,
    VisualScreenshotNode,
    VisualSelectDropdownNode,
    VisualTableScraperNode,
    VisualTypeTextNode,
    VisualWaitForElementNode,
    VisualWaitForNavigationNode,
    VisualWaitNode,
)
from casare_rpa.presentation.canvas.visual_nodes.browser.scripting import (
    VisualBrowserRunScriptNode,
)

__all__ = [
    "VisualLaunchBrowserNode",
    "VisualCloseBrowserNode",
    "VisualNewTabNode",
    "VisualGetAllImagesNode",
    "VisualDownloadFileNode",
    "VisualGoToURLNode",
    "VisualGoBackNode",
    "VisualGoForwardNode",
    "VisualRefreshPageNode",
    "VisualClickElementNode",
    "VisualTypeTextNode",
    "VisualSelectDropdownNode",
    "VisualImageClickNode",
    "VisualPressKeyNode",
    "VisualExtractTextNode",
    "VisualGetAttributeNode",
    "VisualScreenshotNode",
    "VisualTableScraperNode",
    "VisualWaitNode",
    "VisualWaitForElementNode",
    "VisualWaitForNavigationNode",
    "VisualFormFieldNode",
    "VisualFormFillerNode",
    "VisualDetectFormsNode",
    "VisualBrowserEvaluateNode",
    "VisualBrowserRunScriptNode",
    # CAPTCHA
    "VisualDetectCaptchaNode",
    "VisualSolveCaptchaNode",
    "VisualSolveCaptchaAINode",
]
