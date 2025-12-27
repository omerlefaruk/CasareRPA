# Browser Package Index

```xml<browser_index>
  <!-- Browser automation base classes and utilities. -->

  <files>
    <f>__init__.py</f>             <e>BrowserBaseNode, get_page_from_context</e>
    <f>browser_base.py</f>         <e>BrowserBaseNode</e>
    <f>property_constants.py</f>   <e>BROWSER_TIMEOUT, BROWSER_SELECTOR</e>
    <f>smart_selector_node.py</f>  <e>SmartSelectorNode</e>
    <f>form_filler_node.py</f>      <e>FormFillerNode</e>
    <f>table_scraper_node.py</f>    <e>TableScraperNode</e>
    <f>evaluate_node.py</f>        <e>BrowserEvaluateNode</e>
    <f>detect_forms_node.py</f>     <e>DetectFormsNode</e>
    <f>visual_find_node.py</f>      <e>VisualFindNode</e>
  </files>

  <entry_points>
    <code>
from casare_rpa.nodes.browser import (
    BrowserBaseNode,
    get_page_from_context,
    take_failure_screenshot,
    BROWSER_TIMEOUT,
    BROWSER_SELECTOR,
)
    </code>
  </entry_points>

  <patterns>
    <p>1. Extend BrowserBaseNode</p>
    <p>2. Use get_page_from_context(context) for page access</p>
    <p>3. Use property constants for common settings</p>
    <p>4. Call take_failure_screenshot on errors</p>
  </patterns>
</browser_index>
```
