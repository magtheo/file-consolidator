# app/event_handlers.py
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
from core.file_processor import FileProcessor # Import the class
from core import config # To access default ignore patterns if needed

# No class needed here, just functions that will take the app_window instance.

def handle_select_directory(app_window): # app_window is an instance of AppMainWindow
    """Handles the 'Select Root Directory' button click."""
    directory = filedialog.askdirectory(mustexist=True, title="Select Project Root Directory")
    if directory:
        app_window.selected_root_dir = directory
        # Use configure() or config() to change Label text
        app_window.status_bar.config(text=f"Selected: {directory}")
        try:
            # Use app_window's file_processor instance
            tree_data = app_window.file_processor.generate_file_tree(directory)
            app_window.file_tree_view.populate_tree(tree_data)
            app_window.output_view.set_text("") # Clear previous output
        except ValueError as ve:
            messagebox.showerror("Error", f"Invalid directory selected: {ve}")
            app_window.status_bar.config(text=f"Error: Invalid directory.")
        except PermissionError as pe:
            messagebox.showerror("Permission Error", f"Cannot access directory or its contents: {pe}")
            app_window.status_bar.config(text=f"Error: Permission denied.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to scan directory: {e}")
            app_window.status_bar.config(text=f"Error: Failed to scan. {e}") # Include exception for debugging


def handle_consolidate_files(app_window): # app_window is an instance of AppMainWindow
    """Handles the 'Consolidate Selected Files' button click."""
    if not app_window.selected_root_dir:
        messagebox.showinfo("Info", "Please select a root directory first.")
        return

    selected_files = app_window.file_tree_view.get_selected_files()

    if not selected_files:
        messagebox.showinfo("Info", "No files selected in the tree. Click on files/folders to select them.")
        return

    try:
        # Use app_window's file_processor instance
        consolidated_text = app_window.file_processor.consolidate_files_content(
            selected_files,
            app_window.selected_root_dir # Pass root_dir for relative paths
        )
        app_window.output_view.set_text(consolidated_text)
        # Use configure() or config() to change Label text
        app_window.status_bar.config(text=f"Consolidated {len(selected_files)} file(s).")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to consolidate files: {e}")
        # Use configure() or config() to change Label text
        app_window.status_bar.config(text=f"Error: Consolidation failed. {e}") # Include exception for debugging