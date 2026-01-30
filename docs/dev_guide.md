# Developer Guide

## Development Setup

1.  Clone the repository.
2.  Install the package in editable mode with development dependencies.

```bash
python -m pip install --upgrade pip
pip install -e .[dev]
```

## Running Tests

The project uses pytest for testing. A custom script scripts/run_tests.py is provided to run tests and enforce coverage thresholds.

```bash
python scripts/run_tests.py
```

* **Failure Threshold:** The build fails if more than 20% of tests fail.

* **Coverage Threshold:**

    * Codebase < 1000 lines: 60% coverage required.

    * Codebase >= 1000 lines: 80% coverage required.

## Project Architecture

The codebase follows the SOLID principles, separating concerns into distinct modules:

* `cli.py`: Handles user interaction and commands (init, compile).

* `epub_builder.py`: The core logic class responsible for assembling the book and ensuring strictly ordered spine items.

* `converter.py`: Handles text processing, converting Markdown to HTML and injecting custom classes for separators.

* `css_template.py`: Contains the KDP_CSS string used to style the EPUB.

## Release Workflow

The project uses GitHub Actions for CI/CD.

* **Pull Requests:** PRs to main must come from dev. PRs to dev must come from feature branches.

* **Versioning:** Semantic versioning is automated based on PR labels (bump:major, bump:patch, or default minor).