# app/file_tree_view_qt.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QMenu, QAbstractItemView
)
from PyQt6.QtGui import QIcon, QFont, QAction, QCursor
from PyQt6.QtCore import Qt, QSize, QEvent
from pathlib import Path

class FileTreeViewQt(QWidget):
    # Qt has built-in icons for files/folders, or you can load custom ones
    # For simplicity, we'll use some standard Qt icons first
    # Or load your custom ones:
    # self.file_icon = QIcon(str(Path(__file__).parent.parent / "assets/file.png"))
    # self.folder_icon = QIcon(str(Path(__file__).parent.parent / "assets/folder.png"))
    # self.folder_open_icon = QIcon(str(Path(__file__).parent.parent / "assets/folder-open.png"))

    def __init__(self, parent=None, app_window=None):
        super().__init__(parent)
        self.app_window = app_window # To call back to main window for ignore/unignore

        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabel("Name") # Only one column header shown
        self.tree_widget.setColumnCount(1) # We'll store fullpath and type in item data

        # --- Enable Multi-Selection ---
        self.tree_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        # --- Install Event Filter for Key Presses on Tree Widget ---
        self.tree_widget.installEventFilter(self)

        # Item data storage (QTreeWidgetItem can store custom data)
        # self.tree_item_data remains conceptually similar but managed via QTreeWidgetItem.setData

        # Icons
        self.file_icon = self.style().standardIcon(getattr(QWidget().style(), 'SP_FileIcon', QWidget().style().StandardPixmap.SP_FileIcon))
        self.folder_icon = self.style().standardIcon(getattr(QWidget().style(), 'SP_DirIcon', QWidget().style().StandardPixmap.SP_DirIcon))
        self.folder_open_icon = self.style().standardIcon(getattr(QWidget().style(), 'SP_DirOpenIcon', QWidget().style().StandardPixmap.SP_DirOpenIcon))
        self.error_icon = self.style().standardIcon(getattr(QWidget().style(), 'SP_MessageBoxCritical', QWidget().style().StandardPixmap.SP_MessageBoxCritical))


        # --- LAYOUT ---
        layout = QVBoxLayout(self)
        layout.addWidget(self.tree_widget)
        layout.setContentsMargins(0,0,0,0) # Remove margins if it's inside a groupbox

        # --- EVENT BINDINGS ---
        # self.tree_widget.itemClicked.connect(self._on_item_click)
        self.tree_widget.itemChanged.connect(self._on_item_changed_propagator)
        self.tree_widget.itemExpanded.connect(self._on_item_expanded)
        self.tree_widget.itemCollapsed.connect(self._on_item_collapsed)

        # Context Menu
        self.tree_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self._on_item_right_click)

        self._is_programmatic_change = False

    def _create_tree_item(self, item_data, parent_qt_item=None):
        if parent_qt_item:
            qt_item = QTreeWidgetItem(parent_qt_item)
        else:
            qt_item = QTreeWidgetItem(self.tree_widget) # Add to root

        qt_item.setText(0, item_data['name'])
        qt_item.setData(0, Qt.ItemDataRole.UserRole, item_data) # Store full data dict

        # Checkbox
        qt_item.setFlags(qt_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        qt_item.setCheckState(0, Qt.CheckState.Unchecked) # Default to unchecked

        # Icon
        item_type = item_data['type']
        if item_type == 'file':
            qt_item.setIcon(0, self.file_icon)
        elif item_type == 'directory':
            qt_item.setIcon(0, self.folder_icon) # Closed by default
        elif item_type == 'directory_error':
            qt_item.setIcon(0, self.error_icon)
            qt_item.setText(0, f"[Err] {item_data['name']}")


        if item_type == 'directory' and item_data.get("children"):
            for child_data in item_data["children"]:
                self._create_tree_item(child_data, qt_item)
        return qt_item

    def _on_item_expanded(self, item):
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        if item_data and item_data['type'] == 'directory':
            item.setIcon(0, self.folder_open_icon)

    def _on_item_collapsed(self, item):
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        if item_data and item_data['type'] == 'directory':
            item.setIcon(0, self.folder_icon)

    def _on_item_changed_propagator(self, item: QTreeWidgetItem, column: int):
        """
        Handles item check state changes and propagates them to children.
        Prevents recursion if the change was made programmatically by this propagation logic.
        """
        if self._is_programmatic_change: 
            return

        if column == 0: 
            self._is_programmatic_change = True 
            try:
                new_state = item.checkState(0)
                # Propagate to children by recursively calling _set_check_state_recursive
                # which handles the actual check state setting and further recursion.
                for i in range(item.childCount()):
                    child = item.child(i)
                    self._set_check_state_recursive(child, new_state)
            finally:
                self._is_programmatic_change = False 

    def _set_check_state_recursive(self, item: QTreeWidgetItem, state: Qt.CheckState):
        """
        Sets the check state for the given item. If the state changes, itemChanged will fire.
        Then, recursively calls itself for all children of this item.
        The _is_programmatic_change flag in _on_item_changed_propagator prevents infinite loops.
        """
        if item.checkState(0) != state:
            item.setCheckState(0, state) # This will trigger _on_item_changed_propagator

        # After this item's state is set (and its itemChanged signal potentially handled),
        # proceed to its children.
        for i in range(item.childCount()):
            self._set_check_state_recursive(item.child(i), state)



    def _on_item_right_click(self, position):
        item = self.tree_widget.itemAt(position)
        if not item:
            return

        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not item_data:
            return

        menu = QMenu()
        relative_path = None
        if 'path' in item_data and self.app_window and self.app_window.selected_root_dir:
            relative_path = self.app_window.get_relative_path_for_item(item_data['path'])

        if item_data['type'] == 'directory' and relative_path:
            is_ignored = relative_path in self.app_window.project_specific_ignores
            if is_ignored:
                action = QAction(f"Unignore '{item_data['name']}'", self)
                action.triggered.connect(lambda checked=False, p=relative_path: self.app_window.unignore_folder_and_refresh(p))
                menu.addAction(action)
            else:
                action = QAction(f"Ignore '{item_data['name']}'", self)
                action.triggered.connect(lambda checked=False, p=relative_path: self.app_window.ignore_folder_and_refresh(p))
                menu.addAction(action)
            menu.addSeparator()

        expand_action = QAction("Expand All", self)
        expand_action.triggered.connect(lambda: self._expand_all_from_node(item))
        menu.addAction(expand_action)

        collapse_action = QAction("Collapse All", self)
        collapse_action.triggered.connect(lambda: self._collapse_all_from_node(item))
        menu.addAction(collapse_action)

        if not menu.isEmpty():
            menu.exec(self.tree_widget.mapToGlobal(position))

    # --- Event Filter for Spacebar ---
    def eventFilter(self, obj, event: QEvent):
        if obj is self.tree_widget and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Space: # Ensure Qt is imported from PyQt6.QtCore
                selected_items = self.tree_widget.selectedItems()
                if selected_items:
                    # Determine target state: if ANY selected item is unchecked, target is CHECKED.
                    # Else (all selected are checked), target is UNCHECKED.
                    target_state = Qt.CheckState.Unchecked # Default
                    for item in selected_items:
                        if item.checkState(0) == Qt.CheckState.Unchecked:
                            target_state = Qt.CheckState.Checked
                            break
                    
                    # Apply the target state to all selected items.
                    # Each call to setCheckState will trigger _on_item_changed_propagator,
                    # which will then correctly propagate to children using its own
                    # _is_programmatic_change flag logic.
                    for item in selected_items:
                        if item.checkState(0) != target_state:
                            item.setCheckState(0, target_state)
                    return True # Event handled
        return super().eventFilter(obj, event) # Pass on other events to the base class
        

    def populate_tree(self, directory_data_list, preserve_state: bool = False):
        # Store state (checked items by path, expanded items by path)
        previously_checked_paths = set()
        previously_expanded_paths = set()

        if preserve_state:
            root = self.tree_widget.invisibleRootItem()
            for i in range(root.childCount()):
                self._collect_state_recursive(root.child(i), previously_checked_paths, previously_expanded_paths)

        self.tree_widget.clear()

        if directory_data_list:
            for item_data in directory_data_list:
                self._create_tree_item(item_data) # Adds to tree_widget directly

        if preserve_state:
            root = self.tree_widget.invisibleRootItem()
            for i in range(root.childCount()):
                self._restore_state_recursive(root.child(i), previously_checked_paths, previously_expanded_paths)


    def _collect_state_recursive(self, item, checked_paths, expanded_paths):
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        if item_data and 'path' in item_data:
            if item.checkState(0) == Qt.CheckState.Checked:
                checked_paths.add(item_data['path'])
            if item.isExpanded() and item_data['type'] in ('directory', 'directory_error'):
                expanded_paths.add(item_data['path'])

        for i in range(item.childCount()):
            self._collect_state_recursive(item.child(i), checked_paths, expanded_paths)

    def _restore_state_recursive(self, item, checked_paths, expanded_paths):
        self._is_programmatic_change = True # Set flag before programmatic changes
        try:
            item_data = item.data(0, Qt.ItemDataRole.UserRole)
            if item_data and 'path' in item_data:
                if item_data['path'] in checked_paths:
                    if item.checkState(0) != Qt.CheckState.Checked:
                         item.setCheckState(0, Qt.CheckState.Checked)
                else:
                    if item.checkState(0) != Qt.CheckState.Unchecked:
                        item.setCheckState(0, Qt.CheckState.Unchecked)

                if item_data['path'] in expanded_paths and item_data['type'] in ('directory', 'directory_error'):
                    item.setExpanded(True)
                    if item_data['type'] == 'directory': item.setIcon(0, self.folder_open_icon)

            for i in range(item.childCount()):
                self._restore_state_recursive(item.child(i), checked_paths, expanded_paths)
        finally:
            self._is_programmatic_change = False # Reset flag


    def get_checked_files(self) -> list[str]:
        checked_files = []
        root = self.tree_widget.invisibleRootItem()
        for i in range(root.childCount()):
            self._collect_checked_files_recursive(root.child(i), checked_files)
        return sorted(list(set(checked_files))) # set for uniqueness

    def _collect_checked_files_recursive(self, item, checked_list):
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        if item_data and item_data['type'] == 'file' and item.checkState(0) == Qt.CheckState.Checked:
            checked_list.append(item_data['path'])
        for i in range(item.childCount()):
            self._collect_checked_files_recursive(item.child(i), checked_list)

    def _expand_all_from_node(self, start_item):
        if not start_item: return
        start_item.setExpanded(True)
        # self._on_item_expanded(start_item) # ensure icon updates
        for i in range(start_item.childCount()):
            child = start_item.child(i)
            item_data = child.data(0, Qt.ItemDataRole.UserRole)
            if item_data and item_data.get('type') in ('directory', 'directory_error'):
                self._expand_all_from_node(child) # Recurse

    def _collapse_all_from_node(self, start_item):
        if not start_item: return
        # Collapse children first
        for i in range(start_item.childCount()):
            child = start_item.child(i)
            item_data = child.data(0, Qt.ItemDataRole.UserRole)
            if item_data and item_data.get('type') in ('directory', 'directory_error'):
                self._collapse_all_from_node(child)
        start_item.setExpanded(False) # Then collapse this node
        # self._on_item_collapsed(start_item) # ensure icon updates