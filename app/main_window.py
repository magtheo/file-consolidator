# app/main_window.py
import tkinter as tk
from tkinter import ttk, PhotoImage
from pathlib import Path

from .file_tree_view import FileTreeView
from .output_view import OutputView
from . import event_handlers 

from core.file_processor import FileProcessor 

class AppMainWindow(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title("LLM Context Builder")
        
        icon_path = Path(__file__).parent.parent / "assets" / "icon.png"
        try:
            if icon_path.is_file():
                app_icon = PhotoImage(file=str(icon_path))
                self.master.iconphoto(True, app_icon)
        except tk.TclError:
            print(f"Could not load icon {icon_path}. Using default.")

        self.master.minsize(700, 500)
        self.master.geometry("900x700") 

        self.selected_root_dir = None
        self.file_processor = FileProcessor()
        self.current_tree_data = None 
        self.project_specific_ignores = set()

        self._create_widgets()
        self._layout_widgets()

        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(0, weight=1)
        self.grid(sticky='nsew')

    # ... rest of the AppMainWindow class remains the same ...
    def _create_widgets(self):
        # --- Top Controls Frame ---
        self.controls_frame = ttk.Frame(self, padding="10")
        
        self.btn_select_dir = ttk.Button(
            self.controls_frame,
            text="Select Root Directory",
            command=lambda: event_handlers.handle_select_directory(self) 
        )
        self.btn_consolidate = ttk.Button(
            self.controls_frame,
            text="Consolidate Checked Files", # Updated button text
            command=lambda: event_handlers.handle_consolidate_files(self) 
        )

        # --- Main Paned Window for resizable areas ---
        self.main_paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)

        # --- File Tree View (Left Pane) ---
        self.file_tree_frame = ttk.LabelFrame(self.main_paned_window, text="File Structure (Click to Check/Uncheck)", padding="5") # Updated label
        self.file_tree_view = FileTreeView(self.file_tree_frame)
        self.main_paned_window.add(self.file_tree_frame, weight=1) 

        # --- Output View (Right Pane) ---
        self.output_frame = ttk.LabelFrame(self.main_paned_window, text="Consolidated Output", padding="5")
        self.output_view = OutputView(self.output_frame)
        self.main_paned_window.add(self.output_frame, weight=2)

        # --- Status Bar ---
        self.status_bar = ttk.Label(self, text="Ready", anchor='w', relief=tk.SUNKEN, padding="2 5")


    def _layout_widgets(self):
        self.grid_rowconfigure(0, weight=0) 
        self.grid_rowconfigure(1, weight=1) 
        self.grid_rowconfigure(2, weight=0) 
        self.grid_columnconfigure(0, weight=1)

        self.controls_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.btn_select_dir.pack(side=tk.LEFT, padx=(0, 5))
        self.btn_consolidate.pack(side=tk.LEFT)

        self.main_paned_window.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0,5))
        self.file_tree_view.pack(fill=tk.BOTH, expand=True)
        self.output_view.pack(fill=tk.BOTH, expand=True)
        
        self.status_bar.grid(row=2, column=0, sticky="ew")

    def load_project_ignores(self):
        self.project_specific_ignores.clear()
        if not self.selected_root_dir: return
        
        ignore_file_path = Path(self.selected_root_dir) / self.IGNORE_FILE_NAME
        if ignore_file_path.is_file():
            try:
                with ignore_file_path.open('r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'): # Ignore empty lines and comments
                            self.project_specific_ignores.add(line)
                print(f"Loaded {len(self.project_specific_ignores)} patterns from {ignore_file_path}")
            except Exception as e:
                print(f"Error loading ignore file {ignore_file_path}: {e}")
                messagebox.showwarning("Ignore File Error", f"Could not load {self.IGNORE_FILE_NAME}:\n{e}")

    def save_project_ignores(self):
        if not self.selected_root_dir: return
        ignore_file_path = Path(self.selected_root_dir) / self.IGNORE_FILE_NAME
        try:
            with ignore_file_path.open('w', encoding='utf-8') as f:
                f.write(f"# Project-specific ignore patterns for {self.master.title()}\n")
                f.write("# One pattern (relative path from root) per line.\n")
                for pattern in sorted(list(self.project_specific_ignores)):
                    f.write(f"{pattern}\n")
            print(f"Saved {len(self.project_specific_ignores)} patterns to {ignore_file_path}")
        except Exception as e:
            print(f"Error saving ignore file {ignore_file_path}: {e}")
            messagebox.showerror("Ignore File Error", f"Could not save {self.IGNORE_FILE_NAME}:\n{e}")

    def get_relative_path_for_item(self, full_item_path: str) -> str | None:
        """Converts a full path to a path relative to selected_root_dir."""
        if not self.selected_root_dir: return None
        try:
            root_p = Path(self.selected_root_dir).resolve()
            item_p = Path(full_item_path).resolve()
            if item_p.is_relative_to(root_p): # Requires Python 3.9+
                 return str(item_p.relative_to(root_p))
            # Fallback for older Python or if not strictly relative (e.g. symlink target outside)
            # This part might need adjustment based on how symlinks should be treated for ignoring
            # For simplicity, if it's not directly relative, we might not be able to reliably make it a relative ignore
            return None 
        except (ValueError, AttributeError): # AttributeError for older is_relative_to
             # Fallback for older python:
            try:
                return os.path.relpath(full_item_path, self.selected_root_dir)
            except ValueError:
                return None # Cannot make relative

    def ignore_folder_and_refresh(self, relative_folder_path: str):
        if relative_folder_path and relative_folder_path not in self.project_specific_ignores:
            self.project_specific_ignores.add(relative_folder_path)
            self.save_project_ignores()
            event_handlers.handle_refresh_directory(self) # Trigger refresh

    def unignore_folder_and_refresh(self, relative_folder_path: str):
        if relative_folder_path and relative_folder_path in self.project_specific_ignores:
            self.project_specific_ignores.remove(relative_folder_path)
            self.save_project_ignores()
            event_handlers.handle_refresh_directory(self) # Trigger refresh