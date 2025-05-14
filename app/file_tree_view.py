# app/file_tree_view.py
import tkinter as tk
from tkinter import ttk, font
from pathlib import Path
import os

class FileTreeView(ttk.Frame):
    # --- CONFIGURATION (from your previous version) ---
    USE_ICONS = True
    TARGET_FONT_FAMILY = "DejaVu Sans" 
    TARGET_FONT_SIZE = 10 # Adjusted for checkbox char
    TREEVIEW_INDENT = 20   
    ICON_SIZE = 16        
    ROW_PADDING = 3 # Reduced padding for checkbox version

    # --- CHECKBOX CHARACTERS ---
    UNCHECKED_CHAR = "☐ "  # U+2610 BALLOT BOX
    CHECKED_CHAR = "☑ "    # U+2611 BALLOT BOX WITH CHECK
    # Make sure your chosen font supports these characters well!

    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)

        self.item_check_states = {} # Stores item_id -> bool (checked True/False)
        self.tree_item_data = {}    # Stores item_id -> original item_data for type info

        # --- FONT SETUP ---
        self.font_for_style = None
        self.font_for_tags = None
        try:
            self.font_for_style = (self.TARGET_FONT_FAMILY, self.TARGET_FONT_SIZE)
            font.nametofont(self.font_for_style) 
            self.font_for_tags = font.Font(family=self.TARGET_FONT_FAMILY, size=self.TARGET_FONT_SIZE)
        except tk.TclError:
            print(f"Warning: Font '{self.TARGET_FONT_FAMILY}' at size {self.TARGET_FONT_SIZE} not found. Falling back.")
            default_fallback_family = "TkDefaultFont" # Changed fallback
            self.font_for_style = (default_fallback_family, self.TARGET_FONT_SIZE)
            self.font_for_tags = font.Font(family=default_fallback_family, size=self.TARGET_FONT_SIZE)

        print(f"Treeview Style Font: {self.font_for_style}")
        if self.font_for_tags: print(f"Tag Font: {self.font_for_tags.actual()}")

        # --- TTK STYLE CONFIGURATION ---
        s = ttk.Style()
        current_theme = s.theme_use()
        if 'clam' in s.theme_names() and current_theme != 'clam':
            try: s.theme_use('clam'); print("Switched to 'clam' theme.")
            except tk.TclError: s.theme_use(current_theme)

        font_height = self.font_for_tags.metrics("linespace")
        rowheight = max(font_height + self.ROW_PADDING * 2,
                        self.ICON_SIZE + self.ROW_PADDING * 2 if self.USE_ICONS else 0)
        
        s.configure('Treeview', rowheight=int(rowheight), indent=self.TREEVIEW_INDENT, font=self.font_for_style)
        # Try to prevent selection highlight from obscuring checkboxes or text
        s.map('Treeview', 
              background=[('selected', s.lookup('Treeview', 'background')), 
                          ('focus', s.lookup('Treeview', 'background'))], # Keep background same on focus
              foreground=[('selected', s.lookup('Treeview', 'foreground')),
                          ('focus', s.lookup('Treeview', 'foreground'))]) # Keep text color same on focus
        s.configure('Treeview.Item', padding=(3,1)) # Item padding (horizontal, vertical)


        # --- TREEVIEW WIDGET ---
        self.tree = ttk.Treeview(self, selectmode='browse', show='tree') # 'browse' for single item focus
                                                                        # We handle "selection" via checkboxes

        self.tree["columns"] = ("fullpath", "type")
        self.tree.column("#0", width=400, minwidth=250, anchor='w', stretch=tk.YES)
        self.tree.column("fullpath", width=0, stretch=tk.NO)
        self.tree.column("type", width=0, stretch=tk.NO)
        self.tree.heading("#0", text="Name", anchor='w')

        ysb = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        xsb = ttk.Scrollbar(self, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        ysb.grid(row=0, column=1, sticky='ns')
        xsb.grid(row=1, column=0, sticky='ew')
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        if self.USE_ICONS:
            self.file_icon = self._load_or_create_icon("file.png", "dodgerblue", icon_size=self.ICON_SIZE)
            self.folder_icon = self._load_or_create_icon("folder.png", "darkorange", icon_size=self.ICON_SIZE)
            self.folder_open_icon = self._load_or_create_icon("folder-open.png", "gold", icon_size=self.ICON_SIZE)
            self.error_icon = self._load_or_create_icon("error.png", "red", icon_size=self.ICON_SIZE)

            self.tree.tag_configure('file', image=self.file_icon, font=self.font_for_tags)
            self.tree.tag_configure('directory', image=self.folder_icon, font=self.font_for_tags)
            self.tree.tag_configure('directory_open', image=self.folder_open_icon, font=self.font_for_tags)
            self.tree.tag_configure('directory_error', image=self.error_icon, font=self.font_for_tags)
        else: # Configure fonts even if not using icons
            for tag_name in ['file', 'directory', 'directory_open', 'directory_error']:
                self.tree.tag_configure(tag_name, font=self.font_for_tags)

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
            self.tree.tag_configure('file', font=self.font_for_tags)
            self.tree.tag_configure('directory', font=self.font_for_tags)
            self.tree.tag_configure('directory_open', font=self.font_for_tags)
            self.tree.tag_configure('directory_error', font=self.font_for_tags)

        # --- EVENT BINDINGS ---
        self.tree.bind("<<TreeviewOpen>>", self._on_open_dir_visuals)
        self.tree.bind("<<TreeviewClose>>", self._on_close_dir_visuals)
        self.tree.bind("<ButtonRelease-1>", self._on_item_click) # Use ButtonRelease for better UX with drag

    def _load_or_create_icon(self, icon_name: str, default_color: str = "grey", icon_size: int = 16):
        base_path = Path(__file__).parent.parent / "assets"
        icon_path = base_path / icon_name
        loaded_image = None
        if icon_path.is_file():
            try:
                temp_image = tk.PhotoImage(file=str(icon_path))
                if temp_image.width() != icon_size or temp_image.height() != icon_size:
                    # Simple scaling (subsample if larger, or recreate if smaller - for now just subsample)
                    factor_w = max(1, temp_image.width() // icon_size)
                    factor_h = max(1, temp_image.height() // icon_size)
                    factor = max(1, min(factor_w, factor_h)) 
                    loaded_image = temp_image.subsample(factor, factor)
                else:
                    loaded_image = temp_image
            except tk.TclError as e:
                print(f"Warning: Could not load icon {icon_path}: {e}. Creating dummy icon.")
        if loaded_image is None:
            loaded_image = tk.PhotoImage(width=icon_size, height=icon_size)
            if icon_size > 0:
                dot_size = max(1, icon_size - 4)
                offset = (icon_size - dot_size) // 2
                if 0 <= offset < icon_size and 0 <= offset + dot_size -1 < icon_size :
                     loaded_image.put(default_color, to=(offset, offset, offset + dot_size - 1, offset + dot_size - 1))
        return loaded_image

    def _on_open_dir_visuals(self, event): # Renamed
        item_id = self.tree.focus()
        if item_id and self.tree.tag_has('directory', item_id):
            self.tree.item(item_id, tags=('directory_open',))

    def _on_close_dir_visuals(self, event): # Renamed
        item_id = self.tree.focus()
        if item_id and self.tree.tag_has('directory_open', item_id):
            self.tree.item(item_id, tags=('directory',))

    def _get_display_text(self, item_id, original_name):
        is_checked = self.item_check_states.get(item_id, False)
        return (self.CHECKED_CHAR if is_checked else self.UNCHECKED_CHAR) + original_name

    def _update_item_text(self, item_id):
        """Updates the display text of an item based on its check state and original name."""
        if not self.tree.exists(item_id): return # Item might have been deleted
        
        original_name = self.tree_item_data.get(item_id, {}).get("name", "")
        if not original_name: # Fallback if original name isn't stored (shouldn't happen)
            current_text = self.tree.item(item_id, "text")
            original_name = current_text.lstrip(self.CHECKED_CHAR).lstrip(self.UNCHECKED_CHAR)

        new_text = self._get_display_text(item_id, original_name)
        self.tree.item(item_id, text=new_text)

    def _on_item_click(self, event):
        item_id = self.tree.identify_row(event.y)
        if not item_id: return

        # Toggle the state for the clicked item
        current_state = self.item_check_states.get(item_id, False)
        new_state = not current_state
        
        self._set_check_state_recursive(item_id, new_state)
        self.tree.focus(item_id) # Keep focus on the clicked item


    def _set_check_state_recursive(self, item_id, state):
        """Sets the check state for an item and all its descendants."""
        if not self.tree.exists(item_id): return

        self.item_check_states[item_id] = state
        self._update_item_text(item_id)

        # If it's a directory, recursively apply to children
        item_type = self.tree_item_data.get(item_id, {}).get("type", "")
        if item_type == "directory" or item_type == "directory_error":
            for child_id in self.tree.get_children(item_id):
                self._set_check_state_recursive(child_id, state)


    def _insert_item(self, parent_node_id, item_data):
        item_type = item_data['type']
        original_name = item_data['name']
        
        tags_to_apply = [item_type] # Start with type tag for icon

        node_id = self.tree.insert(
            parent_node_id, 'end',
            text=self._get_display_text(None, original_name), # Initial text with unchecked box
            values=(item_data['path'], item_type),
            open=False,
            tags=tuple(tags_to_apply)
        )
        self.item_check_states[node_id] = False # Default to unchecked
        self.tree_item_data[node_id] = item_data # Store original data

        if item_type == 'directory' and item_data.get("children"):
            for child_item in item_data["children"]:
                self._insert_item(node_id, child_item)
        elif item_type == 'directory_error': # Special handling for error nodes
            self.tree.item(node_id, text=self._get_display_text(node_id, f"[Err] {original_name}"))


    def populate_tree(self, directory_data_list):
        # Clear existing tree and states
        self.item_check_states.clear()
        self.tree_item_data.clear()
        for i in self.tree.get_children():
            try: self.tree.delete(i)
            except tk.TclError: pass # Item might already be gone
        
        for item_data in directory_data_list:
            self._insert_item('', item_data)

    def get_checked_files(self) -> list[str]:
        """Gets paths of all files that are currently checked."""
        checked_file_paths = set()
        for item_id, is_checked in self.item_check_states.items():
            if is_checked and self.tree.exists(item_id):
                item_data = self.tree_item_data.get(item_id)
                if item_data and item_data['type'] == 'file':
                    checked_file_paths.add(item_data['path'])
        return sorted(list(checked_file_paths))