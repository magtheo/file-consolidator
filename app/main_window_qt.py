# app/main_window_qt.py (New or heavily modified file)
import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QStatusBar, QSplitter, QFrame, QLabel, QFileDialog, QMessageBox,
    QTextEdit, QDialog, QDialogButtonBox, QListWidget, QListWidgetItem
)
from PyQt6.QtGui import QIcon, QAction # For icons and menu actions
from PyQt6.QtCore import Qt, QDir
from pathlib import Path
import os

from core import config as core_config
from core.file_processor import FileProcessor
# from .file_tree_view_qt import FileTreeViewQt # New Qt file tree
# from .output_view_qt import OutputViewQt     # New Qt output view
# from .event_handlers_qt import connect_event_handlers # Or integrate handlers directly

class AppMainWindowQt(QMainWindow): # Inherit from QMainWindow for menus, toolbars, status bar
    IGNORE_FILE_NAME = ".file-consolidator-ignore"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("LLM Context Builder (Qt)")

        icon_path = Path(__file__).parent.parent / "assets" / "icon.png"
        if icon_path.is_file():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.setMinimumSize(700, 500)
        self.setGeometry(100, 100, 900, 700) # x, y, width, height

        self.selected_root_dir = None
        self.file_processor = FileProcessor()
        self.current_tree_data = None
        self.project_specific_ignores = set()

        self._create_widgets()
        self._layout_widgets()
        self._connect_signals() # For event handling

        # Load initial ignores or set up status
        self.status_bar.showMessage("Ready")

    def _create_widgets(self):
        # --- Central Widget (required for QMainWindow if not using dock widgets) ---
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # --- Top Controls ---
        self.btn_select_dir = QPushButton("Select Root Directory")
        self.btn_refresh_dir = QPushButton("Refresh Tree")
        self.btn_refresh_dir.setEnabled(False)
        self.btn_consolidate = QPushButton("Consolidate Checked Files")
        self.btn_view_ignored = QPushButton("View Ignored Patterns")

        # --- Main Splitter (replaces PanedWindow) ---
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # --- File Tree View (Left Pane) ---
        # Placeholder - this will be your FileTreeViewQt instance
        from .file_tree_view_qt import FileTreeViewQt # Import here to avoid circular dependency if in same file
        self.file_tree_view = FileTreeViewQt(app_window=self)
        # For QGroupBox like LabelFrame:
        file_tree_groupbox = QFrame() # Or QGroupBox("File Structure")
        file_tree_layout = QVBoxLayout(file_tree_groupbox)
        file_tree_layout.addWidget(QLabel("File Structure (Check/Uncheck)")) # Title if not QGroupBox
        file_tree_layout.addWidget(self.file_tree_view)
        self.main_splitter.addWidget(file_tree_groupbox)

        # --- Output View (Right Pane) ---
        # Placeholder - this will be your OutputViewQt instance
        from .output_view_qt import OutputViewQt # Import here
        self.output_view = OutputViewQt(app_window=self)
        output_groupbox = QFrame() # Or QGroupBox("Consolidated Output")
        output_layout = QVBoxLayout(output_groupbox)
        output_layout.addWidget(QLabel("Consolidated Output"))
        output_layout.addWidget(self.output_view)
        self.main_splitter.addWidget(output_groupbox)

        self.main_splitter.setStretchFactor(0, 1) # Initial proportion for file tree
        self.main_splitter.setStretchFactor(1, 2) # Initial proportion for output

        # --- Status Bar ---
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def _layout_widgets(self):
        # Overall layout for the central widget
        main_layout = QVBoxLayout(self.central_widget)

        # Controls layout
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(self.btn_select_dir)
        controls_layout.addWidget(self.btn_refresh_dir)
        controls_layout.addWidget(self.btn_consolidate)
        controls_layout.addWidget(self.btn_view_ignored)
        controls_layout.addStretch() # Pushes buttons to the left

        main_layout.addLayout(controls_layout)
        main_layout.addWidget(self.main_splitter) # Splitter will take up remaining space

    def _connect_signals(self):
        self.btn_select_dir.clicked.connect(self.handle_select_directory)
        self.btn_refresh_dir.clicked.connect(self.handle_refresh_directory)
        self.btn_consolidate.clicked.connect(self.handle_consolidate_files)
        self.btn_view_ignored.clicked.connect(self.show_ignored_patterns_window)
        # More connections as needed

    # --- Event Handler Methods (Ported from event_handlers.py) ---
    def handle_select_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Project Root Directory", self.selected_root_dir or QDir.homePath())
        if directory:
            self.selected_root_dir = directory
            self.current_tree_data = None
            self.status_bar.showMessage(f"Selected: {directory}. Loading ignores...")
            QApplication.processEvents() # Ensure UI updates

            self.load_project_ignores()

            self.status_bar.showMessage(f"Scanning: {directory}...")
            QApplication.processEvents()

            try:
                self.current_tree_data = self.file_processor.generate_file_tree(
                    directory,
                    additional_ignore_patterns=list(self.project_specific_ignores)
                )
                self.file_tree_view.populate_tree(self.current_tree_data, preserve_state=False)
                self.output_view.set_text("")
                self.status_bar.showMessage(f"Scanned: {directory}")
                self.btn_refresh_dir.setEnabled(True)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to scan directory: {e}")
                self.status_bar.showMessage(f"Error: Failed to scan. {e}")
                self.btn_refresh_dir.setEnabled(False)

    def handle_refresh_directory(self):
        if not self.selected_root_dir:
            QMessageBox.information(self, "Info", "No directory selected to refresh.")
            return

        self.status_bar.showMessage(f"Refreshing: {self.selected_root_dir}...")
        QApplication.processEvents()

        try:
            self.current_tree_data = self.file_processor.generate_file_tree(
                self.selected_root_dir,
                additional_ignore_patterns=list(self.project_specific_ignores)
            )
            self.file_tree_view.populate_tree(self.current_tree_data, preserve_state=True)
            self.status_bar.showMessage(f"Refreshed: {self.selected_root_dir}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh directory: {e}")
            self.status_bar.showMessage(f"Error: Refresh failed. {e}")

    def handle_consolidate_files(self):
        if not self.selected_root_dir:
            QMessageBox.information(self, "Info", "Please select a root directory first.")
            return
        checked_files = self.file_tree_view.get_checked_files()
        if not checked_files:
            QMessageBox.information(self, "Info", "No files checked in the tree.")
            return
        try:
            output_parts = [f"Current Root Directory: {self.selected_root_dir}\n"]
            if self.current_tree_data is not None:
                root_dir_name = Path(self.selected_root_dir).name
                formatted_tree = self.file_processor.format_tree_structure(
                    self.current_tree_data, root_dir_name
                )
                output_parts.append(f"File Structure:\n{formatted_tree}\n")
            else:
                output_parts.append("File Structure: (Not available - rescan directory if needed)\n")
            output_parts.append("Selected File Contents:\n" + "="*30 + "\n")
            consolidated_content_str = self.file_processor.consolidate_files_content(
                checked_files, self.selected_root_dir
            )
            output_parts.append(consolidated_content_str)
            self.output_view.set_text("".join(output_parts))
            self.status_bar.showMessage(f"Consolidated {len(checked_files)} file(s).")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to consolidate files: {e}")
            self.status_bar.showMessage(f"Error: Consolidation failed. {e}")

    # ... (load_project_ignores, save_project_ignores, get_relative_path_for_item,
    #      ignore_folder_and_refresh, unignore_folder_and_refresh, get_all_current_ignore_patterns
    #      methods can be ported with minor changes for UI feedback using QMessageBox) ...

    def show_ignored_patterns_window(self):
        # This will become a QDialog
        dialog = IgnoredPatternsDialog(self.get_all_current_ignore_patterns(), self.selected_root_dir, self)
        if dialog.exec(): # exec() shows the dialog modally
            new_patterns_set = dialog.get_project_specific_ignores()
            if new_patterns_set is not None: # Check if user didn't cancel or an error occurred
                self.project_specific_ignores = new_patterns_set
                self.save_project_ignores()
                QMessageBox.information(self, "Saved", f"Project-specific ignore patterns saved to\n{Path(self.selected_root_dir) / self.IGNORE_FILE_NAME}")
                self.handle_refresh_directory() # Refresh tree after saving

    # Port these methods (minor UI changes for QMessageBox)
    def load_project_ignores(self): # All logic is fine, just change messagebox
         self.project_specific_ignores.clear()
         if not self.selected_root_dir: return

         ignore_file_path = Path(self.selected_root_dir) / self.IGNORE_FILE_NAME
         if ignore_file_path.is_file():
             try:
                 with ignore_file_path.open('r', encoding='utf-8') as f:
                     for line in f:
                         line = line.strip()
                         if line and not line.startswith('#'):
                             self.project_specific_ignores.add(line)
                 print(f"Loaded {len(self.project_specific_ignores)} patterns from {ignore_file_path}")
             except Exception as e:
                 print(f"Error loading ignore file {ignore_file_path}: {e}")
                 QMessageBox.warning(self, "Ignore File Error", f"Could not load {self.IGNORE_FILE_NAME}:\n{e}")

    def save_project_ignores(self): # All logic is fine, just change messagebox
         if not self.selected_root_dir: return
         ignore_file_path = Path(self.selected_root_dir) / self.IGNORE_FILE_NAME
         try:
             with ignore_file_path.open('w', encoding='utf-8') as f:
                 f.write(f"# Project-specific ignore patterns for {self.windowTitle()}\n") # Use self.windowTitle()
                 f.write("# One pattern (relative path from root) per line.\n")
                 for pattern in sorted(list(self.project_specific_ignores)):
                     f.write(f"{pattern}\n")
             print(f"Saved {len(self.project_specific_ignores)} patterns to {ignore_file_path}")
         except Exception as e:
             print(f"Error saving ignore file {ignore_file_path}: {e}")
             QMessageBox.critical(self, "Ignore File Error", f"Could not save {self.IGNORE_FILE_NAME}:\n{e}")

    def get_relative_path_for_item(self, full_item_path: str) -> str | None:
        # This method remains largely the same, using os.path.relpath
        if not self.selected_root_dir: return None
        try:
            # Path.is_relative_to is good for Python 3.9+
            if hasattr(Path, 'is_relative_to'):
                root_p = Path(self.selected_root_dir).resolve()
                item_p = Path(full_item_path).resolve()
                if item_p.is_relative_to(root_p):
                    return str(item_p.relative_to(root_p))
                return None # Not relative
            else: # Fallback for older Python
                return os.path.relpath(full_item_path, self.selected_root_dir)
        except ValueError:
            return None

    def ignore_folder_and_refresh(self, relative_folder_path: str):
        if relative_folder_path and relative_folder_path not in self.project_specific_ignores:
            self.project_specific_ignores.add(relative_folder_path)
            self.save_project_ignores()
            self.handle_refresh_directory()

    def unignore_folder_and_refresh(self, relative_folder_path: str):
        if relative_folder_path and relative_folder_path in self.project_specific_ignores:
            self.project_specific_ignores.remove(relative_folder_path)
            self.save_project_ignores()
            self.handle_refresh_directory()

    def get_all_current_ignore_patterns(self) -> dict:
        return {
            "default": list(core_config.DEFAULT_IGNORE_PATTERNS),
            "project_specific": sorted(list(self.project_specific_ignores))
        }

# --- Ignored Patterns Dialog (replaces Toplevel) ---
class IgnoredPatternsDialog(QDialog):
    def __init__(self, ignored_data, selected_root_dir, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ignored Patterns")
        self.setMinimumSize(600, 500)
        self.selected_root_dir = selected_root_dir # Store for enabling/disabling save

        layout = QVBoxLayout(self)

        # Default Patterns (Read-Only)
        default_group = QFrame() # Or QGroupBox("Default Ignore Patterns (Read-Only)")
        default_group_layout = QVBoxLayout(default_group)
        default_group_layout.addWidget(QLabel("Default Ignore Patterns (Read-Only)"))
        self.default_text_area = QTextEdit()
        self.default_text_area.setReadOnly(True)
        if ignored_data["default"]:
            self.default_text_area.setPlainText("\n".join(ignored_data["default"]))
        else:
            self.default_text_area.setPlainText("(None)")
        default_group_layout.addWidget(self.default_text_area)
        layout.addWidget(default_group)

        # Project-Specific Patterns (Editable)
        project_group = QFrame() # Or QGroupBox("Project-Specific Ignores (Editable)")
        project_group_layout = QVBoxLayout(project_group)
        project_group_layout.addWidget(QLabel("Project-Specific Ignores (Editable)"))
        self.project_ignore_text_area = QTextEdit()
        if self.selected_root_dir:
            if ignored_data["project_specific"]:
                self.project_ignore_text_area.setPlainText("\n".join(ignored_data["project_specific"]))
            else:
                self.project_ignore_text_area.setPlainText("# Add project-specific patterns here, one per line.\n# Lines starting with # are comments.\n")
        else:
            self.project_ignore_text_area.setPlainText("(Select a project root directory first to edit specific ignores.)")
            self.project_ignore_text_area.setEnabled(False)
        project_group_layout.addWidget(self.project_ignore_text_area)
        layout.addWidget(project_group)


        # Dialog Buttons (Save & Close, Cancel)
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept) # Default accept action
        self.button_box.rejected.connect(self.reject)

        save_button = self.button_box.button(QDialogButtonBox.StandardButton.Save)
        save_button.setText("Save Project Ignores & Close")
        if not self.selected_root_dir:
            save_button.setEnabled(False)

        layout.addWidget(self.button_box)

    def get_project_specific_ignores(self):
        if not self.selected_root_dir:
            return None # Indicate no save should happen or pass original set

        new_patterns_text = self.project_ignore_text_area.toPlainText()
        new_patterns_set = set()
        for line in new_patterns_text.splitlines():
            line = line.strip()
            if line and not line.startswith('#'):
                new_patterns_set.add(line)
        return new_patterns_set