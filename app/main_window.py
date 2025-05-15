# app/main_window.py
import tkinter as tk
from tkinter import ttk, PhotoImage, messagebox
from pathlib import Path
import os
from core import config as core_config

from .file_tree_view import FileTreeView
from .output_view import OutputView
from . import event_handlers 

from core.file_processor import FileProcessor 

class AppMainWindow(tk.Frame):
    IGNORE_FILE_NAME = ".file-consolidator-ignore"
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

        # NEW: Create the Refresh Directory button
        self.btn_refresh_dir = ttk.Button(
            self.controls_frame,
            text="Refresh Tree",
            command=lambda: event_handlers.handle_refresh_directory(self),
            state=tk.DISABLED # Start disabled until a directory is selected
        )

        self.btn_consolidate = ttk.Button(
            self.controls_frame,
            text="Consolidate Checked Files", # Updated button text
            command=lambda: event_handlers.handle_consolidate_files(self) 
        )

        self.btn_view_ignored = ttk.Button(
            self.controls_frame,
            text="View Ignored Patterns",
            command=self.show_ignored_patterns_window # Link to the new method
        )


        # --- Main Paned Window for resizable areas ---
        self.main_paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)

        # --- File Tree View (Left Pane) ---
        self.file_tree_frame = ttk.LabelFrame(self.main_paned_window, text="File Structure (Check/Uncheck)", padding="5")
        self.file_tree_view = FileTreeView(self.file_tree_frame, app_window=self) 
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
        self.btn_refresh_dir.pack(side=tk.LEFT, padx=(0, 5)) 
        self.btn_consolidate.pack(side=tk.LEFT)
        self.btn_view_ignored.pack(side=tk.LEFT, padx=(0, 5))


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

    def get_all_current_ignore_patterns(self) -> dict:
        """
        Returns a dictionary with 'default' and 'project_specific' ignore patterns.
        """
        return {
            "default": list(core_config.DEFAULT_IGNORE_PATTERNS), # Get from core.config
            "project_specific": sorted(list(self.project_specific_ignores))
        }

    def show_ignored_patterns_window(self):
        ignored_patterns_data = self.get_all_current_ignore_patterns()

        top = tk.Toplevel(self.master)
        top.title("Ignored Patterns")
        top.geometry("600x500") # Slightly larger for editing
        top.transient(self.master)
        # top.grab_set() # Let's make it non-modal for now to allow interaction with main window if needed,
                       # but be careful if main window actions affect this dialog's data.
                       # If strictly modal is preferred, uncomment grab_set().

        # --- Frame for Default Patterns (Read-Only) ---
        default_frame = ttk.LabelFrame(top, text="Default Ignore Patterns (Read-Only)", padding=5)
        default_frame.pack(padx=10, pady=(10,5), fill="x", expand=False)

        default_text_area = tk.Text(default_frame, wrap=tk.WORD, font=("TkDefaultFont", 10), height=8)
        default_scrollbar = ttk.Scrollbar(default_frame, orient='vertical', command=default_text_area.yview)
        default_text_area.configure(yscrollcommand=default_scrollbar.set)
        default_text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        default_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        if ignored_patterns_data["default"]:
            for pattern in ignored_patterns_data["default"]:
                default_text_area.insert(tk.END, f"{pattern}\n")
        else:
            default_text_area.insert(tk.END, "(None)\n")
        default_text_area.config(state=tk.DISABLED)

        # --- Frame for Project-Specific Patterns (Editable) ---
        project_frame = ttk.LabelFrame(top, text="Project-Specific Ignores (Editable)", padding=5)
        project_frame.pack(padx=10, pady=5, fill="both", expand=True)

        self.project_ignore_text_area = tk.Text(project_frame, wrap=tk.WORD, font=("TkDefaultFont", 10)) # Store as instance var
        project_scrollbar = ttk.Scrollbar(project_frame, orient='vertical', command=self.project_ignore_text_area.yview)
        self.project_ignore_text_area.configure(yscrollcommand=project_scrollbar.set)
        self.project_ignore_text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        project_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        if self.selected_root_dir:
            if ignored_patterns_data["project_specific"]:
                for pattern in ignored_patterns_data["project_specific"]:
                    self.project_ignore_text_area.insert(tk.END, f"{pattern}\n")
            else:
                self.project_ignore_text_area.insert(tk.END, "# Add project-specific patterns here, one per line.\n# Lines starting with # are comments.\n")
            self.project_ignore_text_area.config(state=tk.NORMAL)
        else:
            self.project_ignore_text_area.insert(tk.END, "(Select a project root directory first to edit specific ignores.)\n")
            self.project_ignore_text_area.config(state=tk.DISABLED)


        # --- Buttons Frame ---
        buttons_frame = ttk.Frame(top, padding=(0, 5, 0, 10))
        buttons_frame.pack(fill="x", side=tk.BOTTOM)

        def save_project_ignores_from_dialog():
            if not self.selected_root_dir:
                messagebox.showwarning("No Project", "Cannot save, no project directory selected.", parent=top)
                return

            new_patterns_text = self.project_ignore_text_area.get("1.0", tk.END)
            new_patterns_set = set()
            for line in new_patterns_text.splitlines():
                line = line.strip()
                if line and not line.startswith('#'):
                    new_patterns_set.add(line)
            
            self.project_specific_ignores = new_patterns_set # Update the set in AppMainWindow
            self.save_project_ignores() # Use existing save method
            
            messagebox.showinfo("Saved", f"Project-specific ignore patterns saved to\n{Path(self.selected_root_dir) / self.IGNORE_FILE_NAME}", parent=top)
            
            # Refresh the tree view in the main window
            if hasattr(event_handlers, 'handle_refresh_directory'):
                 event_handlers.handle_refresh_directory(self)
            top.destroy() # Close dialog after saving


        save_button = ttk.Button(buttons_frame, text="Save Project Ignores & Close", command=save_project_ignores_from_dialog)
        save_button.pack(side=tk.RIGHT, padx=5)
        if not self.selected_root_dir: # Disable save if no project selected
            save_button.config(state=tk.DISABLED)

        cancel_button = ttk.Button(buttons_frame, text="Cancel", command=top.destroy)
        cancel_button.pack(side=tk.RIGHT)

        top.protocol("WM_DELETE_WINDOW", top.destroy) # Handle window close button
        top.focus_set()