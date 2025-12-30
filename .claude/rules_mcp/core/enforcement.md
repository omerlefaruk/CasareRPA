<rule id="enforcement" priority="critical">
  <name>Hard Constraints</name>
  <description>Non-negotiable rules - NEVER violate</description>

  <constraints>
    <constraint id="domain-priority">
      <rule>Domain: No infrastructure/presentation imports</rule>
      <penalty>Architectural violation - must fix</penalty>
    </constraint>

    <constraint id="no-silent-failures">
      <rule>ALL external calls in try/except</rule>
      <rule>Log with context (loguru): what, failed, recovery</rule>
    </constraint>

    <constraint id="http-only">
      <rule>Use UnifiedHttpClient ONLY</rule>
      <forbidden>httpx, aiohttp, requests (raw)</forbidden>
      <location>@src/casare_rpa/infrastructure/http/</location>
    </constraint>

    <constraint id="no-secrets">
      <rule>NEVER commit credentials/tokens</rule>
      <rule>Use environment variables or Vault</rule>
    </constraint>

    <constraint id="async-first">
      <rule>No blocking I/O in async contexts</rule>
      <rule>Playwright ops MUST be async</rule>
    </constraint>

    <constraint id="theme-only">
      <rule>UI: Use THEME.* constants</rule>
      <forbidden>No hardcoded hex colors</forbidden>
      <location>@src/casare_rpa/presentation/canvas/theme.py</location>
    </constraint>

    <constraint id="qt-slots">
      <rule>Qt: @Slot required for all signal handlers</rule>
      <forbidden>No lambdas as signal handlers</forbidden>
    </constraint>

    <constraint id="node-schema">
      <rule>Nodes: Use @properties + get_parameter()</rule>
      <forbidden>NO self.config.get() calls</forbidden>
    </constraint>

    <constraint id="typed-events">
      <rule>Events: Frozen dataclass domain events only</rule>
      <location>@src/casare_rpa/domain/events/</location>
    </constraint>
  </constraints>

  <destructive_commands>
    <command status="forbidden">git reset --hard</command>
    <command status="forbidden">git checkout --</command>
    <command status="forbidden">rm -rf</command>
    <exception>Explicit user request only</exception>
  </destructive_commands>
</rule>
