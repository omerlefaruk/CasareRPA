<rule id="domain-purity" priority="critical">
  <name>Domain Purity</name>
  <description>Domain layer has ZERO external dependencies</description>

  <principles>
    <principle>No imports from Infrastructure or Presentation</principle>
    <principle>No I/O operations (file, network, database)</principle>
    <principle>Framework agnostic (No PySide6, Playwright, aiohttp)</principle>
    <principle>Testable in isolation (no mocks required)</principle>
  </principles>

  <layer_boundaries>
    <boundary>
      <layer>Domain</layer>
      <may_import>Nothing external</may_import>
    </boundary>
    <boundary>
      <layer>Application</layer>
      <may_import>Domain only</may_import>
    </boundary>
    <boundary>
      <layer>Infrastructure</layer>
      <may_import>Domain, external libs</may_import>
    </boundary>
    <boundary>
      <layer>Presentation</layer>
      <may_import>Domain, Application</may_import>
    </boundary>
  </layer_boundaries>

  <references>
    <ref>@src/casare_rpa/domain/_index.md</ref>
    <ref>@.claude/rules/06-enforcement.md</ref>
  </references>
</rule>
