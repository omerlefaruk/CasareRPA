# Tab Search Feature - Quick Start Guide

## Overview

The Tab Search feature provides quick access to all nodes using fuzzy search. Simply press **Tab** or **Right-Click** while in the node graph to bring up the searchable context menu.

## Usage

### Opening the Search Menu

1. Focus the node graph (click on the canvas)
2. Press **Tab** key or **Right-Click**
3. The context menu appears with a search field at the top

### Searching for Nodes

The search uses intelligent fuzzy matching with three strategies:

#### 1. **Exact Substring Match** (Highest Priority)
Type any part of the node name:
- `"typ"` → **Type Text** (exact match in "Type")
- `"elem"` → Click **Elem**ent

#### 2. **Word Initial Match** (High Priority)
Type the first letter of each word:
- `"b l"` → **B**rowser **L**aunch
- `"c e"` → **C**lick **E**lement
- `"g v"` → **G**et **V**ariable
- `"w e"` → **W**ait for **E**lement

#### 3. **Sequential Character Match** (Fallback)
Type characters that appear in sequence:
- `"brsr"` → **Br**ow**s**e**r** Launch
- `"clck"` → **Cl**i**ck** Element

### Keyboard Shortcuts

- **Tab** or **Right-Click** - Open searchable context menu
- **Type in search field** - Filter nodes as you type
- **↑/↓** - Navigate through categories and nodes
- **Enter** - Create selected node
- **Esc** - Close menu

### Tips

1. **Shorter is Better**: `"b l"` is faster than typing `"Browser Launch"`
2. **Space Matters**: `"b l"` (with space) matches word initials better
3. **Real-time Results**: Results update as you type
4. **First Match**: The top result is usually what you want

## Examples

### Common Searches

| Search | Matches | Description |
|--------|---------|-------------|
| `b l` | **Browser Launch** | Launch a browser |
| `c e` | **Click Element** | Click on element |
| `t t` | **Type Text** | Type text input |
| `g v` | **Get Variable** | Get variable value |
| `s v` | **Set Variable** | Set variable value |
| `w e` | **Wait for Element** | Wait for element |
| `g u` | **Go to URL** | Navigate to URL |
| `i f` | **If** | Conditional logic |
| `f l` | **For Loop** | Iteration loop |

### Advanced Searches

- `"nav"` → **Nav**igate nodes (Go to URL, Go Back, etc.)
- `"wait"` → All **wait** nodes
- `"var"` → All **var**iable nodes
- `"browser"` → All **browser** nodes

## Implementation Details

### Files Created

1. **`src/casare_rpa/utils/fuzzy_search.py`**
   - Fuzzy matching algorithm
   - Word initial detection
   - Score calculation
   - Match highlighting

2. **`src/casare_rpa/gui/node_search_dialog.py`**
   - Search dialog UI
   - Results list with highlighting
   - Keyboard navigation
   - Node selection handling

3. **Modified `src/casare_rpa/gui/node_graph_widget.py`**
   - Tab key event filter
   - Dialog positioning
   - Node creation at cursor

### Scoring System

- **Exact substring**: -200 + position (lower = better)
- **Word initials**: -100 + word count + positions
- **Sequential match**: position × 10 + span + gaps + boundary bonus

### Testing

Run tests to verify functionality:
```bash
python tests/test_fuzzy_search.py
```

All tests should pass ✓

---

**Enjoy faster node creation with Tab search! 🚀**
