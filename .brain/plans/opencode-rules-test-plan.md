# OpenCode Rules Integration Test Plan

**Created**: 2025-12-25
**Status**: Ready for Execution
**MCP Servers**: Partially Configured (filesystem, git working; codebase needs fix)

## Quick Summary

| Item | Status |
|------|--------|
| `opencode.json` | ✅ Created with `instructions` array |
| `.agent/rules/` frontmatter | ✅ All 15 files have frontmatter |
| MCP Configuration | ✅ `.mcp.json` configured |
| OpenCode Config | ✅ `.opencode/mcp_config.json` exists |
| Codebase Index | ❌ Needs ChromaDB fix |

## MCP Server Status

| Server | Command | Status |
|--------|---------|--------|
| `codebase` | `python scripts/chroma_search_mcp.py` | ⚠️ Needs indexing fix |
| `filesystem` | `npx @modelcontextprotocol/server-filesystem .` | ✅ Working |
| `git` | `npx @modelcontextprotocol/server-git` | ✅ Working |
| `sequential-thinking` | `npx @modelcontextprotocol/server-sequential-thinking` | ✅ Configured |
| `exa` | `npx exa-mcp-server` | ✅ Configured |
| `ref` | `npx @upstash/context7-mcp` | ✅ Configured |

## Usage Patterns (from `.opencode/mcp_config.json`)

```json
{
  "exploration": ["codebase", "filesystem", "git"],
  "research": ["exa", "ref", "codebase"],
  "planning": ["sequential-thinking", "filesystem", "git"]
}
```

## Test Execution Steps

### Step 1: Verify OpenCode Configuration

**Command**:
```bash
# Check opencode.json exists and is valid
cat opencode.json | python -m json.tool > /dev/null && echo "Valid JSON"
```

**Expected**: Valid JSON with `instructions` array referencing `.agent/rules/`

### Step 2: Test Filesystem MCP

**Command**:
```bash
# List rules directory (simulating filesystem MCP)
dir .agent\rules\
```

**Expected**: Lists all 15 rule files

### Step 3: Test Git MCP

**Command**:
```bash
# Get recent commits (simulating git MCP)
git log --oneline -5
```

**Expected**: Shows recent commit history

### Step 4: Test OpenCode Rules Loading

**Commands** (in OpenCode TUI):
```
/init
```

**Questions to ask**:
1. "What is the 5-phase workflow?" → Should reference `@.agent/rules/01-workflow-default.md`
2. "What are the coding standards?" → Should reference `@.agent/rules/02-coding-standards.md`
3. "How do I create a node?" → Should reference `@.agent/rules/03-nodes.md`
4. "What are the hard constraints?" → Should reference `@.agent/rules/06-enforcement.md`

### Step 5: Test Agent MCP Usage

**Commands** (in OpenCode TUI):
```
@explorer Find browser automation patterns in the codebase
@general Design a solution for OAuth token handling
@builder Implement a new HTTP node following the rules
```

**Expected**:
- Agents reference rules from `.agent/rules/`
- Agents use MCP servers appropriately
- Agents follow 5-phase workflow

### Step 6: Test Skill Invocation

**Commands** (in OpenCode TUI):
```
Skill(skill="node-template-generator", category="browser", name="ClickElement")
Skill(skill="test-generator", target="src/casare_rpa/nodes/browser/")
```

**Expected**:
- Skills are loaded from `.opencode/skill/<name>/SKILL.md`
- Skills produce valid output

## Files Modified During Setup

| File | Change |
|------|--------|
| `opencode.json` | Created with `instructions` array |
| `AGENTS.md` | Added OpenCode integration section |
| `.agent/rules/01-core.md` | Added YAML frontmatter |
| `.agent/rules/02-architecture.md` | Added YAML frontmatter |
| `.agent/rules/03-nodes.md` | Added YAML frontmatter |
| `.agent/rules/12-ddd-events.md` | Added YAML frontmatter |

## Known Issues

1. **Codebase MCP**: ChromaDB version incompatibility (`upsert_documents` method)
   - **Fix needed**: Update `scripts/chroma_search_mcp.py` for newer ChromaDB API
   - **Workaround**: Use `rg` for code search until fixed

2. **Encoding**: Windows console may not display emojis
   - **Fix**: Use ASCII characters in scripts

## Success Criteria

- [x] `opencode.json` exists with valid `instructions` array
- [x] All rule files in `.agent/rules/` have YAML frontmatter
- [ ] OpenCode can load rules from `.agent/rules/` (to be tested)
- [ ] Agents can use MCP servers (filesystem, git) (to be tested)
- [ ] Skills can be invoked from `.opencode/skill/` (to be tested)

## Next Steps

1. **Fix ChromaDB** for codebase MCP (optional, not blocking)
2. **Test OpenCode rules loading** (critical)
3. **Test agent MCP usage** (important)
4. **Test skill invocation** (important)
5. **Update rules** based on recent commits (optional)

## Commands Reference

```bash
# Test MCP configuration
python scripts/mcp_test.py

# Index codebase (if ChromaDB fixed)
python scripts/index_codebase.py

# Start OpenCode
opencode

# Initialize project
/init

# Sync agent guides
python scripts/sync_agent_guides.py
```

## Recent Commits to Consider for Rule Updates

| Commit | Description | Rule Impact |
|--------|-------------|-------------|
| `fc25c54e` | Token refresh handling | May need `07-tools.md` update |
| `a4e8bb85` | Vertex AI auth variants | May need `02-architecture.md` update |
| `1066de9b` | AGENTS.md access_token | Already updated |
| `2e53ed27` | Per-request config | May need `02-architecture.md` update |

---

*This test plan was created as part of the OpenCode rules integration implementation.*
