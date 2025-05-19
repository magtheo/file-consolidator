# app/output_view_qt.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QLabel, QMessageBox, QApplication, QHBoxLayout
from PyQt6.QtGui import QDrag, QCursor
from PyQt6.QtCore import Qt, QMimeData, QUrl
import tempfile
import os
from utils import clipboard_helper # Can still use this

class OutputViewQt(QWidget):
    def __init__(self, parent=None, app_window=None):
        super().__init__(parent)
        self.app_window = app_window # Main window reference if needed

        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setFontFamily("Courier New") # Or QFont("Courier New", 10)

        self.btn_copy = QPushButton("Copy to Clipboard")
        self.drag_handle_label = QLabel("Drag as File")
        self.drag_handle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drag_handle_label.setStyleSheet("QLabel { border: 1px solid gray; padding: 5px; }") # Basic styling
        self.drag_handle_label.setCursor(QCursor(Qt.CursorShape.OpenHandCursor)) # Indicate draggable

        # --- DND Setup ---
        self.drag_handle_label.mousePressEvent = self._drag_mouse_press
        self.drag_handle_label.mouseMoveEvent = self._drag_mouse_move
        self._drag_start_position = None
        self._temp_drag_file_path = None

        # --- LAYOUT ---
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.text_area)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.btn_copy)
        buttons_layout.addWidget(self.drag_handle_label)
        main_layout.addLayout(buttons_layout)
        main_layout.setContentsMargins(0,0,0,0)


        # --- CONNECTIONS ---
        self.btn_copy.clicked.connect(self.copy_content)

    def set_text(self, content: str):
        self.text_area.setPlainText(content)

    def get_text(self) -> str:
        return self.text_area.toPlainText()

    def copy_content(self):
        text_to_copy = self.get_text()
        if text_to_copy:
            clipboard_helper.copy_to_clipboard(text_to_copy) # Or use QApplication.clipboard()
            original_text = self.btn_copy.text()
            self.btn_copy.setText("Copied!")
            # Use QTimer for delayed reset if desired
            self.btn_copy.repaint() # Ensure text update is visible
            QApplication.processEvents()
            self.app_window.status_bar.showMessage("Content copied to clipboard.", 2000) # Show for 2s
            # Reset button text after a delay (e.g., using QTimer)
            # For simplicity, you might just leave it or reset on next action
        else:
            QMessageBox.information(self, "Clipboard", "Nothing to copy.")

    # --- Drag and Drop Implementation ---
    def _prepare_temp_file_for_drag(self) -> bool:
        content = self.get_text()
        if not content:
            QMessageBox.information(self, "Drag File", "Output is empty, nothing to drag.")
            return False
        self._cleanup_temp_drag_file()
        try:
            fd, self._temp_drag_file_path = tempfile.mkstemp(suffix=".txt", prefix="consolidated_output_", text=False)
            with os.fdopen(fd, "wb") as f:
                f.write(content.encode('utf-8'))
            return True
        except Exception as e:
            QMessageBox.critical(self, "Drag File Error", f"Could not create temporary file for dragging: {e}")
            self._temp_drag_file_path = None
            return False

    def _cleanup_temp_drag_file(self):
        if self._temp_drag_file_path:
            path_to_remove = self._temp_drag_file_path
            self._temp_drag_file_path = None
            try:
                if os.path.exists(path_to_remove):
                    os.remove(path_to_remove)
            except Exception as e:
                print(f"Error cleaning up temporary drag file {path_to_remove}: {e}")

    def _drag_mouse_press(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._prepare_temp_file_for_drag():
                self._drag_start_position = event.pos()
                self.drag_handle_label.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
            else:
                self._drag_start_position = None # Preparation failed
        # super().mousePressEvent(event) # Call if QLabel itself needs to handle press

    def _drag_mouse_move(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return 
        if self._drag_start_position is None: # Drag not initiated or temp file failed
            return 

        # Check if mouse has moved enough to start a drag
        if (event.pos() - self._drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return

        print(f"Starting drag for: {self._temp_drag_file_path}")
        if self._temp_drag_file_path and os.path.exists(self._temp_drag_file_path):
            print(f"Temporary file {self._temp_drag_file_path} exists. Size: {os.path.getsize(self._temp_drag_file_path)} bytes.")
            # For debugging, you can print a snippet of the content:
            # with open(self._temp_drag_file_path, 'r', encoding='utf-8') as f_debug:
            #     print(f"Temp file content (first 50 chars): {f_debug.read(50)}")
        else:
            print(f"Temporary file {self._temp_drag_file_path} does NOT exist or path is None before drag.exec!")
            # This would be a problem, ensure _prepare_temp_file_for_drag was successful
            self.drag_handle_label.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
            self._drag_start_position = None
            return


        drag = QDrag(self)
        mime_data = QMimeData()
        urls = [QUrl.fromLocalFile(self._temp_drag_file_path)]
        mime_data.setUrls(urls)
        drag.setMimeData(mime_data)
        
        # **** MODIFICATION: Only offer CopyAction ****
        # The target application decides how to handle it (e.g., it might still choose to move if it's on the same filesystem)
        # but we are signaling our intent is for a copy from this temp source.
        action = drag.exec(Qt.DropAction.CopyAction) # Only allow CopyAction from our side

        self.drag_handle_label.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        self._drag_start_position = None 
        
        if action == Qt.DropAction.CopyAction:
            print(f"Drag action was accepted as COPY for {self._temp_drag_file_path}. Target made a copy.")
            # Temp file will be cleaned up by next drag or on destroy.
        elif action == Qt.DropAction.MoveAction:
            # This case should be less likely if we only offer CopyAction, but some targets might still report Move.
            print(f"Drag action was accepted as MOVE for {self._temp_drag_file_path}. Target now owns it.")
            self._temp_drag_file_path = None # Prevent our cleanup if target moved it
        elif action == Qt.DropAction.LinkAction:
            print(f"Drag action was accepted as LINK for {self._temp_drag_file_path}.")
        else: # Qt.DropAction.IgnoreAction or other
            print(f"Drag action was IGNORED or failed (action: {action}) for {self._temp_drag_file_path}. Will be cleaned up later.")
        
        # The temporary file is intentionally NOT cleaned up here immediately.
        # It will be cleaned by _prepare_temp_file_for_drag() on the next drag attempt,
        # or by destroyEvent() when the widget is destroyed. This gives the target
        # application more time to access the file.


    def destroyEvent(self, event): # QWidget's equivalent of __del__ or Tk's destroy
        self._cleanup_temp_drag_file()
        super().destroyEvent(event)