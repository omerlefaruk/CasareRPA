"""
Workflow Migration Dialog

Provides a dialog for migrating workflows between versions.
Users can check compatibility, preview changes, and execute migrations.
"""

from typing import Optional, TYPE_CHECKING
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QTextEdit,
    QPushButton,
    QWidget,
    QGroupBox,
    QProgressBar,
    QCheckBox,
    QTreeWidget,
    QTreeWidgetItem,
    QSplitter,
    QMessageBox,
)
from PySide6.QtGui import QFont, QColor

from loguru import logger
from casare_rpa.presentation.canvas.ui.widgets.animated_dialog import AnimatedDialog

if TYPE_CHECKING:
    from casare_rpa.application.use_cases.workflow_migration import (
        WorkflowMigrationUseCase,
        MigrationResult,
        CompatibilityResult,
    )
    from casare_rpa.domain.workflow.versioning import VersionHistory


class MigrationWorker(QThread):
    """Background worker for migration execution."""

    finished = Signal(object)  # MigrationResult
    error = Signal(str)
    progress = Signal(int, int)  # current, total

    def __init__(
        self,
        use_case: "WorkflowMigrationUseCase",
        from_version: str,
        to_version: str,
        dry_run: bool = False,
    ):
        super().__init__()
        self._use_case = use_case
        self._from_version = from_version
        self._to_version = to_version
        self._dry_run = dry_run

    def run(self):
        """Execute migration in background thread."""
        import asyncio

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self._use_case.migrate(
                    self._from_version, self._to_version, dry_run=self._dry_run
                )
            )
            self.finished.emit(result)
        except Exception as e:
            logger.exception("Migration failed")
            self.error.emit(str(e))
        finally:
            loop.close()


class MigrationDialog(AnimatedDialog):
    """
    Dialog for migrating workflows between versions.

    Features:
    - Version selection (source and target)
    - Compatibility check
    - Breaking changes preview
    - Dry run option
    - Migration execution with progress
    """

    migration_completed = Signal(object)  # MigrationResult

    def __init__(
        self,
        version_history: "VersionHistory",
        parent: Optional[QWidget] = None,
    ):
        """
        Initialize the migration dialog.

        Args:
            version_history: VersionHistory for the workflow
            parent: Parent widget
        """
        super().__init__(parent)

        self._version_history = version_history
        self._use_case: Optional["WorkflowMigrationUseCase"] = None
        self._worker: Optional[MigrationWorker] = None
        self._compatibility: Optional["CompatibilityResult"] = None

        self.setWindowTitle("Workflow Migration")
        self.resize(700, 550)
        self.setModal(True)

        self._create_ui()
        self._load_versions()

    def _create_ui(self):
        """Create the user interface."""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("Migrate Workflow Version")
        header_font = QFont()
        header_font.setPointSize(12)
        header_font.setBold(True)
        header.setFont(header_font)
        layout.addWidget(header)

        # Version selection
        version_group = QGroupBox("Version Selection")
        version_layout = QHBoxLayout(version_group)

        version_layout.addWidget(QLabel("From:"))
        self._from_combo = QComboBox()
        self._from_combo.currentIndexChanged.connect(self._on_version_changed)
        version_layout.addWidget(self._from_combo, 1)

        version_layout.addWidget(QLabel("→"))

        version_layout.addWidget(QLabel("To:"))
        self._to_combo = QComboBox()
        self._to_combo.currentIndexChanged.connect(self._on_version_changed)
        version_layout.addWidget(self._to_combo, 1)

        self._check_btn = QPushButton("Check Compatibility")
        self._check_btn.clicked.connect(self._check_compatibility)
        version_layout.addWidget(self._check_btn)

        layout.addWidget(version_group)

        # Splitter for changes and details
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Breaking changes tree
        changes_group = QGroupBox("Breaking Changes")
        changes_layout = QVBoxLayout(changes_group)

        self._changes_tree = QTreeWidget()
        self._changes_tree.setHeaderLabels(["Change", "Severity", "Auto-Fix"])
        self._changes_tree.setColumnWidth(0, 350)
        self._changes_tree.setColumnWidth(1, 80)
        changes_layout.addWidget(self._changes_tree)

        splitter.addWidget(changes_group)

        # Details panel
        details_group = QGroupBox("Migration Details")
        details_layout = QVBoxLayout(details_group)

        self._details_text = QTextEdit()
        self._details_text.setReadOnly(True)
        self._details_text.setMaximumHeight(120)
        details_layout.addWidget(self._details_text)

        splitter.addWidget(details_group)

        layout.addWidget(splitter, 1)

        # Progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setVisible(False)
        layout.addWidget(self._progress_bar)

        # Status label
        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: gray;")
        layout.addWidget(self._status_label)

        # Options
        options_layout = QHBoxLayout()
        self._dry_run_check = QCheckBox("Dry Run (preview only)")
        self._dry_run_check.setChecked(True)
        options_layout.addWidget(self._dry_run_check)
        options_layout.addStretch()
        layout.addLayout(options_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self._migrate_btn = QPushButton("Migrate")
        self._migrate_btn.setEnabled(False)
        self._migrate_btn.clicked.connect(self._execute_migration)
        button_layout.addWidget(self._migrate_btn)

        self._close_btn = QPushButton("Close")
        self._close_btn.clicked.connect(self.reject)
        button_layout.addWidget(self._close_btn)

        layout.addLayout(button_layout)

    def _load_versions(self):
        """Load available versions into combo boxes."""
        versions = self._version_history.list_versions()

        self._from_combo.clear()
        self._to_combo.clear()

        for ver in versions:
            display = f"v{ver.version} - {ver.change_summary or 'No description'}"
            self._from_combo.addItem(display, ver.version)
            self._to_combo.addItem(display, ver.version)

        # Select current and latest
        if len(versions) >= 2:
            self._from_combo.setCurrentIndex(len(versions) - 2)
            self._to_combo.setCurrentIndex(len(versions) - 1)

    def _on_version_changed(self):
        """Handle version selection change."""
        self._compatibility = None
        self._changes_tree.clear()
        self._details_text.clear()
        self._migrate_btn.setEnabled(False)
        self._status_label.setText("")

    def _check_compatibility(self):
        """Check compatibility between selected versions."""
        from casare_rpa.application.use_cases.workflow_migration import (
            WorkflowMigrationUseCase,
        )

        from_ver = self._from_combo.currentData()
        to_ver = self._to_combo.currentData()

        if not from_ver or not to_ver:
            self._status_label.setText("Please select both versions")
            return

        if from_ver == to_ver:
            self._status_label.setText("Source and target versions must be different")
            return

        # Create use case
        self._use_case = WorkflowMigrationUseCase(self._version_history)

        # Check feasibility
        feasible, compatibility, reason = self._use_case.check_migration_feasibility(
            from_ver, to_ver
        )

        self._compatibility = compatibility
        self._populate_changes(compatibility)

        if feasible:
            self._status_label.setText("✓ Migration is feasible")
            self._status_label.setStyleSheet("color: green;")
            self._migrate_btn.setEnabled(True)
        else:
            self._status_label.setText(f"✗ {reason}")
            self._status_label.setStyleSheet("color: red;")
            self._migrate_btn.setEnabled(False)

        # Update details
        self._update_details(compatibility)

    def _populate_changes(self, compatibility: "CompatibilityResult"):
        """Populate breaking changes tree."""
        self._changes_tree.clear()

        if not compatibility.breaking_changes:
            item = QTreeWidgetItem(["No breaking changes detected", "", ""])
            item.setForeground(0, QColor("green"))
            self._changes_tree.addTopLevelItem(item)
            return

        for change in compatibility.breaking_changes:
            severity_color = {
                "error": QColor("red"),
                "warning": QColor("orange"),
                "info": QColor("blue"),
            }.get(change.severity, QColor("gray"))

            auto_fix = "Yes" if change.auto_migratable else "No"

            item = QTreeWidgetItem([change.description, change.severity, auto_fix])
            item.setForeground(1, severity_color)

            if change.auto_migratable:
                item.setForeground(2, QColor("green"))
            else:
                item.setForeground(2, QColor("red"))

            self._changes_tree.addTopLevelItem(item)

    def _update_details(self, compatibility: "CompatibilityResult"):
        """Update details text."""
        lines = []

        lines.append(f"Compatible: {'Yes' if compatibility.is_compatible else 'No'}")
        lines.append(
            f"Auto-Migratable: {'Yes' if compatibility.auto_migratable else 'No'}"
        )
        lines.append(f"Breaking Changes: {len(compatibility.breaking_changes)}")

        if compatibility.migration_notes:
            lines.append("")
            lines.append("Notes:")
            for note in compatibility.migration_notes:
                lines.append(f"  • {note}")

        self._details_text.setText("\n".join(lines))

    def _execute_migration(self):
        """Execute the migration."""
        if not self._use_case:
            return

        from_ver = self._from_combo.currentData()
        to_ver = self._to_combo.currentData()
        dry_run = self._dry_run_check.isChecked()

        # Confirm if not dry run
        if not dry_run:
            reply = QMessageBox.question(
                self,
                "Confirm Migration",
                f"This will create a new version migrated from v{from_ver} to v{to_ver}.\n\n"
                "This action cannot be undone. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        # Disable UI
        self._migrate_btn.setEnabled(False)
        self._check_btn.setEnabled(False)
        self._from_combo.setEnabled(False)
        self._to_combo.setEnabled(False)
        self._progress_bar.setVisible(True)
        self._progress_bar.setRange(0, 0)  # Indeterminate

        self._status_label.setText(
            "Migrating..." if not dry_run else "Running dry run..."
        )
        self._status_label.setStyleSheet("color: blue;")

        # Run in background
        self._worker = MigrationWorker(self._use_case, from_ver, to_ver, dry_run)
        self._worker.finished.connect(self._on_migration_finished)
        self._worker.error.connect(self._on_migration_error)
        self._worker.start()

    def _on_migration_finished(self, result: "MigrationResult"):
        """Handle migration completion."""
        self._progress_bar.setVisible(False)
        self._re_enable_ui()

        if result.success:
            msg = (
                "Dry run completed successfully"
                if result.migrated_data and self._dry_run_check.isChecked()
                else "Migration completed successfully"
            )
            self._status_label.setText(f"✓ {msg}")
            self._status_label.setStyleSheet("color: green;")

            # Show summary
            summary = (
                f"Steps: {result.steps_completed}/{result.total_steps}\n"
                f"Duration: {result.duration_ms:.1f}ms\n"
                f"Breaking changes resolved: {result.breaking_changes_resolved}"
            )

            if result.warnings:
                summary += f"\nWarnings: {len(result.warnings)}"

            self._details_text.setText(summary)
            self.migration_completed.emit(result)
        else:
            self._status_label.setText("✗ Migration failed")
            self._status_label.setStyleSheet("color: red;")
            self._details_text.setText("\n".join(result.errors))

    def _on_migration_error(self, error: str):
        """Handle migration error."""
        self._progress_bar.setVisible(False)
        self._re_enable_ui()

        self._status_label.setText(f"✗ Error: {error}")
        self._status_label.setStyleSheet("color: red;")

    def _re_enable_ui(self):
        """Re-enable UI after migration."""
        self._check_btn.setEnabled(True)
        self._from_combo.setEnabled(True)
        self._to_combo.setEnabled(True)
        if self._compatibility:
            self._migrate_btn.setEnabled(True)


def show_migration_dialog(
    version_history: "VersionHistory",
    parent: Optional[QWidget] = None,
) -> Optional["MigrationResult"]:
    """
    Show the migration dialog and return result.

    Args:
        version_history: VersionHistory for the workflow
        parent: Parent widget

    Returns:
        MigrationResult if migration was executed, None if cancelled
    """
    dialog = MigrationDialog(version_history, parent)
    result = [None]

    def on_completed(migration_result):
        result[0] = migration_result

    dialog.migration_completed.connect(on_completed)

    if dialog.exec() == QDialog.DialogCode.Accepted:
        return result[0]
    return result[0]  # Return result even if dialog was closed after migration
