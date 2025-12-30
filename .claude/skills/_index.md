# Skills Index

```xml
<skills_index>
  <!-- CasareRPA skills follow skill-creator patterns -->
  <!-- Progressive disclosure: metadata always loaded, SKILL.md on trigger, references/ on demand -->

  <skills>
    <!-- Workflow & Node Development -->
    <skill name="test-generator">Generate comprehensive pytest test suites for CasareRPA components (nodes, controllers, use cases, domain entities). Use when: creating tests, testing new nodes, test coverage needed.</skill>
    <skill name="node-template-generator">Generate boilerplate code for new CasareRPA automation nodes. Use when: creating new nodes, adding node categories, implementing BaseNode patterns.</skill>
    <skill name="workflow-validator">Validate CasareRPA workflow JSON files for structural integrity, node dependencies, and connection validity. Use when: validating workflows, checking workflow JSON, testing workflow definitions.</skill>
    <skill name="chain-tester">Node chain testing templates for quality agent. Use when: testing node chains, WorkflowBuilder patterns, tier-based testing.</skill>

    <!-- Agent Execution -->
    <skill name="agent-invoker">Quick reference for invoking CasareRPA agents via Task tool. AUTO-CHAIN ENABLED by default. Use when: invoking agents, running agent chains, task routing.</skill>
    <skill name="parallel-exec">Automatic task decomposition with parallel agent execution. Use when: breaking down tasks, parallel agent work, complex multi-file changes.</skill>

    <!-- Code Quality & Review -->
    <skill name="code-reviewer">Structured code review output format for the reviewer agent. Provides APPROVED/ISSUES format with file:line references. Use when: reviewing code, code review gating, quality checks.</skill>
    <skill name="import-fixer">Fix import statements across the codebase to align with clean architecture layer boundaries. Use when: fixing imports, layer boundary violations, circular import issues.</skill>
    <skill name="dependency-updater">Analyze and update Python dependencies in pyproject.toml, checking for compatibility and security vulnerabilities. Use when: updating dependencies, checking security issues, dependency analysis.</skill>

    <!-- RPA Patterns -->
    <skill name="rpa-patterns">Common RPA automation patterns (retry, polling, circuit breaker). Use when: implementing RPA workflows, error handling, resilient automation.</skill>
    <skill name="error-recovery">RPA error handling patterns (fallback, retry, skip, user notification). Use when: handling errors in RPA workflows, error recovery strategies.</skill>
    <skill name="selector-strategies">CSS/XPath selector best practices for web automation (dropdowns, dynamic tables, nested components). Use when: writing selectors, handling dynamic content, React apps.</skill>
    <skill name="playwright-testing">RPA workflow testing with Playwright browser automation. Use when: testing browser nodes, page object model, wait strategies, screenshot testing.</skill>

    <!-- Integration & Infrastructure -->
    <skill name="mcp-server">Build MCP (Model Context Protocol) servers for CasareRPA integrations using Python FastMCP. Use when: creating MCP servers, tool design, error handling, RPA-specific patterns.</skill>

    <!-- Documentation & Context -->
    <skill name="brain-updater">Update .brain/ context files after completing tasks. Use when: updating project context, documenting changes, brain context management.</skill>
    <skill name="changelog-updater">Maintain and update CHANGELOG.md following Keep a Changelog format. Use when: updating changelog, version documentation, release notes.</skill>
  </skills>

  <structure>
    <component>SKILL.md</component>     <desc>Entry point with frontmatter (metadata) + body (<500 lines)</desc>
    <component>references/</component>  <desc>Documentation loaded on demand</desc>
    <component>examples/</component>    <desc>Concrete code samples</desc>
    <component>templates/</component>   <desc>Code templates for assets</desc>
    <component>scripts/</component>     <desc>Executable code (Python/Bash/etc.)</desc>
  </structure>

  <principles>
    <rule>Progressive disclosure: metadata always visible, SKILL.md on trigger, references/ as needed</rule>
    <rule>Concise SKILL.md: under 500 lines, lean on references/ for detailed content</rule>
    <rule>Description includes "when to use" triggers in frontmatter</rule>
    <rule>No auxiliary files: README.md, INSTALLATION_GUIDE.md, etc. prohibited</rule>
  </principles>
</skills_index>
```

*Token-optimized: All references are lazy-loaded*
