# Contributing to CasareRPA

Thank you for your interest in contributing to CasareRPA! We want to make it as easy as possible for you to join this project.

## Getting Started

1.  **Fork the repository** on GitHub.
2.  **Clone your fork** locally.
3.  **Create a virtual environment** and install dependencies (see [README.md](README.md)).
4.  **Create a branch** for your feature or bug fix: `git checkout -b feature/amazing-feature`.

## Development Workflow

We follow a structured workflow to maintain code quality:

### 1. Code Style
We use strict coding standards enforced by `ruff` and `black`.
-   **Linting**: `ruff check src/`
-   **Formatting**: `black src/ tests/`
-   **Type Checking**: `mypy src/casare_rpa`

Please ensure your code passes these checks before submitting a PR.

### 2. Testing
We use `pytest` for testing.
-   Run all tests: `pytest`
-   Run specific tests: `pytest tests/domain/test_my_feature.py`

New features should include unit tests. Integration tests are encouraged where possible.

### 3. Commit Messages
We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:
-   `feat: add new browser node`
-   `fix: resolve crash on startup`
-   `docs: update installation guide`
-   `refactor: simplify event bus`

## Pull Requests

1.  Push your branch to your fork.
2.  Open a Pull Request against the `main` branch.
3.  Fill out the PR template describing your changes.
4.  Wait for code review and address any feedback.

## Reporting Bugs

Please use the [GitHub Issue Tracker](https://github.com/omerlefaruk/CasareRPA/issues) to report bugs. Include:
-   Steps to reproduce.
-   Expected vs. actual behavior.
-   Logs or screenshots if applicable.

## Code of Conduct

Please note that we have a [Code of Conduct](CODE_OF_CONDUCT.md). Please follow it in all your interactions with the project.
