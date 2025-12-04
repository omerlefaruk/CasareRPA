# Installation

## Requirements

- Windows 10/11
- Python 3.12+
- pip package manager

## Install from Source

```bash
git clone https://github.com/CasareRPA/CasareRPA.git
cd CasareRPA
pip install -e .
```

## Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

## Run CasareRPA

```bash
python run.py
```

## Verify Installation

After launching, you should see:

1. Main window with canvas
2. Node library panel (left)
3. Properties panel (right)
4. Bottom panel with Output/Log tabs

## Next Steps

- [Create Your First Workflow](first-workflow.md)
- [Learn Core Concepts](concepts.md)
