# md2epub

**md2epub** is a helper library and CLI tool designed to convert Markdown text into professional, publish-ready EPUB files. It specifically targets formatting standards suitable for KDP (Kindle Direct Publishing), ensuring strict ordering of content.

## Features

* **Project Scaffolding**: Quickly initialize a book directory with a standard structure using Cookiecutter templates.
* **Markdown to EPUB**: Converts Markdown content into XHTML with a generated navigation structure.
* **KDP-Ready Styling**: Includes a CSS template optimized for e-readers, handling fonts, margins, and scene breaks.
* **Custom Formatting**: Specific support for novel formatting:
    * `xxx` on a single line creates a centered **Scene Break**.
    * `***` on a single line creates a centered **Asterisk Break**.

## Quick Start

Install the package and initialize your first book:

```bash
pip install md2epub
md2epub init my_first_book
```

