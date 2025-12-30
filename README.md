# CasareRPA

**The Next-Generation Windows Desktop RPA Platform**

CasareRPA is a high-performance, open-source Robotic Process Automation (RPA) platform built for Windows. It combines a powerful visual workflow editor with a modern, clean architecture backend to deliver reliable and scalable automation solutions.

![CasareRPA Banner](docs/images/banner.png) *(Note: Placeholder for banner image)*

## Features

-   **Visual Workflow Editor**: Drag-and-drop interface for creating complex automation flows.
-   **Modern Tech Stack**: Built with Python 3.12, PySide6, and Playwright.
-   **Clean Architecture**: Domain-Driven Design (DDD) principles ensure maintainability and testability.
-   **Browser Automation**: robust web scraping and interaction using Playwright.
-   **Desktop Automation**: Control Windows applications with UIAutomation and PyWin32.
-   **AI Integration**: Seamlessly integrate LLMs (Gemini, Claude, OpenAI) into your workflows.
-   **Extensible Node System**: Easily create custom nodes for specific tasks.

## Getting Started

### Prerequisites

-   Windows 10/11
-   Python 3.12+
-   Git

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/omerlefaruk/CasareRPA.git
    cd CasareRPA
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv .venv
    .venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -e ".[dev]"
    ```
    *Note: This installs the package in editable mode with development dependencies.*

4.  **Install Playwright browsers:**
    ```bash
    playwright install
    ```

5.  **Configure the environment:**
    -   Copy `config/settings.example.json` to `config/settings.json`.
    -   Copy `.env.example` to `.env` and fill in any required API keys (e.g., for AI features).

Launch the CasareRPA Canvas (V2 UI by default):
```bash
python manage.py canvas
```

To launch the legacy V1 UI:
```bash
python manage.py canvas --v1
```

Or via environment variables:
```bash
# Windows
set CASARE_UI_V1=1
python manage.py canvas
```

### Run Modes
- **Dev Mode**: Uses local source code and supports auto-reload (for Orchestrator).
- **Packaged Mode**: Application bundled as an executable (managed via `scripts/build.py`).

## Documentation

Full documentation is available in the `docs/` directory.

-   [User Guide](docs/user-guide/index.md)
-   [Developer Guide](docs/developer-guide/index.md)
-   [Architecture Overview](docs/developer-guide/architecture/index.md)

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to get started.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
