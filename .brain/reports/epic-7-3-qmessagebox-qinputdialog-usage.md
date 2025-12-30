# Epic 7.3: QMessageBox/QInputDialog Usage Analysis

## Summary
Found extensive usage of QMessageBox and QInputDialog throughout the codebase, particularly in the canvas UI layer. All usage patterns need to be replaced with standardized v2 prompts (MessageBoxV2, ConfirmDialogV2, etc.).

## Files Using QMessageBox (47 total)

### Canvas UI Layer (36 files)
| File | Usage Count | Pattern |
|------|-------------|---------|
| `src/casare_rpa/presentation/canvas/components/fleet_dashboard_manager.py` | ~24 | information(), warning(), critical() |
| `src/casare_rpa/presentation/canvas/controllers/workflow_controller.py` | ~25 | information(), warning(), critical(), question() |
| `src/casare_rpa/presentation/canvas/ui/dialogs/credential_manager_dialog.py` | ~30 | information(), warning(), critical(), question() |
| `src/casare_rpa/presentation/canvas/ui/panels/credentials_panel.py` | ~15 | question(), warning(), information(), critical() |
| `src/casare_rpa/presentation/canvas/ui/panels/api_key_panel.py` | ~8 | question(), warning(), information() |
| `src/casare_rpa/presentation/canvas/ui/dialogs/google_oauth_dialog.py` | ~12 | warning(), information() |
| `src/casare_rpa/presentation/canvas/ui/dialogs/openai_oauth_dialog.py` | ~8 | warning(), critical(), information() |
| `src/casare_rpa/presentation/canvas/ui/panels/browser_recording_panel.py` | ~5 | warning(), critical() |
| `src/casare_rpa/presentation/canvas/ui/dialogs/antigravity_oauth_dialog.py` | ~3 | warning() |
| `src/casare_rpa/presentation/canvas/ui/panels/process_mining_panel.py` | ~2 | critical() |
| `src/casare_rpa/presentation/canvas/ui/panels/recorded_actions_panel.py` | ~2 | critical() |
| `src/casare_rpa/presentation/canvas/ui/widgets/orchestrator/queues_tab.py` | ~3 | critical() |
| `src/casare_rpa/presentation/canvas/ui/widgets/orchestrator/transactions_tab.py` | ~2 | critical() |
| `src/casare_rpa/presentation/canvas/ui/widgets/ai_settings_widget.py` | ~2 | critical() |
| `src/casare_rpa/presentation/canvas/ui/widgets/performance_dashboard.py` | ~2 | critical() |
| `src/casare_rpa/presentation/canvas/ui/widgets/encryptable_line_edit.py` | ~2 | critical() |
| `src/casare_rpa/presentation/canvas/ui/toolbars/hotkey_manager.py` | ~1 | critical() |
| `src/casare_rpa/presentation/canvas/ui/dialogs/quick_node_config_dialog.py` | ~1 | critical() |
| `src/casare_rpa/presentation/canvas/ui/dialogs/remote_robot_dialog.py` | ~1 | critical() |
| `src/casare_rpa/presentation/canvas/ui/dialogs/fleet_tabs/robots_tab.py` | ~1 | critical() |
| `src/casare_rpa/presentation/canvas/ui/dialogs/project_manager_dialog.py` | ~1 | critical() |
| `src/casare_rpa/presentation/canvas/ui/dialogs/recording_dialog.py` | ~1 | critical() |
| `src/casare_rpa/presentation/canvas/ui/dialogs/environment_editor.py` | ~2 | warning() |
| `src/casare_rpa/presentation/canvas/ui/debug_panel.py` | ~2 | information() |
| `src/casare_rpa/presentation/canvas/theme_system/primitive_gallery.py` | ~2 | information(), warning() |
| `src/casare_rpa/presentation/canvas/selectors/ui_explorer/ui_explorer_dialog.py` | ~1 | information() |
| `src/casare_rpa/presentation/canvas/controllers/viewport_controller.py` | ~1 | warning() |
| `src/casare_rpa/presentation/canvas/actions/create_subflow.py` | ~2 | warning(), critical() |
| `src/casare_rpa/presentation/canvas/controllers/project_controller.py` | ~1 | critical() |
| `src/casare_rpa/presentation/canvas/coordinators/signal_coordinator.py` | ~1 | warning() |
| `src/casare_rpa/presentation/canvas/main_window.py` | ~1 | information() |
| `src/casare_rpa/presentation/canvas/app.py` | ~4 | critical(), warning() |

### Node Implementations
| File | Usage Count | Pattern |
|------|-------------|---------|
| `src/casare_rpa/nodes/system/dialogs/message.py` | ~2 | Different implementation for nodes |
| `src/casare_rpa/nodes/system/dialogs/input.py` | ~1 | Input dialog for nodes |

### Utilities (2 files)
| File | Usage Count | Pattern |
|------|-------------|---------|
| `src/casare_rpa/utils/playwright_setup.py` | ~4 | question(), information(), warning() |
| `src/casare_rpa/robot/tray_icon.py` | ~1 | critical() |

## Files Using QInputDialog (8 total)

### Canvas UI Layer (7 files)
| File | Usage Count | Pattern |
|------|-------------|---------|
| `src/casare_rpa/presentation/canvas/ui/panels/project_explorer_panel.py` | ~3 | getText() |
| `src/casare_rpa/presentation/canvas/ui/dialogs/environment_editor.py` | ~3 | getText() |
| `src/casare_rpa/presentation/canvas/graph/node_frame.py` | ~1 | getText() |
| `src/casare_rpa/presentation/canvas/graph/node_quick_actions.py` | ~1 | getText() |
| `src/casare_rpa/presentation/canvas/ui/debug_panel.py` | ~2 | getText() |
| `src/casare_rpa/presentation/canvas/coordinators/signal_coordinator.py` | ~1 | getText() |

### Node Implementation
| File | Usage Count | Pattern |
|------|-------------|---------|
| `src/casare_rpa/nodes/system/dialogs/input.py` | ~1 | getText() for nodes |

## Common Usage Patterns Identified

### QMessageBox Patterns
1. **Information Dialogs**
   - `QMessageBox.information(parent, title, message)`
   - Usage: Success messages, confirmations

2. **Warning Dialogs**
   - `QMessageBox.warning(parent, title, message)`
   - Usage: Validation errors, non-critical failures

3. **Critical Dialogs**
   - `QMessageBox.critical(parent, title, message)`
   - Usage: Severe errors, critical failures

4. **Question Dialogs**
   - `QMessageBox.question(parent, title, message, buttons, default_button)`
   - Usage: Confirmation dialogs with Yes/No or OK/Cancel

### QInputDialog Patterns
1. **Text Input**
   - `QInputDialog.getText(parent, title, label, text_mode, current_text)`
   - Usage: Name input, parameter input, custom text input

## Replacement Strategy

### QMessageBox → MessageBoxV2/ConfirmDialogV2
```python
# Current
QMessageBox.information(parent, "Title", "Message")
QMessageBox.warning(parent, "Title", "Message")
QMessageBox.critical(parent, "Title", "Message")
QMessageBox.question(parent, "Title", "Message", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

# Future
MessageBoxV2.information(parent, "Title", "Message")
MessageBoxV2.warning(parent, "Title", "Message")
MessageBoxV2.error(parent, "Title", "Message")
ConfirmDialogV2(parent, "Title", "Message").show_question()
```

### QInputDialog → Custom Dialog v2
Need to create standardized input dialogs using the new dialog framework.

## Priority Files for Migration
1. **High Priority** (Most usage):
   - `fleet_dashboard_manager.py`
   - `workflow_controller.py`
   - `credential_manager_dialog.py`
   - `credentials_panel.py`

2. **Medium Priority**:
   - `api_key_panel.py`
   - `google_oauth_dialog.py`
   - `openai_oauth_dialog.py`

3. **Low Priority**:
   - Various utility files with minimal usage

## Notes
- All dialogs must use `THEME_V2` and `TOKENS_V2` (no hardcoded colors)
- Follow the standardized dialog footer pattern with ButtonRole
- Maintain existing button behavior and return values
- Update icon mappings (Question → Information for info dialogs)