<rules category="workflow">
  <flow id="five-phase" name="5-Phase Workflow">
    <phase order="1" name="RESEARCH" gate="required">
      <description>Understand the problem before coding</description>
      <agents>explore, researcher</agents>
      <actions>
        <action>Read relevant _index.md files</action>
        <action>Search existing code for patterns</action>
        <action>Read .brain/decisions/ for context</action>
        <action>Use Task(explore) for codebase discovery</action>
      </actions>
      <output>Understanding of requirements and existing patterns</output>
    </phase>

    <phase order="2" name="PLAN" gate="user_approval">
      <description>Design approach before implementing</description>
      <agents>architect, Plan</agents>
      <actions>
        <action>Create plan file in plans/ directory</action>
        <action>Design implementation approach</action>
        <action>Identify files to modify</action>
        <action>Consider alternatives</action>
      </actions>
      <gate_requirement>Ask: "Plan ready. Approve EXECUTE?"</gate_requirement>
      <output>Approved plan with file list</output>
    </phase>

    <phase order="3" name="EXECUTE" gate="after_approval">
      <description>Implement according to plan</description>
      <agents>builder, refactor, ui</agents>
      <actions>
        <action>Write tests FIRST (TDD)</action>
        <action>Implement following plan</action>
        <action>Use THEME.* for UI colors</action>
        <action>Follow coding standards</action>
      </actions>
      <principles>
        <principle>KISS: Minimal code that works</principle>
        <principle>No over-engineering</principle>
        <principle>Strict type hints</principle>
      </principles>
      <output>Working implementation</output>
    </phase>

    <phase order="4" name="VALIDATE" gate="blocking">
      <description>Quality gate - loop until APPROVED</description>
      <agents>quality, reviewer</agents>
      <actions>
        <action>Run tests (pytest)</action>
        <action>Code review with code-reviewer skill</action>
        <action>Fix issues until APPROVED</action>
      </actions>
      <output>APPROVED status from reviewer</output>
    </phase>

    <phase order="5" name="DOCS" gate="unless_small_change">
      <description>Update documentation</description>
      <agents>docs, brain-updater</agents>
      <actions>
        <action>Update .brain/context/current.md for major tasks</action>
        <action>Update relevant _index.md files</action>
        <action>Self code review and QA summary</action>
      </actions>
      <exception>
        <condition>Small change: &lt;50 lines, UI fix, typo</condition>
        <action>Skip docs, use commit prefix fix(ui): or chore(typo):</action>
      </exception>
      <output>Updated documentation</output>
    </phase>
  </flow>

  <reporting>
    <rule>Always report current phase and progress</rule>
    <format>(in progress/completed/next)</format>
  </reporting>

  <references>
    <ref>@.claude/rules/01-core.md</ref>
    <ref>@docs/agent/workflow.md</ref>
    <ref>.claude/skills/agent-invoker/SKILL.md</ref>
  </references>
</rules>
