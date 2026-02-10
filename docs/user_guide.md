This file contains the detailed instructions for writers using your tool.

```markdown
# User Guide

## Installation

Ensure you have Python 3.12 or higher installed.

```bash
pip install md2epub
```

## Creating a New Book

To start a new project, use the init command. This creates a folder with all the necessary configuration files and templates.

```bash
md2epub init my_new_book
```

You will be prompted for basic details (Book Name, Author Name, Dedications, etc.) which are used to configure the project.

## Writing Your Content

Navigate to your new book directory. You will see several markdown files (e.g., chapter_01.md, title.md). Write your book using standard Markdown.

### Formatting Tips:

* Chapters: Start chapters with a header # Chapter Title.

* Scene Breaks: To insert a visible break in the text, place xxx on its own line.

* Asterisks: To insert a decorative break, place *** on its own line.

### Configuration (`metadata.yaml`)

The metadata.yaml file controls the build process. You must list every file you want to include in the EPUB here.

```
title: "My Great Novel"
author: "Jane Doe"
language: en
cover_image: cover.png
front_matter:
  - title.md
  - copyright.md
  - dedication.md
chapters:
  - chapter_01.md
  - chapter_02.md
```

## Compiling the EPUB

When you are ready to generate your book:

```bash
md2epub compile my_new_book
```

This will generate an .epub file in the current directory.

## Reverse Engineering (Unpacking)

If you have an existing EPUB file that you want to convert into a `md2epub` project structure (e.g., to recover source files or migrate an existing book):

1. Run the `unpack` command:

```bash
md2epub unpack my_existing_book.epub my_project_dir
```

2. This will create `my_project_dir` containing:
    * `metadata.yaml`: Reconstructed configuration file with Title, Author, and file ordering.
    * `images/`: A directory containing all images extracted from the EPUB.
    * Markdown files: Chapters and front matter converted from the EPUB's internal HTML.

3. You can now edit the markdown files or `metadata.yaml` and re-compile the book using `md2epub compile`.