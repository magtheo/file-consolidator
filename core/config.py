# core/config.py

# Default patterns for files and directories to ignore during scanning.
# Uses fnmatch-style wildcards.
# Patterns can match file/directory names or relative paths from the root.
DEFAULT_IGNORE_PATTERNS = [
    ".git",
    ".vscode",
    "__pycache__",
    "*.pyc",
    "*.pyo",
    "*.so",
    "*.egg-info",
    "venv/",
    ".venv/",
    "env/",
    ".env/",
    "node_modules/",
    "build/",
    "dist/",
    ".DS_Store",
    "Thumbs.db",
    "*.log",
    "*.tmp",
    "*.swp",
    "*.swo",
]

# Maximum file size in Megabytes to attempt to read.
# Helps prevent freezing the app when a huge (binary) file is accidentally selected.
MAX_FILE_SIZE_TO_READ_MB = 5

# Default encoding to try when reading files.
# 'errors="ignore"' will be used if decoding fails.
DEFAULT_ENCODING = "utf-8"