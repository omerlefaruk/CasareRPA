# Brain Protocol

The `.brain/` directory is the AI agent's working memory.

## Structure
```
.brain/
├── context/
│   └── current.md      # Current session state
├── docs/
│   └── *.md            # Implementation checklists
├── plans/
│   └── *.md            # Active plans
├── projectRules.md     # Full coding standards
└── systemPatterns.md   # Architecture patterns
```

## Usage

### Session Start
1. Read `.brain/context/current.md`
2. Understand current state and priorities

### During Work
- Create plans in `.brain/plans/`
- Reference patterns in `.brain/systemPatterns.md`

### Session End
- Update `.brain/context/current.md` with:
  - What was done
  - What's next
  - Any blockers

## Maintenance
- Keep `current.md` concise
- Archive completed plans
- Update patterns when new ones emerge
