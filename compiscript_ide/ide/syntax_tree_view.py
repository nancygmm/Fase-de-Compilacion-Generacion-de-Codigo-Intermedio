import tkinter as tk
from tkinter import ttk

class SyntaxTreeView:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        ttk.Label(self.frame, text="Árbol sintáctico", anchor="w").pack(fill=tk.X, pady=(0,4))
        self.text = tk.Text(self.frame, wrap="none", height=12, font=("Consolas", 10))
        self.text.pack(fill=tk.BOTH, expand=True)
        yscroll = ttk.Scrollbar(self.frame, orient="vertical", command=self.text.yview)
        xscroll = ttk.Scrollbar(self.frame, orient="horizontal", command=self.text.xview)
        self.text.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)
        xscroll.pack(side=tk.BOTTOM, fill=tk.X)

    def clear(self):
        self.text.delete("1.0", tk.END)

    def _lines_from_ast(self, node, depth=0, out=None):
        if out is None:
            out = []
        if node is None:
            return out
        indent = "  " * depth
        cls = node.__class__.__name__
        if hasattr(node, "getText") and node.getChildCount() == 0:
            out.append(f"{indent}{cls}: {node.getText()}")
        else:
            out.append(f"{indent}{cls}")
        if hasattr(node, "getChildCount"):
            for i in range(node.getChildCount()):
                self._lines_from_ast(node.getChild(i), depth+1, out)
        return out

    def load_from_ast(self, ast):
        self.clear()
        lines = self._lines_from_ast(ast, 0, [])
        self.text.insert("1.0", "\n".join(lines))
