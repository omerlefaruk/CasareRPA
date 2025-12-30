<rule id="index-first" priority="critical">
  <name>INDEX-FIRST Rule</name>
  <description>Always read _index.md before searching code</description>

  <workflow>
    <step order="1">Read relevant _index.md for overview</step>
    <step order="2">Search __init__.py to find exact module</step>
    <step order="3">Read specific file - only what's needed</step>
  </workflow>

  <prohibited>
    <action>NEVER grep/glob before checking index</action>
    <action>NEVER read entire files when _index.md has the answer</action>
  </prohibited>

  <references>
    <ref>@src/casare_rpa/domain/_index.md</ref>
    <ref>@src/casare_rpa/nodes/_index.md</ref>
    <ref>@src/casare_rpa/application/_index.md</ref>
    <ref>@src/casare_rpa/infrastructure/_index.md</ref>
    <ref>@src/casare_rpa/presentation/canvas/_index.md</ref>
  </references>
</rule>
