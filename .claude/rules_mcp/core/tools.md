<rule id="tool-usage" priority="normal">
  <name>Tool Usage Guidelines</name>
  <description>Prefer MCP tools over bash commands</description>

  <prefer>
    <tool>mcp__filesystem__read_multiple_files</tool>
    <tool>mcp__filesystem__read_text_file</tool>
    <tool>mcp__git__*</tool>
    <tool>mcp__plugin_serena_serena__*</tool>
    <tool>Task(explore) for codebase search</tool>
  </prefer>

  <avoid>
    <tool>bash cat (use Read instead)</tool>
    <tool>bash echo (use text output)</tool>
    <tool>bash grep (use Grep tool)</tool>
    <tool>bash find (use Glob tool)</tool>
  </avoid>

  <file_reads>
    <pattern>3-5 small files (<500 lines)</pattern>
    <use>mcp__filesystem__read_multiple_files</use>
  </file_reads>

  <large_files>
    <pattern>Files >500 lines</pattern>
    <use>mcp__filesystem__read_text_file with limit=N</use>
  </large_files>

  <parallel_execution>
    <rule>Launch independent operations in ONE message</rule>
    <correct>Task(explore, "A") + Task(explore, "B")</correct>
    <wrong>Task(...) → wait → Task(...)</wrong>
  </parallel_execution>
</rule>
