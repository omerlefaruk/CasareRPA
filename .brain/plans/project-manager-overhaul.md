# Project Manager Overhaul - Full Design Plan

## Overview
Complete redesign of Project Manager with VS Code-style explorer, environments (dev/staging/prod), folder organization, global credentials, and project templates using real nodes.

## User Requirements
- [x] Full overhaul (new Project Manager window)
- [x] Dockable side panel for variables (VS Code Explorer style)
- [x] Folders/categories for project organization
- [x] Global credentials (shared, projects reference by alias)
- [x] Project templates using real nodes from database
- [x] Environment support (dev/staging/prod)

---

## Phase 1: Domain Layer Extensions

### 1.1 New Entity: Environment
**File**: `src/casare_rpa/domain/entities/project/environment.py`

```python
@dataclass
class Environment:
    id: str                          # env_uuid8
    name: str                        # "development", "staging", "production"
    description: str
    variables: Dict[str, Any]        # Environment-specific variable overrides
    credential_overrides: Dict[str, str]  # alias -> credential_id per env
    settings: EnvironmentSettings
    is_default: bool
    created_at: datetime
    modified_at: datetime

@dataclass
class EnvironmentSettings:
    api_base_urls: Dict[str, str]    # service -> URL mapping
    timeout_override: Optional[int]
    retry_count_override: Optional[int]
    feature_flags: Dict[str, bool]
```

### 1.2 New Entity: ProjectFolder
**File**: `src/casare_rpa/domain/entities/project/folder.py`

```python
@dataclass
class ProjectFolder:
    id: str                          # fold_uuid8
    name: str
    parent_id: Optional[str]         # For nested hierarchy
    description: str
    color: str                       # Hex color for UI
    icon: str                        # Icon name
    project_ids: List[str]           # Projects in this folder
    is_expanded: bool                # UI state
    sort_order: int
    created_at: datetime
```

### 1.3 New Entity: ProjectTemplate
**File**: `src/casare_rpa/domain/entities/project/template.py`

```python
@dataclass
class ProjectTemplate:
    id: str                          # tmpl_uuid8
    name: str
    description: str
    category: str                    # "Web Scraping", "Google Workspace", etc.
    icon: str
    color: str
    tags: List[str]

    # Template content
    base_workflow: Dict[str, Any]    # Starter workflow JSON
    default_variables: List[Variable]
    default_credentials: List[CredentialBinding]
    default_settings: ProjectSettings
    default_environments: List[Environment]

    # Metadata
    version: str
    author: str
    difficulty: str                  # "beginner", "intermediate", "advanced"
    estimated_nodes: int
    preview_image: Optional[str]     # Base64 or path
    created_at: datetime
```

### 1.4 Extended Project Entity
**Updates to**: `src/casare_rpa/domain/entities/project/project.py`

Add fields:
```python
folder_id: Optional[str] = None          # Which folder contains this project
template_id: Optional[str] = None        # Created from template
environment_ids: List[str] = field(default_factory=list)
active_environment_id: Optional[str] = None
```

### 1.5 Schema Migration
- Current: `PROJECT_SCHEMA_VERSION = "1.0.0"`
- New: `PROJECT_SCHEMA_VERSION = "2.0.0"`
- Migration: Auto-create "default" environment for v1 projects

---

## Phase 2: Repository Layer

### 2.1 New Repository Interfaces

**EnvironmentRepository** (`domain/repositories/environment_repository.py`):
```python
class EnvironmentRepository(ABC):
    async def get(self, project_id: str, env_id: str) -> Optional[Environment]
    async def get_all(self, project_id: str) -> List[Environment]
    async def save(self, project_id: str, environment: Environment) -> None
    async def delete(self, project_id: str, env_id: str) -> None
    async def get_active(self, project_id: str) -> Optional[Environment]
```

**FolderRepository** (`domain/repositories/folder_repository.py`):
```python
class FolderRepository(ABC):
    async def get(self, folder_id: str) -> Optional[ProjectFolder]
    async def get_all(self) -> List[ProjectFolder]
    async def get_children(self, parent_id: Optional[str]) -> List[ProjectFolder]
    async def save(self, folder: ProjectFolder) -> None
    async def delete(self, folder_id: str) -> None
    async def move_project(self, project_id: str, folder_id: Optional[str]) -> None
```

**TemplateRepository** (`domain/repositories/template_repository.py`):
```python
class TemplateRepository(ABC):
    async def get(self, template_id: str) -> Optional[ProjectTemplate]
    async def get_all() -> List[ProjectTemplate]
    async def get_by_category(category: str) -> List[ProjectTemplate]
    async def create_project_from(template_id: str, name: str, path: Path) -> Project
```

---

## Phase 3: Infrastructure Layer

### 3.1 File Storage Structure (v2.0.0)
```
~/.casare_rpa/
├── config/
│   ├── folders.json           # Global folder hierarchy
│   └── templates/             # Built-in templates
│       ├── web_scraping.json
│       ├── google_workspace.json
│       └── ...
├── credentials/
│   └── credentials.enc        # Global encrypted credentials
└── projects_index.json        # All projects registry

ProjectFolder/
├── project.json               # Updated schema v2.0.0
├── variables.json             # Project-level defaults
├── credentials.json           # Credential bindings (aliases)
├── environments/              # NEW
│   ├── development.json
│   ├── staging.json
│   └── production.json
└── scenarios/
    └── *.json
```

### 3.2 Built-in Templates (8 templates)

| Template | Category | Nodes | Difficulty |
|----------|----------|-------|------------|
| Web Scraping Starter | Web | 8 | Beginner |
| Google Workspace Integration | Google | 12 | Intermediate |
| Desktop Automation Suite | Desktop | 10 | Advanced |
| Data ETL Pipeline | Data | 9 | Intermediate |
| Email & Document Processing | Email | 8 | Intermediate |
| API Integration & Webhooks | API | 6 | Beginner |
| Scheduled Notification System | Messaging | 5 | Beginner |
| Office Document Automation | Office | 8 | Intermediate |

---

## Phase 4: Application Layer (Use Cases)

### 4.1 New Use Cases

**Environment Management**:
- `CreateEnvironmentUseCase`
- `UpdateEnvironmentUseCase`
- `DeleteEnvironmentUseCase`
- `SwitchEnvironmentUseCase`
- `CloneEnvironmentUseCase`

**Folder Management**:
- `CreateFolderUseCase`
- `RenameFolderUseCase`
- `DeleteFolderUseCase`
- `MoveProjectToFolderUseCase`
- `ReorderFoldersUseCase`

**Template Management**:
- `ListTemplatesUseCase`
- `CreateProjectFromTemplateUseCase`
- `PreviewTemplateUseCase`

---

## Phase 5: Presentation Layer (UI)

### 5.1 Project Explorer Panel (VS Code Style)
**File**: `src/casare_rpa/presentation/canvas/ui/panels/project_explorer_panel.py`

```
┌─────────────────────────────────────┐
│ PROJECT EXPLORER            [≡] [+] │
├─────────────────────────────────────┤
│ 🔍 Search projects...               │
├─────────────────────────────────────┤
│ ▼ 📁 Client Projects                │
│   ├── 📦 Acme Corp RPA              │
│   │   ├── 📄 Invoice Processing     │
│   │   └── 📄 Report Generation      │
│   └── 📦 BigBank Automation         │
│       └── 📄 Loan Application       │
│ ▼ 📁 Internal Tools                 │
│   └── 📦 Data Migration             │
│ ── 📦 Unsorted Project              │
├─────────────────────────────────────┤
│ [+ New Project] [📁 New Folder]     │
└─────────────────────────────────────┘
```

**Features**:
- Drag-drop projects between folders
- Right-click context menu (rename, delete, duplicate)
- Double-click to open project
- Expand/collapse folders
- Search/filter across all projects

### 5.2 Environment Switcher Bar
**File**: `src/casare_rpa/presentation/canvas/ui/widgets/environment_switcher.py`

```
┌────────────────────────────────────────────────┐
│ Environment: [▼ Development] │ ● Synced │ [⚙]  │
└────────────────────────────────────────────────┘
```

**Features**:
- Dropdown to switch environments
- Sync status indicator
- Quick access to environment settings
- Color-coded by environment (green=dev, yellow=staging, red=prod)

### 5.3 Variables Panel (Dockable)
**File**: `src/casare_rpa/presentation/canvas/ui/panels/variables_manager_panel.py`

```
┌─────────────────────────────────────────────────┐
│ VARIABLES                           [≡] [+] [🔍]│
├─────────────────────────────────────────────────┤
│ Scope: [All ▼] [Global│Project│Environment]     │
├─────────────────────────────────────────────────┤
│ Name          │ Value           │ Scope │ Type  │
├───────────────┼─────────────────┼───────┼───────┤
│ api_url       │ https://dev...  │ Env   │ str   │
│ max_retries   │ 3               │ Proj  │ int   │
│ debug_mode    │ true            │ Glob  │ bool  │
│ credentials   │ ••••••••        │ Glob  │ secret│
├─────────────────────────────────────────────────┤
│ [+ Add Variable]                                │
└─────────────────────────────────────────────────┘
```

**Features**:
- Filter by scope (Global/Project/Environment)
- Inline editing
- Type validation
- Secret masking
- Search across all variables
- Import/Export (JSON/CSV)

### 5.4 Credentials Panel
**File**: `src/casare_rpa/presentation/canvas/ui/panels/credentials_panel.py`

```
┌─────────────────────────────────────────────────┐
│ CREDENTIALS                         [≡] [+] [⚙]│
├─────────────────────────────────────────────────┤
│ 🔑 API Keys                                     │
│   ├── openai_key (OpenAI)           [Test] [✏]│
│   └── anthropic_key (Anthropic)     [Test] [✏]│
│ 🔐 Logins                                       │
│   ├── erp_login (SAP)                      [✏]│
│   └── email_smtp (Gmail)                   [✏]│
│ 🌐 Google Accounts                              │
│   └── workspace@company.com         [Refresh]  │
├─────────────────────────────────────────────────┤
│ [+ Add Credential] [Import] [Export]            │
└─────────────────────────────────────────────────┘
```

### 5.5 New Project Wizard (with Templates)
**File**: `src/casare_rpa/presentation/canvas/ui/dialogs/project_wizard_dialog.py`

```
┌─────────────────────────────────────────────────────────┐
│                   CREATE NEW PROJECT                     │
├──────────────────────────────────────────────────────────┤
│  Step 1 of 3: Choose Template                            │
│                                                          │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │
│  │ 🌐      │ │ 📧      │ │ 🖥️      │ │ 📊      │        │
│  │ Web     │ │ Google  │ │ Desktop │ │ Data    │        │
│  │ Scraping│ │ Workspace│ │ Auto   │ │ ETL     │        │
│  │ ✓       │ │         │ │         │ │         │        │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘        │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │
│  │ 📬      │ │ 🔗      │ │ 🔔      │ │ 📝      │        │
│  │ Email   │ │ API     │ │ Notifi- │ │ Office  │        │
│  │ Docs    │ │ Webhooks│ │ cations │ │ Docs    │        │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘        │
│  ┌─────────┐                                             │
│  │ ⬜      │                                             │
│  │ Blank   │                                             │
│  │ Project │                                             │
│  └─────────┘                                             │
│                                                          │
│                              [Back] [Next →]             │
└──────────────────────────────────────────────────────────┘
```

**Step 2**: Project details (name, location, folder, description)
**Step 3**: Environment setup (create dev/staging/prod)

### 5.6 Project Settings Dialog
**File**: `src/casare_rpa/presentation/canvas/ui/dialogs/project_settings_dialog.py`

Tabs:
1. **General**: Name, description, author, tags
2. **Environments**: Manage dev/staging/prod
3. **Variables**: Project-level defaults
4. **Credentials**: Binding aliases to global credentials
5. **Execution**: Timeout, retries, browser settings

---

## Phase 6: Integration Points

### 6.1 Main Window Changes
- Add Project Explorer to left dock (collapsible)
- Add Environment Switcher to toolbar
- Add Variables Panel to side dock
- Update status bar with current project + environment

### 6.2 Menu Changes
**File Menu**:
- New Project... → Project Wizard
- Open Project... → File dialog
- Recent Projects → Submenu
- Project Settings... → Settings dialog
- Close Project

**View Menu**:
- Project Explorer (toggle)
- Variables Panel (toggle)
- Credentials Panel (toggle)

### 6.3 Keyboard Shortcuts
| Action | Shortcut |
|--------|----------|
| New Project | Ctrl+Shift+N |
| Project Settings | Ctrl+, |
| Toggle Explorer | Ctrl+Shift+E |
| Switch Environment | Ctrl+Shift+E (hold) |

---

## Implementation Order

### Sprint 1: Domain Foundation
1. Create Environment entity
2. Create ProjectFolder entity
3. Create ProjectTemplate entity
4. Extend Project entity
5. Update schema to v2.0.0
6. Create migration logic

### Sprint 2: Repository & Storage
1. Implement EnvironmentRepository
2. Implement FolderRepository
3. Implement TemplateRepository
4. Update ProjectStorage for new structure
5. Create 8 built-in templates

### Sprint 3: Use Cases
1. Environment management use cases
2. Folder management use cases
3. Template use cases
4. Integration with existing ProjectController

### Sprint 4: UI - Core Panels
1. Project Explorer Panel
2. Variables Manager Panel
3. Environment Switcher widget
4. Credentials Panel

### Sprint 5: UI - Dialogs & Integration
1. Project Wizard Dialog
2. Project Settings Dialog
3. Main Window integration
4. Menu updates
5. Keyboard shortcuts

### Sprint 6: Polish & Testing
1. Drag-drop for folders
2. Search/filter functionality
3. Import/Export
4. Unit tests
5. Integration tests

---

## Resolved Decisions

1. **Environment inheritance**: YES - staging inherits from dev, prod from staging (cascade)
2. **Default environments**: Create all 3 (dev/staging/prod) by default
3. **Folder colors**: Predefined palette (8 colors)
4. **Template previews**: Description only (no thumbnails)
5. **Variables import**: Support .env file import

---

## Success Criteria

- [ ] Users can organize projects in folders with drag-drop
- [ ] Users can switch environments with one click
- [ ] Users can manage variables across scopes in one panel
- [ ] Users can create projects from 8+ templates
- [ ] Users can reference global credentials in projects
- [ ] Schema migration from v1→v2 is seamless
- [ ] All existing projects continue to work

---

**Last Updated**: 2025-12-08
**Status**: Planning
**Author**: Claude (Architect Agent)
