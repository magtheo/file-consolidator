# app/file_tree_view.py
import tkinter as tk
from tkinter import ttk, font
from pathlib import Path
import os

class FileTreeView(ttk.Frame):
    # --- CONFIGURATION ---
    USE_ICONS = True  # << SET THIS TO False TO TEST WITHOUT ANY ICONS
    TARGET_FONT_FAMILY = "DejaVu Sans" # Or "Liberation Sans", "Noto Sans"
    TARGET_FONT_SIZE = 11  # INCREASED from 9 to 11
    TREEVIEW_INDENT = 16   # INCREASED from 8 to 16
    ICON_SIZE = 16         # INCREASED from 10 to 16
    
    # Add padding to make the rows more spacious
    ROW_PADDING = 14        # NEW PARAMETER

    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)

        # --- FONT SETUP ---
        self.font_for_style = None
        self.font_for_tags = None
        try:
            # For ttk.Style, a font name string or tuple is best.
            self.font_for_style = (self.TARGET_FONT_FAMILY, self.TARGET_FONT_SIZE)
            # Test this font can be resolved by Tk for metrics
            font.nametofont(self.font_for_style) # Will raise TclError if font is bad
            # For tags, font.Font object is fine and gives access to .actual()
            self.font_for_tags = font.Font(family=self.TARGET_FONT_FAMILY, size=self.TARGET_FONT_SIZE)
        except tk.TclError:
            print(f"Warning: Font '{self.TARGET_FONT_FAMILY}' at size {self.TARGET_FONT_SIZE} not found or invalid. Falling back.")
            try:
                fallback_family = "Liberation Sans"
                self.font_for_style = (fallback_family, self.TARGET_FONT_SIZE)
                font.nametofont(self.font_for_style)
                self.font_for_tags = font.Font(family=fallback_family, size=self.TARGET_FONT_SIZE)
            except tk.TclError:
                print(f"Warning: Font '{fallback_family}' not found. Using TkDefaultFont.")
                self.font_for_style = ("TkDefaultFont", self.TARGET_FONT_SIZE) # Absolute fallback
                self.font_for_tags = font.Font(family="TkDefaultFont", size=self.TARGET_FONT_SIZE)

        print(f"Attempting Treeview Style Font: {self.font_for_style}")
        if self.font_for_tags:
            print(f"Actual Tag Font: {self.font_for_tags.actual()}")

        # --- TTK STYLE CONFIGURATION ---
        s = ttk.Style()
        
        # Try a different theme to see if it behaves better
        current_theme = s.theme_use()
        print(f"Current theme: {current_theme}. Available: {s.theme_names()}")
        if 'clam' in s.theme_names():
            try:
                s.theme_use('clam') # 'clam' is often more basic and predictable
                print("Switched to 'clam' theme for Treeview.")
            except tk.TclError:
                print("Could not switch to 'clam' theme.")
                s.theme_use(current_theme) # Revert if failed

        # Calculate rowheight with increased padding - use both font size and icon size
        rowheight = max(self.TARGET_FONT_SIZE + self.ROW_PADDING * 2, 
                         self.ICON_SIZE + self.ROW_PADDING)
                         
        s.configure('Treeview',
                    rowheight=rowheight,
                    indent=self.TREEVIEW_INDENT,
                    font=self.font_for_style)
        
        # Add item-specific styling to increase cell padding
        s.configure('Treeview.Item', padding=(4, 2))

        # --- TREEVIEW WIDGET ---
        self.tree = ttk.Treeview(self, selectmode='extended', show='tree')
        # The style 'Treeview' should be picked up. No self.tree.configure(font=...)

        self.tree["columns"] = ("fullpath", "type")
        self.tree.column("#0", width=400, minwidth=250, anchor='w', stretch=tk.YES)
        self.tree.column("fullpath", width=0, stretch=tk.NO, minwidth=0)
        self.tree.column("type", width=0, stretch=tk.NO, minwidth=0)
        self.tree.heading("#0", text="Name", anchor='w')

        ysb = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        xsb = ttk.Scrollbar(self, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        ysb.grid(row=0, column=1, sticky='ns')
        xsb.grid(row=1, column=0, sticky='ew')
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # --- ICONS & TAGS ---
        if self.USE_ICONS:
            self.file_icon = self._load_or_create_icon("file.png", "dodgerblue", icon_size=self.ICON_SIZE)
            self.folder_icon = self._load_or_create_icon("folder.png", "darkorange", icon_size=self.ICON_SIZE)
            self.folder_open_icon = self._load_or_create_icon("folder-open.png", "gold", icon_size=self.ICON_SIZE)
            self.error_icon = self._load_or_create_icon("error.png", "red", icon_size=self.ICON_SIZE)

            self.tree.tag_configure('file', image=self.file_icon, font=self.font_for_tags)
            self.tree.tag_configure('directory', image=self.folder_icon, font=self.font_for_tags)
            self.tree.tag_configure('directory_open', image=self.folder_open_icon, font=self.font_for_tags)
            self.tree.tag_configure('directory_error', image=self.error_icon, font=self.font_for_tags)
        else:
            # If not using icons, still configure fonts for tags
            self.tree.tag_configure('file', font=self.font_for_tags)
            self.tree.tag_configure('directory', font=self.font_for_tags)
            self.tree.tag_configure('directory_open', font=self.font_for_tags)
            self.tree.tag_configure('directory_error', font=self.font_for_tags)

        self.tree.bind("<<TreeviewOpen>>", self._on_open_dir)
        self.tree.bind("<<TreeviewClose>>", self._on_close_dir)

    def _load_or_create_icon(self, icon_name: str, default_color: str = "grey", icon_size: int = 16):
        # Ensure PhotoImage objects are stored if they are class/instance members,
        # but here they are local to this method call before being assigned to self.xxx_icon
        base_path = Path(__file__).parent.parent / "assets"
        icon_path = base_path / icon_name
        
        loaded_image = None
        if icon_path.is_file():
            try:
                temp_image = tk.PhotoImage(file=str(icon_path))
                # Basic subsampling if image is larger than target icon_size
                if temp_image.width() > icon_size or temp_image.height() > icon_size:
                    factor_w = max(1, temp_image.width() // icon_size)
                    factor_h = max(1, temp_image.height() // icon_size)
                    factor = max(1, min(factor_w, factor_h)) # Smallest reduction factor
                    loaded_image = temp_image.subsample(factor, factor)
                else:
                    loaded_image = temp_image
            except tk.TclError as e:
                print(f"Warning: Could not load icon {icon_path}: {e}. Creating dummy icon.")
        
        if loaded_image is None: # Fallback to create dummy icon
            loaded_image = tk.PhotoImage(width=icon_size, height=icon_size)
            if icon_size > 0: # Only draw if size is positive
                dot_size = max(1, icon_size - 4) # e.g., for 10px icon, 6px dot
                offset = (icon_size - dot_size) // 2 
                x1, y1 = offset, offset
                x2, y2 = offset + dot_size - 1, offset + dot_size - 1
                # Ensure coordinates are valid
                if x1 <= x2 and y1 <= y2 and x2 < icon_size and y2 < icon_size :
                    loaded_image.put(default_color, to=(x1, y1, x2, y2))
                elif icon_size > 0: # Fallback for very small icon_size
                    loaded_image.put(default_color, to=(0, 0, icon_size - 1, icon_size - 1))
        return loaded_image

    # Rest of the methods remain unchanged
    def _on_open_dir(self, event):
        item_id = self.tree.focus() 
        if item_id and self.tree.tag_has('directory', item_id):
            self.tree.item(item_id, tags=('directory_open',))

    def _on_close_dir(self, event):
        item_id = self.tree.focus()
        if item_id and self.tree.tag_has('directory_open', item_id):
            self.tree.item(item_id, tags=('directory',))

    def _insert_item(self, parent_node_id, item_data):
        item_type = item_data['type']
        tags_to_apply_list = []
        if item_type == 'file': tags_to_apply_list.append('file')
        elif item_type == 'directory': tags_to_apply_list.append('directory')
        elif item_type == 'directory_error':
            tags_to_apply_list.append('directory_error')
            item_data['name'] = f"[Err] {item_data['name']}"
        tags_to_apply = tuple(tags_to_apply_list)
        has_children = 'children' in item_data and item_data['children']
        node_id = self.tree.insert(
            parent_node_id, 'end', text=item_data['name'],
            values=(item_data['path'], item_type),
            open=False, tags=tags_to_apply
        )
        if item_type == 'directory' and has_children:
            for child_item in item_data['children']:
                self._insert_item(node_id, child_item)

    def populate_tree(self, directory_data_list):
        for i in self.tree.get_children():
            try: self.tree.delete(i)
            except tk.TclError: pass 
        for item_data in directory_data_list:
            self._insert_item('', item_data)

    def get_selected_files(self) -> list[str]:
        selected_file_paths = set()
        selected_item_ids = self.tree.selection()
        for item_id in selected_item_ids:
            try: item_values = self.tree.item(item_id, 'values')
            except tk.TclError: continue
            if not item_values or len(item_values) < 2: continue
            item_path_str, item_type = item_values[0], item_values[1]
            if item_type == 'file': selected_file_paths.add(item_path_str)
            elif item_type == 'directory': self._add_files_from_directory(item_id, selected_file_paths)
        return sorted(list(selected_file_paths))

    def _add_files_from_directory(self, dir_item_id, selected_file_paths_set):
        try: children = self.tree.get_children(dir_item_id)
        except tk.TclError: return
        for child_id in children:
            try: child_values = self.tree.item(child_id, 'values')
            except tk.TclError: continue
            if not child_values or len(child_values) < 2: continue
            child_path_str, child_type = child_values[0], child_values[1]
            if child_type == 'file': selected_file_paths_set.add(child_path_str)
            elif child_type == 'directory': self._add_files_from_directory(child_id, selected_file_paths_set)