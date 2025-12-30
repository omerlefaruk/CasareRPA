<rules category="workflow">
  <gates>
    <gate id="research-complete" phase="RESEARCH">
      <check>Read relevant _index.md files</check>
      <check>Searched existing code</check>
      <check>Understood requirements</check>
      <allow_proceed>Yes</allow_proceed>
    </gate>

    <gate id="plan-approved" phase="PLAN">
      <check>Plan file created in plans/</check>
      <check>Files to modify identified</check>
      <requirement>EXPLICIT USER APPROVAL REQUIRED</requirement>
      <prompt>"Plan ready. Approve EXECUTE?"</prompt>
      <allow_proceed>After user says "yes" or "approve"</allow_proceed>
    </gate>

    <gate id="tests-pass" phase="VALIDATE">
      <check>pytest tests/ -v passes</check>
      <check>Code reviewer returns APPROVED</check>
      <check>No ISSUES listed</check>
      <allow_proceed>Only when APPROVED</allow_proceed>
      <on_failure>Fix issues and re-run quality agent</on_failure>
    </gate>
  </gates>

  <small_change_exception>
    <criteria>
      <criterion>&lt;50 lines changed</criterion>
      <criterion>UI fix (color, layout, toggle)</criterion>
      <criterion>Typo correction</criterion>
      <criterion>Tiny refactor</criterion>
    </criteria>
    <skip>
      <item>DOCS phase</item>
      <item>PLAN phase (for trivial fixes)</item>
    </skip>
    <commit_prefix>
      <prefix>fix(ui): for UI fixes</prefix>
      <prefix>fix: for simple bugs</prefix>
      <prefix>chore(typo): for typos</prefix>
      <prefix>refactor(small): for small refactors</prefix>
    </commit_prefix>
  </small_change_exception>
</rules>
