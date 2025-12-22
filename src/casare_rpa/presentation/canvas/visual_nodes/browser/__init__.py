"""
Visual Nodes - Browser
"""

from casare_rpa.presentation.canvas.visual_nodes.browser.nodes import (
    VisualLaunchBrowserNode,
    VisualCloseBrowserNode,
    VisualNewTabNode,
    VisualGetAllImagesNode,
    VisualDownloadFileNode,
    VisualGoToURLNode,
    VisualGoBackNode,
    VisualGoForwardNode,
    VisualRefreshPageNode,
    VisualClickElementNode,
    VisualTypeTextNode,
    VisualSelectDropdownNode,
    VisualImageClickNode,
    VisualPressKeyNode,
    VisualExtractTextNode,
    VisualGetAttributeNode,
    VisualScreenshotNode,
    VisualTableScraperNode,
    VisualWaitNode,
    VisualWaitForElementNode,
    VisualWaitForNavigationNode,
    VisualFormFieldNode,
    VisualFormFillerNode,
    VisualDetectFormsNode,
)
from casare_rpa.presentation.canvas.visual_nodes.browser.evaluate_node import (
    VisualBrowserEvaluateNode,
)
from casare_rpa.presentation.canvas.visual_nodes.browser.scripting import (
    VisualBrowserRunScriptNode,
)
from casare_rpa.presentation.canvas.visual_nodes.browser.captcha import (
    VisualDetectCaptchaNode,
    VisualSolveCaptchaNode,
    VisualSolveCaptchaAINode,
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
