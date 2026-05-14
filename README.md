# Split PDF by Bookmark

A GUI tool that splits a PDF file into multiple smaller files based on its **bookmarks** (outline/table of contents).

---

## Features

- Simple graphical interface built with PyQt5
- Automatically reads bookmarks from a PDF file
- Splits each bookmark into a separate PDF file
- Supports configurable bookmark depth (top-level, sub-chapters, ...)
- Output files are automatically named after their bookmark titles
- Displays a live log and progress bar during processing

---

## Requirements

- Python 3.8+
- Libraries:

```
PyQt5
pypdf
```

Quick install:

```bash
pip install PyQt5
pip install pypdf
pip install cryptography
```

---

## Usage

```bash
python split_pdf_by_bookmark.py
```

---

## Step-by-step Guide

### 1. Select input PDF

Click **Browse...** next to the **Input PDF File** field and select the PDF you want to split.

> After selecting a file, the output directory will be auto-filled to `<filename>_chapters/` in the same folder as the PDF.

### 2. Select output directory (optional)

Click **Browse...** next to the **Output Directory** field to choose where the split PDF files will be saved.  
If left empty, the program will create a `<filename>_chapters/` folder next to the original PDF.

### 3. Set Bookmark depth

| Value | Meaning |
|-------|---------|
| `0` | Top-level bookmarks only |
| `1` | Include first-level sub-chapters |
| `2+` | Include deeper nested levels |

> Use `0` to split by main chapters/sections.

### 4. Run

Click the **▶ Split PDF** button to start.

- The log area will list all found bookmarks with their page numbers.
- The progress bar shows the current progress.
- A completion message will appear in the log when done.

---

## Output

Each output file is named using the format:

```
01_Bookmark_Title.pdf
02_Bookmark_Title.pdf
...
```

Special characters in bookmark titles are removed automatically. File names are capped at 100 characters.

---

## Notes

- The input PDF must have **bookmarks** (outline). If none are found, the program will display an error.
- Each output file contains the pages from the start of that bookmark up to (but not including) the next bookmark.
