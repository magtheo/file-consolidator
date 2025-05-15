# app/event_handlers.py
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
from pathlib import Path # For getting root directory name
# from core.file_processor import FileProcessor # Already available via app_window
# from core import config

def handle_select_directory(app_window):
    directory = filedialog.askdirectory(mustexist=True, title="Select Project Root Directory")
    if directory:
        app_window.selected_root_dir = directory
        app_window.current_tree_data = None 
        app_window.status_bar.config(text=f"Selected: {directory}. Loading ignores...")
        app_window.update_idletasks()

        app_window.load_project_ignores() # NEW: Load project-specific ignores

        app_window.status_bar.config(text=f"Scanning: {directory}...")
        app_window.update_idletasks() # Ensure status bar updates

        try:
            # Pass project specific ignores to file_processor
            app_window.current_tree_data = app_window.file_processor.generate_file_tree(
                directory,
                additional_ignore_patterns=list(app_window.project_specific_ignores)
            )
            app_window.file_tree_view.populate_tree(app_window.current_tree_data, preserve_state=False) # Fresh populate
            app_window.output_view.set_text("") 
            app_window.status_bar.config(text=f"Scanned: {directory}")
            app_window.btn_refresh_dir.config(state=tk.NORMAL) # Enable refresh button
        except Exception as e: # Catch-all for safety
            messagebox.showerror("Error", f"Failed to scan directory: {e}")
            app_window.status_bar.config(text=f"Error: Failed to scan. {e}")
            app_window.btn_refresh_dir.config(state=tk.DISABLED)


def handle_refresh_directory(app_window): # NEW HANDLER
    if not app_window.selected_root_dir:
        messagebox.showinfo("Info", "No directory selected to refresh.")
        return

    app_window.status_bar.config(text=f"Refreshing: {app_window.selected_root_dir}...")
    app_window.update_idletasks()
    
    # No need to reload ignores here, they are already in app_window.project_specific_ignores
    # unless you want a mechanism to detect external changes to .file-consolidator-ignore
    # For now, assume they are managed by the app's ignore/unignore actions.
    # If desired, add app_window.load_project_ignores() here too.

    try:
        app_window.current_tree_data = app_window.file_processor.generate_file_tree(
            app_window.selected_root_dir,
            additional_ignore_patterns=list(app_window.project_specific_ignores)
        )
        # Preserve state during refresh
        app_window.file_tree_view.populate_tree(app_window.current_tree_data, preserve_state=True)
        app_window.status_bar.config(text=f"Refreshed: {app_window.selected_root_dir}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to refresh directory: {e}")
        app_window.status_bar.config(text=f"Error: Refresh failed. {e}")


def handle_consolidate_files(app_window):
    if not app_window.selected_root_dir:
        messagebox.showinfo("Info", "Please select a root directory first.")
        return
    checked_files = app_window.file_tree_view.get_checked_files()
    if not checked_files:
        messagebox.showinfo("Info", "No files checked in the tree.")
        return
    try:
        output_parts = [f"Current Root Directory: {app_window.selected_root_dir}\n"]
        if hasattr(app_window, 'current_tree_data') and app_window.current_tree_data is not None:
            root_dir_name = Path(app_window.selected_root_dir).name
            formatted_tree = app_window.file_processor.format_tree_structure(
                app_window.current_tree_data, root_dir_name
            )
            output_parts.append(f"File Structure:\n{formatted_tree}\n")
        else:
            output_parts.append("File Structure: (Not available - rescan directory if needed)\n")
        output_parts.append("Selected File Contents:\n" + "="*30 + "\n")
        consolidated_content_str = app_window.file_processor.consolidate_files_content(
            checked_files, app_window.selected_root_dir
        )
        output_parts.append(consolidated_content_str)
        app_window.output_view.set_text("".join(output_parts))
        app_window.status_bar.config(text=f"Consolidated {len(checked_files)} file(s).")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to consolidate files: {e}")
        app_window.status_bar.config(text=f"Error: Consolidation failed. {e}")