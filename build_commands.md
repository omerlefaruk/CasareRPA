# CasareRPA Build Commands

This document contains the PyInstaller commands used to build the CasareRPA applications as standalone executables.

---

## Canvas

```
pyinstaller --noconsole --noconfirm --name "CasareRPA-Canvas" \
  --add-data "src/casare_rpa;casare_rpa" \
  --hidden-import=PySide6.QtSvg \
  --hidden-import=PySide6.QtWidgets \
  --hidden-import=PySide6.QtGui \
  --hidden-import=PySide6.QtCore \
  --hidden-import=loguru \
  --hidden-import=psutil \
  --hidden-import=qasync \
  --hidden-import=NodeGraphQt \
  --hidden-import=Qt \
  --hidden-import=orjson \
  --hidden-import=playwright \
  --hidden-import=playwright.async_api \
  --hidden-import=playwright.sync_api \
  --hidden-import=uiautomation \
  --clean run.py
```

---

## Robot

```
pyinstaller --name="CasareRPA-Robot" --windowed --paths=src \
  --hidden-import=casare_rpa.robot \
  --hidden-import=casare_rpa.utils \
  --hidden-import=playwright \
  --hidden-import=PySide6 \
  --hidden-import=qasync \
  --onedir --clean src/casare_rpa/robot/tray_icon.py
```

---

## Orchestrator

```
pyinstaller --name="CasareRPA-Orchestrator" --windowed --paths=src \
  --hidden-import=casare_rpa.orchestrator \
  --hidden-import=casare_rpa.utils \
  --hidden-import=PySide6 \
  --hidden-import=qasync \
  --onedir --clean src/casare_rpa/orchestrator/main_window.py
```

---

> Update these commands as needed if new dependencies are added.
