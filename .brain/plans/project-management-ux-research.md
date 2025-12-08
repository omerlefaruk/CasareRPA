# Project Management UX Research for CasareRPA

**Research Date**: 2025-12-08
**Status**: COMPLETE

---

## Executive Summary

This research analyzes best-in-class project management UX patterns from UiPath, Power Automate, Automation Anywhere, n8n, and VS Code. The goal is to recommend concrete UX improvements and PySide6/Qt component designs for CasareRPA's project management system.

---

## 1. Competitive Analysis

### 1.1 UiPath Studio + Orchestrator

**Folder Organization** ([UiPath Docs](https://docs.uipath.com/orchestrator/docs/managing-folders)):
- **Modern Folders**: Up to 7 levels of hierarchy
- **Inheritance Model**: User access inherited from parent folders
- **Cross-Folder Access**: Workflows can access resources in other folders via `Orchestrator Folder Path` parameter
- **Tenant Segregation**: Non-production vs production environments can be separate tenants

**Key Patterns**:
| Feature | Implementation |
|---------|----------------|
| Folder Admin Role | Separate from Tenant Admin |
| Environment Management | External config files or separate Orchestrator instances |
| VCS Integration | Built-in GIT, TFS, SVN support |
| Solution Folders | Virtual folders for grouping projects |

**Strengths**:
- Fine-grained access control at folder level
- Clear separation of environments
- Enterprise-ready role-based access

**Weaknesses**:
- Complex setup for small teams
- Learning curve for folder hierarchy

### 1.2 Power Automate Desktop

**Solutions Architecture** ([Microsoft Learn](https://learn.microsoft.com/en-us/power-apps/maker/data-platform/environmentvariables-power-automate)):
- **Solutions**: Container for Apps, Flows (Cloud + Desktop), Dataverse tables, etc.
- **Environment Variables**: Key-value pairs stored at solution level
- **ALM Support**: CI/CD via SolutionPackager and DevOps tools

**Environment Variables** ([azurecurve](https://www.azurecurve.co.uk/2024/02/working-with-power-automate-what-are-environment-variables-and-why-should-they-be-used/)):
- **Limitation**: Desktop flows cannot directly access environment variables
- **Workaround**: Pass values via Cloud Flow input parameters
- **Best Practice**: Use JSON variable to group related config values
- **Deployment**: Values can be unpacked and stored in source control

**Key Patterns**:
| Feature | Implementation |
|---------|----------------|
| Variable Storage | Solution-level, not flow-level |
| Environment Switching | Different values files per environment |
| Desktop Flow Integration | Cloud flow passes env vars as inputs |
| Multi-value Config | JSON variable for grouped settings |

**Strengths**:
- Strong ALM/DevOps integration
- Environment-agnostic flow development

**Weaknesses**:
- Desktop flows isolated from env vars
- Requires cloud flow wrapper for env config

### 1.3 Automation Anywhere Control Room

**Credential Vault** ([AA Docs](https://docs.automationanywhere.com/bundle/enterprise-v2019/page/enterprise-cloud/topics/control-room/bots/credentials/cloud-credentials-overview.html)):
- **Lockers**: Group credentials for access control
- **Credential Attributes**: Up to 50 attributes per credential
- **External Key Vault**: CyberArk, AWS Secrets Manager, Azure Key Vault, HashiCorp integration
- **Connection Modes**: Express (auto) vs Manual (secure, recommended for prod)

**Key Patterns**:
| Feature | Implementation |
|---------|----------------|
| Credential Creation | Max 50 attributes per credential |
| Locker System | Group credentials, limit access |
| Security | Never stored in plaintext, never in bot source |
| Device Validation | Optional credential validation before deployment |

**Strengths**:
- Enterprise-grade security (HSM support)
- External vault integration
- Audit logging for all credential access

**Weaknesses**:
- Complex initial setup
- Master key management overhead

### 1.4 n8n

**Organization Hierarchy** ([DEV Community](https://dev.to/brook_051cd08713006b/managing-n8n-projects-and-folders-4i06)):
```
Instance
  Projects (Enterprise/Pro)
    Folders (tag-based)
      Workflows
    Credentials
    Team Members
```

**Folders** ([n8n Community](https://community.n8n.io/t/organize-workflows-using-folders-got-created/49089)):
- Tag-based organization creating visual hierarchy
- Environment variable: `N8N_FOLDERS_ENABLED=true`
- Workflow template to convert tags into folders

**Credentials** ([n8n Community](https://community.n8n.io/t/credentials-linked-to-tags/228381)):
- Feature request: Credentials filtered by workflow tags
- Current limitation: Credentials not auto-bound when promoting Dev to Prod
- Migration requires manual credential rebinding

**Key Patterns**:
| Feature | Implementation |
|---------|----------------|
| Tags | Primary organization mechanism |
| Folders | Visual hierarchy from tags |
| Projects | Container for team collaboration (Pro) |
| RBAC | Role-based access on projects |

**Strengths**:
- Simple tag-based organization
- Quick folder creation from existing tags
- Open-source flexibility

**Weaknesses**:
- No credential-to-tag binding
- Environment promotion issues

### 1.5 VS Code Workspace Model

**Workspace Types** ([VS Code Docs](https://code.visualstudio.com/docs/editor/workspaces)):
- **Single Folder**: Simplest, one root folder
- **Multi-root**: Multiple folders in `.code-workspace` file
- **Scoped Workspaces**: Different `.code-workspace` files for different views (client, server, etc.)

**Tree View API** ([VS Code API](https://code.visualstudio.com/api/extension-guides/tree-view)):
- `TreeDataProvider` interface for custom tree views
- `TreeView` API for view operations (expand, collapse, reveal)
- Visibility: visible, collapsed, hidden (remembered per workspace)

**File Explorer** ([VS Code UI](https://code.visualstudio.com/docs/getstarted/userinterface)):
- Filter via `Ctrl+Alt+F` with partial name match
- Drag-drop between root folders
- Context menu for file operations
- Tree indent configurable (default 8px)

**Key Patterns**:
| Feature | Implementation |
|---------|----------------|
| Tree Navigation | Filter, expand/collapse, reveal |
| Multi-root | Multiple folder roots in single window |
| Scoped Views | Different workspace files for different contexts |
| Customization | Tree indent, visibility preferences |

**Strengths**:
- Clean, intuitive file explorer
- Excellent keyboard navigation
- Flexible workspace configurations

**Weaknesses**:
- Not RPA-specific (no credential/variable integration)

---

## 2. Variable Management UX

### 2.1 Scoping Best Practices

**Hierarchy** ([Power Automate Scoped Variables](https://www.hubsite365.com/en-ww/crm-pages/power-automate-desktop-scoped-variables-e44bd0a8-0adf-41c1-803a-37a75bbd2829.htm)):
```
Global Variables (Application-wide)
  Environment Variables (dev/staging/prod)
    Project Variables (per-project defaults)
      Scenario Variables (workflow-specific)
        Local Variables (node-scoped, runtime only)
```

**Best Practices** ([GeeksforGeeks](https://www.geeksforgeeks.org/software-engineering/types-of-variables-in-automation-anywhere-rpa/)):
1. **Minimize Global Variables**: Prefer local scope
2. **Use Input/Output Variables**: Clear data contracts between components
3. **Naming Convention**: Prefix by scope (g_, env_, p_, s_, l_)
4. **Encapsulation**: Subflows should use input/output, not global access

**CasareRPA Current State**:
```python
# From domain/entities/project/variables.py
class VariableScope(Enum):
    GLOBAL = "global"
    PROJECT = "project"
    SCENARIO = "scenario"
```

### 2.2 Environment Switcher Pattern

**Recommended UI**:
```
+------------------------------------------+
| Environment: [Development v] [Sync] [Diff]|
+------------------------------------------+
```

**Implementation Pattern**:
1. **Dropdown**: Shows current environment (dev, staging, prod)
2. **Sync Button**: Pulls/pushes env vars from central store
3. **Diff Button**: Shows differences between environments
4. **Color Coding**: Green=synced, Yellow=local changes, Red=conflict

**Data Structure**:
```python
@dataclass
class EnvironmentConfig:
    name: str  # "development", "staging", "production"
    variables: Dict[str, Any]
    credentials_overrides: Dict[str, str]  # alias -> credential_id
    is_default: bool = False
```

### 2.3 Variable UI Components

**Variable Editor Panel**:
```
+------------------------------------------+
| Variables                    [+] [Search] |
+------------------------------------------+
| Scope: [All v] [Project v] [Scenario v]  |
+------------------------------------------+
| Name        | Type    | Value  | Scope   |
|-------------|---------|--------|---------|
| api_base_url| String  | https..| Project |
| max_retries | Integer | 3      | Env:dev |
| debug_mode  | Boolean | true   | Scenario|
+------------------------------------------+
```

**Features**:
- Inline editing with type validation
- Scope filter dropdown
- Environment override indicator (badge)
- Variable usage search (find references)

---

## 3. Project Organization

### 3.1 Recommended Folder Structure

```
CasareRPA Projects/
  projects_index.json          # Project registry

  MyProject/
    project.json               # Project metadata
    variables.json             # Project variables
    credentials.json           # Credential bindings
    environments/
      development.json         # Dev env overrides
      staging.json
      production.json
    scenarios/
      main.json
      login_flow.json
    subflows/
      common_login.json
    assets/
      selectors.json           # Reusable selectors
      templates/               # Document templates
```

### 3.2 Tags vs Folders vs Both

**Recommendation**: **Both** - with smart integration

| Method | Use Case |
|--------|----------|
| Folders | Physical organization, environment separation |
| Tags | Cross-cutting concerns (status, priority, owner) |

**Tag Categories**:
- **Status**: draft, active, archived, deprecated
- **Priority**: high, medium, low
- **Type**: web, desktop, api, hybrid
- **Owner**: team_a, team_b, external

### 3.3 Project Metadata Schema

**Enhanced Project Entity**:
```python
@dataclass
class Project:
    id: str
    name: str
    description: str
    author: str
    created_at: datetime
    modified_at: datetime
    tags: List[str]
    settings: ProjectSettings

    # NEW FIELDS
    version: str = "1.0.0"           # Semantic versioning
    category: str = ""               # "Finance", "HR", etc.
    icon: str = ""                   # Icon identifier
    color: str = "#4A90D9"           # Project color
    template_id: Optional[str] = None # If created from template
    environments: List[str] = field(default_factory=lambda: ["development"])
    default_environment: str = "development"
```

### 3.4 Project Templates

**Template Structure**:
```python
@dataclass
class ProjectTemplate:
    id: str
    name: str
    description: str
    category: str  # "Web Automation", "Data Processing", etc.
    icon: str

    # Template content
    default_scenarios: List[Dict]  # Pre-built scenario scaffolds
    default_variables: Dict[str, Variable]
    default_settings: ProjectSettings
    required_credentials: List[str]  # Credential types needed

    # UI hints
    setup_wizard_steps: List[Dict]  # Guided setup
```

**Built-in Templates**:
1. **Web Scraping**: Browser launch, navigation, data extraction
2. **Form Automation**: Form detection, filling, submission
3. **Report Generation**: Data fetch, document creation, email
4. **API Integration**: REST calls, data transformation
5. **Desktop Automation**: UIAutomation setup, window handling

---

## 4. Credentials Reference Patterns

### 4.1 Current CasareRPA Approach

**CredentialBinding** (`credentials.py`):
```python
@dataclass
class CredentialBinding:
    alias: str           # Local name: "erp_login"
    vault_path: str      # Global path: "projects/proj_123/erp_creds"
    credential_type: str
    description: str
    required: bool
```

### 4.2 Environment-Specific Overrides

**Recommended Enhancement**:
```python
@dataclass
class CredentialBinding:
    alias: str
    default_credential_id: str  # Default credential
    environment_overrides: Dict[str, str]  # env -> credential_id
    credential_type: str
    description: str
    required: bool

    def get_credential_id(self, environment: str) -> str:
        return self.environment_overrides.get(environment, self.default_credential_id)
```

**UI Pattern**:
```
+------------------------------------------+
| Credential: ERP Login                     |
+------------------------------------------+
| Alias: erp_login                          |
| Type: username_password                   |
| Required: [x]                             |
+------------------------------------------+
| Environment Bindings:                     |
| Development: [Test ERP Account v]         |
| Staging:     [Staging ERP Account v]      |
| Production:  [Prod ERP Account v]         |
+------------------------------------------+
```

### 4.3 Credential Resolution Order

1. **Environment Override**: Check current env's credential_id
2. **Project Binding**: Check project-level credential_id
3. **Global Credential**: Check global credential store by alias
4. **Environment Variable**: Fallback to env var (legacy support)

---

## 5. UI Component Designs (PySide6/Qt)

### 5.1 Project Explorer Tree View

**Component**: `ProjectExplorerPanel`

```python
class ProjectExplorerPanel(QDockWidget):
    """
    VS Code-style project explorer with hierarchical tree view.

    Features:
    - Project/Scenario/Subflow hierarchy
    - Drag-drop reordering
    - Context menu actions
    - Search/filter
    - Environment switcher
    """

    def __init__(self, parent=None):
        super().__init__("Explorer", parent)
        self._setup_ui()

    def _setup_ui(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # Environment switcher
        env_bar = self._create_environment_bar()
        layout.addWidget(env_bar)

        # Search
        search_bar = self._create_search_bar()
        layout.addWidget(search_bar)

        # Tree view
        self._tree = ProjectTreeView()
        layout.addWidget(self._tree)

        self.setWidget(container)
```

**Tree Model**:
```python
class ProjectTreeModel(QAbstractItemModel):
    """
    Custom model for project hierarchy with drag-drop support.

    Hierarchy:
    - Project
      - Scenarios
        - scenario_1.json
        - scenario_2.json
      - Subflows
        - login_subflow.json
      - Variables
      - Credentials
      - Environments
        - development
        - staging
        - production
    """

    def flags(self, index):
        flags = super().flags(index)
        item = index.internalPointer()

        if item.is_draggable:
            flags |= Qt.ItemFlag.ItemIsDragEnabled
        if item.is_drop_target:
            flags |= Qt.ItemFlag.ItemIsDropEnabled

        return flags

    def supportedDropActions(self):
        return Qt.DropAction.MoveAction
```

**Tree Item Types**:
```python
class ProjectTreeItem:
    """Base tree item with type discrimination."""

    class ItemType(Enum):
        PROJECT = "project"
        FOLDER = "folder"
        SCENARIO = "scenario"
        SUBFLOW = "subflow"
        VARIABLE_GROUP = "variables"
        CREDENTIAL_GROUP = "credentials"
        ENVIRONMENT_GROUP = "environments"
        ENVIRONMENT = "environment"

    def __init__(self, item_type: ItemType, name: str, data: Any = None):
        self.item_type = item_type
        self.name = name
        self.data = data
        self.children: List[ProjectTreeItem] = []
        self.parent: Optional[ProjectTreeItem] = None

    @property
    def is_draggable(self) -> bool:
        return self.item_type in (ItemType.SCENARIO, ItemType.SUBFLOW)

    @property
    def is_drop_target(self) -> bool:
        return self.item_type == ItemType.FOLDER

    @property
    def icon(self) -> str:
        icons = {
            ItemType.PROJECT: "folder-project",
            ItemType.FOLDER: "folder",
            ItemType.SCENARIO: "file-workflow",
            ItemType.SUBFLOW: "file-subflow",
            ItemType.VARIABLE_GROUP: "symbol-variable",
            ItemType.CREDENTIAL_GROUP: "key",
            ItemType.ENVIRONMENT_GROUP: "server",
            ItemType.ENVIRONMENT: "server-environment",
        }
        return icons.get(self.item_type, "file")
```

### 5.2 Drag-Drop Implementation

**Enable Drag-Drop** ([KDAB Guide](https://www.kdab.com/modelview-drag-and-drop-part-1/)):
```python
class ProjectTreeView(QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Enable internal move drag-drop
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)

        # Auto-expand on hover (500ms delay)
        self.setAutoExpandDelay(500)

        # Selection
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        # Styling
        self.setIndentation(16)
        self.setHeaderHidden(True)
        self.setAnimated(True)
```

### 5.3 Environment Switcher Bar

```python
class EnvironmentSwitcherBar(QWidget):
    """
    Compact environment switcher with sync status.
    """

    environment_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # Label
        label = QLabel("Environment:")
        label.setStyleSheet("color: #808080; font-size: 11px;")
        layout.addWidget(label)

        # Dropdown
        self._combo = QComboBox()
        self._combo.setMinimumWidth(120)
        self._combo.currentTextChanged.connect(self._on_env_changed)
        layout.addWidget(self._combo)

        # Sync status indicator
        self._sync_indicator = QLabel()
        self._sync_indicator.setFixedSize(16, 16)
        layout.addWidget(self._sync_indicator)

        # Sync button
        sync_btn = QPushButton()
        sync_btn.setIcon(QIcon(":/icons/sync.svg"))
        sync_btn.setFixedSize(24, 24)
        sync_btn.setToolTip("Sync with central config")
        sync_btn.clicked.connect(self._on_sync)
        layout.addWidget(sync_btn)

        layout.addStretch()

        self._apply_style()

    def set_environments(self, environments: List[str], current: str):
        self._combo.blockSignals(True)
        self._combo.clear()
        self._combo.addItems(environments)
        self._combo.setCurrentText(current)
        self._combo.blockSignals(False)

    def set_sync_status(self, status: str):
        """Status: 'synced', 'modified', 'conflict'"""
        colors = {
            "synced": "#27AE60",    # Green
            "modified": "#F1C40F",  # Yellow
            "conflict": "#E74C3C", # Red
        }
        self._sync_indicator.setStyleSheet(
            f"background: {colors.get(status, '#808080')}; border-radius: 8px;"
        )
```

### 5.4 Variable Manager Panel

```python
class VariableManagerPanel(QWidget):
    """
    Tabular variable manager with scope filtering and inline editing.
    """

    variable_changed = Signal(str, object)  # name, value

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar
        toolbar = QHBoxLayout()

        # Scope filter
        self._scope_filter = QComboBox()
        self._scope_filter.addItems(["All", "Global", "Project", "Scenario"])
        self._scope_filter.currentTextChanged.connect(self._filter_by_scope)
        toolbar.addWidget(QLabel("Scope:"))
        toolbar.addWidget(self._scope_filter)

        toolbar.addStretch()

        # Search
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search variables...")
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(self._on_search)
        toolbar.addWidget(self._search)

        # Add button
        add_btn = QPushButton("+")
        add_btn.setFixedSize(28, 28)
        add_btn.clicked.connect(self._add_variable)
        toolbar.addWidget(add_btn)

        layout.addLayout(toolbar)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels([
            "Name", "Type", "Value", "Scope", "Env Override"
        ])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self._table)
```

### 5.5 Credential Binding Dialog

```python
class CredentialBindingDialog(QDialog):
    """
    Dialog for binding credentials with environment-specific overrides.
    """

    def __init__(self, binding: Optional[CredentialBinding] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Credential Binding")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        # Alias
        form = QFormLayout()
        self._alias_edit = QLineEdit()
        form.addRow("Alias:", self._alias_edit)

        # Type
        self._type_combo = QComboBox()
        self._type_combo.addItems([
            "username_password", "api_key", "oauth_token", "connection_string"
        ])
        form.addRow("Type:", self._type_combo)

        # Required
        self._required_check = QCheckBox("Required")
        self._required_check.setChecked(True)
        form.addRow("", self._required_check)

        layout.addLayout(form)

        # Environment bindings
        env_group = QGroupBox("Environment Bindings")
        env_layout = QVBoxLayout(env_group)

        self._env_table = QTableWidget()
        self._env_table.setColumnCount(2)
        self._env_table.setHorizontalHeaderLabels(["Environment", "Credential"])
        self._env_table.horizontalHeader().setStretchLastSection(True)
        env_layout.addWidget(self._env_table)

        layout.addWidget(env_group)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

        if binding:
            self._load_binding(binding)
```

### 5.6 Project Creation Wizard

```python
class ProjectWizard(QWizard):
    """
    Multi-step project creation wizard.
    """

    def __init__(self, templates: List[ProjectTemplate], parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Project")
        self.setMinimumSize(700, 500)

        # Pages
        self.addPage(TemplateSelectionPage(templates))
        self.addPage(ProjectDetailsPage())
        self.addPage(EnvironmentSetupPage())
        self.addPage(CredentialSetupPage())
        self.addPage(SummaryPage())

    def get_project_config(self) -> Dict[str, Any]:
        """Collect all wizard data into project config."""
        return {
            "template_id": self.field("template_id"),
            "name": self.field("project_name"),
            "description": self.field("description"),
            "path": self.field("project_path"),
            "environments": self.field("environments"),
            "credentials": self.field("credentials"),
        }


class TemplateSelectionPage(QWizardPage):
    """Page 1: Select project template."""

    def __init__(self, templates: List[ProjectTemplate], parent=None):
        super().__init__(parent)
        self.setTitle("Choose Template")
        self.setSubTitle("Select a template to start with or create from scratch.")

        layout = QVBoxLayout(self)

        # Template grid
        grid = QGridLayout()
        row, col = 0, 0

        # "Blank" option
        blank_card = TemplateCard("Blank Project", "Start from scratch", "file-blank")
        blank_card.clicked.connect(lambda: self._select_template(None))
        grid.addWidget(blank_card, row, col)
        col += 1

        for template in templates:
            if col >= 3:
                col = 0
                row += 1

            card = TemplateCard(template.name, template.description, template.icon)
            card.clicked.connect(lambda t=template: self._select_template(t))
            grid.addWidget(card, row, col)
            col += 1

        layout.addLayout(grid)
        layout.addStretch()

        self.registerField("template_id", self, "template_id")
```

### 5.7 Styling (Dark Theme)

```python
PROJECT_EXPLORER_STYLE = """
QDockWidget {
    background: #252526;
    color: #CCCCCC;
}

QDockWidget::title {
    background: #3C3C3C;
    padding: 6px;
    font-weight: bold;
}

QTreeView {
    background: #252526;
    border: none;
    color: #CCCCCC;
    selection-background-color: #094771;
    selection-color: #FFFFFF;
}

QTreeView::item {
    padding: 4px 0;
    border: none;
}

QTreeView::item:hover {
    background: #2A2D2E;
}

QTreeView::item:selected {
    background: #094771;
}

QTreeView::branch:has-children:!has-siblings:closed,
QTreeView::branch:closed:has-children:has-siblings {
    image: url(:/icons/chevron-right.svg);
}

QTreeView::branch:open:has-children:!has-siblings,
QTreeView::branch:open:has-children:has-siblings {
    image: url(:/icons/chevron-down.svg);
}

QComboBox {
    background: #3C3C3C;
    border: 1px solid #3C3C3C;
    border-radius: 2px;
    padding: 4px 8px;
    color: #CCCCCC;
}

QComboBox:hover {
    border: 1px solid #007ACC;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QLineEdit {
    background: #3C3C3C;
    border: 1px solid #3C3C3C;
    border-radius: 2px;
    padding: 4px 8px;
    color: #CCCCCC;
}

QLineEdit:focus {
    border: 1px solid #007ACC;
}

QPushButton {
    background: #0E639C;
    border: none;
    border-radius: 2px;
    padding: 6px 14px;
    color: #FFFFFF;
}

QPushButton:hover {
    background: #1177BB;
}

QPushButton:pressed {
    background: #094771;
}

QTableWidget {
    background: #252526;
    border: 1px solid #3C3C3C;
    gridline-color: #3C3C3C;
    color: #CCCCCC;
}

QTableWidget::item {
    padding: 4px;
}

QTableWidget::item:selected {
    background: #094771;
}

QHeaderView::section {
    background: #3C3C3C;
    border: none;
    padding: 6px;
    font-weight: bold;
}
"""
```

---

## 6. Recommendations Summary

### 6.1 Immediate Improvements (Phase 1)

1. **Enhanced Project Entity**: Add version, category, icon, color, environments
2. **Environment System**: Add `environments/` folder with dev/staging/prod configs
3. **Environment Switcher**: Simple dropdown in toolbar
4. **Variable Scope UI**: Add scope column and filter to variable editor

### 6.2 Medium-Term (Phase 2)

1. **Project Explorer Panel**: VS Code-style tree with drag-drop
2. **Credential Binding Dialog**: Environment-specific overrides
3. **Project Templates**: Web Scraping, Form Automation, etc.
4. **Tag System**: Cross-cutting organization with filter bar

### 6.3 Long-Term (Phase 3)

1. **Multi-Project Workspace**: `.code-workspace`-style support
2. **Team Collaboration**: Role-based access (like n8n Projects)
3. **External Vault Integration**: HashiCorp, AWS, Azure
4. **CI/CD Integration**: Export for SolutionPackager-style deployment

---

## 7. Sources

- [UiPath Orchestrator Folders](https://docs.uipath.com/orchestrator/docs/managing-folders)
- [UiPath Modern Folders Administration](https://docs.uipath.com/orchestrator/standalone/2024.10/user-guide/administration-of-modern-folders)
- [Power Automate Environment Variables](https://learn.microsoft.com/en-us/power-apps/maker/data-platform/environmentvariables-power-automate)
- [Power Automate Environment Variables Best Practices](https://www.azurecurve.co.uk/2024/02/working-with-power-automate-what-are-environment-variables-and-why-should-they-be-used/)
- [Automation Anywhere Credential Vault](https://docs.automationanywhere.com/bundle/enterprise-v2019/page/enterprise-cloud/topics/control-room/bots/credentials/cloud-credentials-overview.html)
- [n8n Projects and Folders](https://dev.to/brook_051cd08713006b/managing-n8n-projects-and-folders-4i06)
- [VS Code Workspaces](https://code.visualstudio.com/docs/editor/workspaces)
- [VS Code Tree View API](https://code.visualstudio.com/api/extension-guides/tree-view)
- [Qt Model/View Drag and Drop](https://www.kdab.com/modelview-drag-and-drop-part-1/)
- [PySide6 QTreeView Documentation](https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTreeView.html)

---

## Appendix: CasareRPA Current State Analysis

### Existing Components

| Component | File | Status |
|-----------|------|--------|
| Project Entity | `domain/entities/project/project.py` | Basic, needs enhancement |
| Variable Scoping | `domain/entities/project/variables.py` | Has GLOBAL/PROJECT/SCENARIO |
| Credential Binding | `domain/entities/project/credentials.py` | Has alias->vault_path |
| Credential Store | `infrastructure/security/credential_store.py` | Full-featured |
| Project Manager Dialog | `presentation/canvas/ui/dialogs/project_manager_dialog.py` | Basic tree view |

### Key Gaps

1. **No Environment System**: Only project-level settings, no dev/staging/prod
2. **No Environment Switcher UI**: No way to switch contexts
3. **No Credential Overrides**: Same credential for all environments
4. **Basic Project Explorer**: QTreeWidget, no drag-drop, limited features
5. **No Project Templates**: Must create from scratch every time
6. **No Tags**: Only folder-based organization
