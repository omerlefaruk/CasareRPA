<rules category="ui">
  <popup id="popup-lifecycle" priority="normal">
    <name>Popup Window Rules</name>

    <base_class>
      <import>from ui.widgets.popups import PopupWindowBase</import>
      <features>Draggable, resizable, click-outside-to-close</features>
      <location>@src/casare_rpa/presentation/canvas/ui/widgets/popups/</location>
    </base_class>

    <lifecycle>
      <event name="showEvent">
        <action>PopupManager.register(self)</action>
        <optional>PopupManager.register(self, pinned=True) for pinned popups</optional>
      </event>
      <event name="closeEvent">
        <action>PopupManager.unregister(self)</action>
      </event>
    </lifecycle>

    <popup_manager>
      <file>@src/casare_rpa/presentation/canvas/managers/popup_manager.py</file>
      <purpose>Centralized click-outside-to-close handling</purpose>
      <features>
        <feature>Single app-level event filter (efficient)</feature>
        <feature>WeakSet for automatic cleanup</feature>
        <feature>Pin state support</feature>
        <feature>close_popup(), close_all_popups() helpers</feature>
      </features>
    </popup_manager>

    <variants>
      <variant>ContextMenu</variant>
      <variant>Dropdown</variant>
      <variant>Tooltip</variant>
      <variant>Toast</variant>
      <variant>Inspector</variant>
      <variant>Autocomplete</variant>
    </variants>

    <references>
      <ref>@.claude/rules/ui/popup-rules.md</ref>
      <ref>@docs/agent/ui-popup.md</ref>
      <ref>@src/casare_rpa/presentation/canvas/_index.md (popup_manager section)</ref>
    </references>
  </popup>
</rules>
