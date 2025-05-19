# LLM Context Builder

A simple Python GUI application to help you select files from a project, view their structure, and consolidate their content into a single text block. This text can then be easily copied and pasted into a Large Language Model (LLM) as context for development tasks.

## Features

*   Browse directory structures.
*   Select specific files for inclusion.
*   View consolidated content with clear file path separators.
*   Copy consolidated content to the clipboard with one click.
*   Configurable ignore patterns for files and directories (edit `core/config.py`).

## Requirements

*   Python 3.7+
*   Tkinter (usually included with Python)
*   `pyperclip` library
*   PyQt6

## Installation

1.  **Clone the repository (or create the files manually):**
    ```bash
    # If you have a git repo:
    # git clone <your-repo-url>
    # cd project_root
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    ```

3.  **Activate the virtual environment:**
    *   On macOS and Linux:
        ```bash
        source venv/bin/activate
        ```
    *   On Windows:
        ```bash
        venv\Scripts\activate
        ```

4.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `pyperclip` might require `xclip` or `xsel` on Linux, or `pbcopy`/`pbpaste` (default on macOS), or it uses Windows built-in clipboard functions.*

## Usage

1.  Navigate to the `project_root` directory.
2.  Run the application:
    ```bash
    python main.py
    ```
3.  Click "Select Root Directory" to choose the project folder you want to analyze.
4.  The file structure will appear. Select the files you want to include.
    *   Selecting a directory in the tree view will include all files within that directory (recursively) when consolidated.
5.  Click "Consolidate Selected Files".
6.  The combined content will appear in the "Consolidated Output" text area.
7.  Click "Copy to Clipboard" to copy the text.

## Configuration

You can modify default ignored files and directories by editing the `DEFAULT_IGNORE_PATTERNS` list in `project_root/core/config.py`.
