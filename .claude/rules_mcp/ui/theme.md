<rules category="ui">
  <theme id="theme-only" priority="critical">
    <name>Theme System Rules</name>

    <constraint>
      <rule>Use THEME.* constants ONLY</rule>
      <forbidden>NO hardcoded hex colors</forbidden>
      <location>@src/casare_rpa/presentation/canvas/theme.py</location>
    </constraint>

    <usage>
      <correct>color = THEME.ACCENT_PRIMARY</correct>
      <wrong>color = "#007ACC"</wrong>
      <wrong>color = "blue"</wrong>
    </usage>

    <token_access>
      <two_level_cache>
        <level>Memory: Module-level cache in theme.py</level>
        <level>Disk: stylesheet_cache.py with version invalidation</level>
      </two_level_cache>
      <getter>from casare_rpa.presentation.canvas.theme import THEME, TOKENS</getter>
    </token_access>

    <v2_tokens>
      <file>@src/casare_rpa/presentation/canvas/theme_system/tokens_v2.py</file>
      <purpose>Design system tokens (dark-only, compact)</purpose>
    </v2_tokens>

    <references>
      <ref>@.claude/rules/ui/theme-rules.md</ref>
      <ref>@docs/agent/ui-theme.md</ref>
      <ref>@src/casare_rpa/presentation/canvas/_index.md (theme_system section)</ref>
    </references>
  </theme>

  <fonts>
    <rule>Use bundled Geist Sans/Mono fonts</rule>
    <loader>@src/casare_rpa/presentation/canvas/theme_system/font_loader.py</loader>
    <families>
      <sans>GEIST_SANS_FAMILY = "Geist Sans"</sans>
      <mono>GEIST_MONO_FAMILY = "Geist Mono"</mono>
    </families>
    <fallback>Segoe UI (sans), Cascadia Code (mono)</fallback>
    <usage>ensure_font_registered() before QApplication creates widgets</usage>
  </fonts>
</rules>
