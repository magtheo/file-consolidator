# core/file_processor.py
import os
from pathlib import Path
import fnmatch
from . import config # Import config from the same package

class FileProcessor:
    def __init__(self):
        self.ignore_patterns = config.DEFAULT_IGNORE_PATTERNS
        self.max_file_size_bytes = config.MAX_FILE_SIZE_TO_READ_MB * 1024 * 1024

    def _is_ignored(self, path_obj: Path, root_path_obj: Path) -> bool:
        """Checks if a path should be ignored based on ignore_patterns."""
        # Check against item name
        if any(fnmatch.fnmatch(path_obj.name, pattern) for pattern in self.ignore_patterns):
            return True
        # Check against relative path
        try:
            relative_path_str = str(path_obj.relative_to(root_path_obj))
            if any(fnmatch.fnmatch(relative_path_str, pattern) for pattern in self.ignore_patterns):
                return True
            # Check if any part of the relative path matches a directory ignore pattern (e.g., "venv/")
            parts = relative_path_str.split(os.sep)
            current_path = ""
            for part in parts:
                current_path = os.path.join(current_path, part)
                if any(fnmatch.fnmatch(current_path + os.sep, pattern) for pattern in self.ignore_patterns if pattern.endswith(('/', '\\'))):
                     return True
                if any(fnmatch.fnmatch(current_path, pattern) for pattern in self.ignore_patterns if not pattern.endswith(('/', '\\')) and path_obj.is_dir()): # e.g. "node_modules"
                     return True


        except ValueError: # Not a subpath, should not happen if root_path_obj is correct
            pass
        return False

    def generate_file_tree(self, root_path_str: str, custom_ignore_patterns=None):
        """
        Generates a tree-like structure of files and directories.
        Returns a list of dictionaries, where each dictionary represents a file or directory.
        Example item: {'name': 'item_name', 'path': '/full/path/to/item', 'type': 'file'/'directory', 'children': []}
        """
        current_ignore_patterns = custom_ignore_patterns if custom_ignore_patterns is not None else self.ignore_patterns
        
        root_path = Path(root_path_str).resolve()
        if not root_path.is_dir():
            raise ValueError(f"Provided path '{root_path_str}' is not a valid directory.")

        tree_data = []

        for item in sorted(root_path.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
            if self._is_ignored(item, root_path):
                continue

            item_info = {
                "name": item.name,
                "path": str(item.resolve()),
                "type": "file" if item.is_file() else "directory"
            }

            if item.is_dir():
                # Recursively get children, but pass their paths relative to the original root for ignoring
                item_info["children"] = self._generate_subtree(item, root_path, current_ignore_patterns)
            
            tree_data.append(item_info)
        
        return tree_data

    def _generate_subtree(self, dir_path: Path, overall_root_path: Path, ignore_patterns):
        """Helper for recursive subtree generation."""
        children_data = []
        try:
            for item in sorted(dir_path.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
                if self._is_ignored(item, overall_root_path): # Always check against the overall root
                    continue

                item_info = {
                    "name": item.name,
                    "path": str(item.resolve()),
                    "type": "file" if item.is_file() else "directory"
                }
                if item.is_dir():
                    item_info["children"] = self._generate_subtree(item, overall_root_path, ignore_patterns)
                children_data.append(item_info)
        except PermissionError:
            # If we can't access a directory, add a placeholder or skip
            children_data.append({
                "name": f"[Access Denied] {dir_path.name}",
                "path": str(dir_path.resolve()),
                "type": "directory_error", # Custom type
                "children": []
            })
        return children_data


    def read_file_content(self, file_path_str: str) -> str:
        """Reads content of a single file."""
        file_path = Path(file_path_str)
        try:
            if file_path.stat().st_size > self.max_file_size_bytes:
                return f"[File too large (>{config.MAX_FILE_SIZE_TO_READ_MB}MB): {file_path.name}]"

            # Try to detect if it's a binary file (simple check)
            # This is not foolproof but can help avoid reading large binary files as text.
            try:
                with file_path.open('rb') as f_bin:
                    chunk = f_bin.read(1024) # Read first 1KB
                    if b'\0' in chunk: # Null byte often indicates binary
                        return f"[Likely binary file, skipped: {file_path.name}]"
            except Exception:
                pass # If we can't read it as binary, try as text

            with file_path.open('r', encoding=config.DEFAULT_ENCODING, errors='ignore') as f:
                return f.read()
        except FileNotFoundError:
            return f"[File not found: {file_path.name}]"
        except PermissionError:
            return f"[Permission denied: {file_path.name}]"
        except Exception as e:
            return f"[Error reading {file_path.name}: {e}]"

    def consolidate_files_content(self, file_paths: list[str], root_dir_path_str: str = None) -> str:
        """
        Consolidates content of multiple files into a single string.
        Adds separators and file path indicators.
        Uses relative paths if root_dir_path_str is provided.
        """
        consolidated_texts = []
        
        try:
            root_dir = Path(root_dir_path_str).resolve() if root_dir_path_str else None
        except Exception: # Handle invalid root_dir_path_str gracefully
            root_dir = None

        for file_path_str in file_paths:
            file_path_obj = Path(file_path_str).resolve()
            
            display_path = file_path_str # Fallback
            if root_dir:
                try:
                    # Ensure file_path_obj is actually within root_dir before making relative
                    if file_path_obj.is_relative_to(root_dir):
                         display_path = str(file_path_obj.relative_to(root_dir))
                    else: # If not relative (e.g. symlink outside), use full path or just name
                        display_path = str(file_path_obj) # Or file_path_obj.name
                except ValueError: # Not a subpath
                    display_path = str(file_path_obj) # Fallback to absolute path
            else:
                display_path = str(file_path_obj) # Use absolute path if no root_dir

            content = self.read_file_content(str(file_path_obj))
            
            header = f"--- FILE: {display_path} ---"
            footer = f"--- END OF FILE: {display_path} ---"
            
            consolidated_texts.append(f"{header}\n{content}\n{footer}\n\n")
            
        return "".join(consolidated_texts)