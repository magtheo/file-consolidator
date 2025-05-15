# core/config.py
from pathlib import Path
import appdirs # For user-specific config directory

# Application name for appdirs
APP_NAME = "LLMContextBuilder"
APP_AUTHOR = "YourAppNameOrAuthor" # Optional, but good practice

# Default patterns for files and directories to ignore during scanning.
DEFAULT_IGNORE_PATTERNS = [
    ".git", ".vscode", "__pycache__", "*.pyc", "*.pyo", "*.so",
    "*.egg-info", "venv/", ".venv/", "env/", ".env/", "node_modules/",
    "build/", "dist/", ".DS_Store", "Thumbs.db", "*.log", "*.tmp",
    "*.swp", "*.swo",
]

MAX_FILE_SIZE_TO_READ_MB = 5
DEFAULT_ENCODING = "utf-8"

# Path for user-specific ignore patterns file
USER_CONFIG_DIR = Path(appdirs.user_config_dir(APP_NAME, APP_AUTHOR))
USER_IGNORE_FILE = USER_CONFIG_DIR / "user_ignores.txt"

# Ensure the user config directory exists
USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)