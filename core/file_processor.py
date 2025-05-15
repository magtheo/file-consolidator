# core/file_processor.py
import os
from pathlib import Path
import fnmatch
from . import config # Import config from the same package

class FileProcessor:
    def __init__(self):
        self.ignore_patterns = config.DEFAULT_IGNORE_PATTERNS
        self.max_file_size_bytes = config.MAX_FILE_SIZE_TO_READ_MB * 1024 * 1024

    def _is_ignored(self, path_obj: Path, root_path_obj: Path, current_scan_ignore_patterns: list) -> bool: # Added current_scan_ignore_patterns
        """Checks if a path should be ignored based on combined ignore_patterns."""
        # Check against item name
        if any(fnmatch.fnmatch(path_obj.name, pattern) for pattern in current_scan_ignore_patterns):
            return True
        # Check against relative path
        try:
            relative_path_str = str(path_obj.relative_to(root_path_obj))
            if any(fnmatch.fnmatch(relative_path_str, pattern) for pattern in current_scan_ignore_patterns):
                return True
            parts = relative_path_str.split(os.sep)
            current_path_part = ""
            for part in parts:
                current_path_part = os.path.join(current_path_part, part)
                if any(fnmatch.fnmatch(current_path_part + os.sep, p) for p in current_scan_ignore_patterns if p.endswith(('/', '\\'))):
                    return True
                if path_obj.is_dir() and any(fnmatch.fnmatch(current_path_part, p) for p in current_scan_ignore_patterns if not p.endswith(('/', '\\')) and Path(p).name == current_path_part):
                    return True
        except ValueError:
            pass
        return False

    def generate_file_tree(self, root_path_str: str, additional_ignore_patterns: list = None): # Modified signature
        """
        Generates a tree-like structure of files and directories.
        Combines default ignore patterns with additionally provided ones.
        """
        # Combine default and additional ignore patterns for this scan
        current_scan_ignore_patterns = list(self.ignore_patterns) # Start with a copy of defaults
        if additional_ignore_patterns:
            current_scan_ignore_patterns.extend(p for p in additional_ignore_patterns if p not in current_scan_ignore_patterns)
        
        root_path = Path(root_path_str).resolve()
        if not root_path.is_dir():
            raise ValueError(f"Provided path '{root_path_str}' is not a valid directory.")

        tree_data_items = []
        for item in sorted(root_path.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
            # Pass the combined ignore patterns to _is_ignored
            if self._is_ignored(item, root_path, current_scan_ignore_patterns):
                continue
            item_info = {
                "name": item.name,
                "path": str(item.resolve()),
                "type": "file" if item.is_file() else "directory"
            }
            if item.is_dir():
                # Pass combined patterns to subtree generation as well
                item_info["children"] = self._generate_subtree(item, root_path, current_scan_ignore_patterns)
            tree_data_items.append(item_info)
        
        return tree_data_items


    def _generate_subtree(self, dir_path: Path, overall_root_path: Path, current_scan_ignore_patterns: list): # Modified signature
        """Helper for recursive subtree generation using current scan's ignore patterns."""
        children_data = []
        try:
            for item in sorted(dir_path.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
                if self._is_ignored(item, overall_root_path, current_scan_ignore_patterns): # Use passed patterns
                    continue
                item_info = {
                    "name": item.name,
                    "path": str(item.resolve()),
                    "type": "file" if item.is_file() else "directory"
                }
                if item.is_dir():
                    item_info["children"] = self._generate_subtree(item, overall_root_path, current_scan_ignore_patterns)
                children_data.append(item_info)
        except PermissionError:
            children_data.append({
                "name": f"[Access Denied]",
                "path": str(dir_path.resolve()),
                "type": "directory_error",
                "children": []
            })
        return children_data

    def format_tree_structure(self, tree_items: list, root_display_name: str) -> str:
        """
        Formats the scanned tree data (list of items within the root) into a string similar to 'tree' command.
        Args:
            tree_items: The list of dictionaries returned by generate_file_tree (items *within* the root).
            root_display_name: The name of the root directory to display.
        """
        output_lines = [root_display_name]

        def _recursive_format(items, prefix="", is_last_parent_item=False):
            for i, item_data in enumerate(items):
                is_last = (i == len(items) - 1)
                connector = "└── " if is_last else "├── "
                line = prefix + connector + item_data["name"]
                
                # Add a slash for directories for clarity
                if item_data["type"] == "directory" or item_data["type"] == "directory_error":
                    line += "/"
                
                output_lines.append(line)

                if "children" in item_data and item_data["children"]:
                    new_prefix = prefix + ("    " if is_last else "│   ")
                    _recursive_format(item_data["children"], new_prefix, is_last)
        
        _recursive_format(tree_items) # Start recursion with the items within the root
        return "\n".join(output_lines)

    def read_file_content(self, file_path_str: str) -> str:
        file_path = Path(file_path_str)
        try:
            if not file_path.is_file(): # Ensure it's a file before attempting to read
                return f"[Not a file: {file_path.name}]"
            if file_path.stat().st_size > self.max_file_size_bytes:
                return f"[File too large (>{config.MAX_FILE_SIZE_TO_READ_MB}MB): {file_path.name}]"
            try:
                with file_path.open('rb') as f_bin:
                    chunk = f_bin.read(1024)
                    if b'\0' in chunk:
                        return f"[Likely binary file, skipped: {file_path.name}]"
            except Exception:
                pass
            with file_path.open('r', encoding=config.DEFAULT_ENCODING, errors='ignore') as f:
                return f.read()
        except FileNotFoundError:
            return f"[File not found: {file_path.name}]"
        except PermissionError:
            return f"[Permission denied: {file_path.name}]"
        except Exception as e:
            return f"[Error reading {file_path.name}: {e}]"

    def consolidate_files_content(self, file_paths: list[str], root_dir_path_str: str = None) -> str:
        consolidated_texts = []
        try:
            root_dir = Path(root_dir_path_str).resolve() if root_dir_path_str else None
        except Exception:
            root_dir = None

        for file_path_str in file_paths:
            file_path_obj = Path(file_path_str).resolve()
            display_path = str(file_path_obj.name) # Default to just name
            if root_dir:
                try:
                    if file_path_obj.is_relative_to(root_dir): # Check if path is truly under root_dir
                        display_path = str(file_path_obj.relative_to(root_dir))
                    else: # If not, use absolute path
                        display_path = str(file_path_obj)
                except ValueError: # Should not happen if is_relative_to is used
                    display_path = str(file_path_obj)
            else: # No root_dir, use absolute path
                display_path = str(file_path_obj)

            content = self.read_file_content(str(file_path_obj))
            header = f"--- FILE: {display_path} ---"
            footer = f"--- END OF FILE: {display_path} ---"
            consolidated_texts.append(f"{header}\n{content}\n{footer}\n\n")
            
        return "".join(consolidated_texts)