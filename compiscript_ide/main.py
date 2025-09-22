import tkinter as tk
from ide.file_tree import FileTree
from ide.editor import CodeEditor
from ide.console import Console
from ide.toolbar import Toolbar
from ide.symbol_table_view import SymbolTableView
from ide.syntax_tree_view import SyntaxTreeView

class IDEApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Compiscript IDE - Analizador Semántico")
        self.root.geometry("1200x720")

        self.top_frame = tk.Frame(root)
        self.top_frame.pack(side=tk.TOP, fill=tk.X)
        self.toolbar = Toolbar(self.top_frame, self)
        self.toolbar.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.status_frame = tk.Frame(self.top_frame)
        self.status_frame.pack(side=tk.RIGHT, padx=10)
        self.status_label = tk.Label(self.status_frame, text="Sin archivo", bg="lightgray", padx=10, pady=2)
        self.status_label.pack()

        self.main_split = tk.PanedWindow(root, orient=tk.HORIZONTAL)
        self.main_split.pack(fill=tk.BOTH, expand=True)

        self.left_split = tk.PanedWindow(self.main_split, orient=tk.HORIZONTAL)
        self.main_split.add(self.left_split, minsize=420)

        self.file_tree = FileTree(self.left_split, self)
        self.left_split.add(self.file_tree.frame, minsize=220)

        self.left_vertical = tk.PanedWindow(self.left_split, orient=tk.VERTICAL)
        self.left_split.add(self.left_vertical)

        self.editor = CodeEditor(self.left_vertical)
        self.left_vertical.add(self.editor.frame, minsize=260)

        self.console = Console(self.left_vertical)
        self.left_vertical.add(self.console, minsize=140)

        self.right_split = tk.PanedWindow(self.main_split, orient=tk.VERTICAL)
        self.main_split.add(self.right_split, minsize=480)

        self.syntax_tree_view = SyntaxTreeView(self.right_split)
        self.right_split.add(self.syntax_tree_view.frame, minsize=240)

        self.symbol_table_view = SymbolTableView(self.right_split)
        self.right_split.add(self.symbol_table_view.frame, minsize=240)

    def open_file(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            self.editor.set_content(content)
            self.editor.current_file = filepath
            filename = filepath.split('/')[-1] if '/' in filepath else filepath.split('\\')[-1]
            self.root.title(f"Compiscript IDE - {filename}")
            if filepath.endswith('.cps'):
                self.status_label.config(text=f"{filename}", bg="lightgreen")
                self.console.log(f"Archivo .cps abierto: {filename}")
            else:
                self.status_label.config(text=f"{filename}", bg="lightyellow")
                self.console.log(f"Archivo abierto: {filename}")
        except Exception as e:
            self.console.log(f"Error al abrir archivo: {str(e)}")
            self.status_label.config(text="Error al abrir", bg="lightcoral")

    def get_code(self):
        return self.editor.get_content()

    def get_current_path(self):
        return self.editor.current_file

if __name__ == "__main__":
    root = tk.Tk()
    app = IDEApp(root)
    root.mainloop()
