import tkinter as tk
from tkinter.scrolledtext import ScrolledText

class CodeEditor:
    def __init__(self, parent):
        self.frame = tk.Frame(parent)
        
        self.text_frame = tk.Frame(self.frame)
        self.text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.line_numbers = tk.Text(
            self.text_frame,
            width=4,
            padx=5,
            pady=5,
            takefocus=0,
            border=0,
            state='disabled',
            wrap='none',
            font=("Consolas", 12),
            bg="#f0f0f0",
            fg="#666666",
            selectbackground="#f0f0f0",
            selectforeground="#666666"
        )
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        
        self.text_area = tk.Text(
            self.text_frame,
            font=("Consolas", 12),
            undo=True,
            wrap='none',
            borderwidth=0,
            highlightthickness=0
        )
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.scrollbar = tk.Scrollbar(self.text_frame, orient=tk.VERTICAL)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.text_area.config(yscrollcommand=self.scrollbar.set)
        self.line_numbers.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.on_scrollbar)
        
        self.h_scrollbar = tk.Scrollbar(self.frame, orient=tk.HORIZONTAL)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.text_area.config(xscrollcommand=self.h_scrollbar.set)
        self.h_scrollbar.config(command=self.text_area.xview)
        
        self.text_area.bind('<KeyPress>', self.on_key_press)
        self.text_area.bind('<KeyRelease>', self.on_key_release)
        self.text_area.bind('<Button-1>', self.on_click)
        self.text_area.bind('<MouseWheel>', self.on_mousewheel)
        self.text_area.bind('<Control-v>', self.on_paste)
        self.text_area.bind('<Control-z>', self.on_undo_redo)
        self.text_area.bind('<Control-y>', self.on_undo_redo)
        
        self.current_file = None
        
        self.update_line_numbers()
    
    def on_scrollbar(self, *args):
        self.text_area.yview(*args)
        self.line_numbers.yview(*args)
    
    def on_mousewheel(self, event):
        self.text_area.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self.line_numbers.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"
    
    def on_key_press(self, event):
        if event.keysym in ('Return', 'BackSpace', 'Delete'):
            self.after_idle(self.update_line_numbers)
    
    def on_key_release(self, event):
        if event.keysym in ('Return', 'BackSpace', 'Delete'):
            self.update_line_numbers()
    
    def on_click(self, event):
        self.after_idle(self.update_line_numbers)
    
    def on_paste(self, event):
        self.after_idle(self.update_line_numbers)
    
    def on_undo_redo(self, event):
        self.after_idle(self.update_line_numbers)
    
    def after_idle(self, func):
        self.text_area.after_idle(func)
    
    def update_line_numbers(self):
        self.line_numbers.config(state='normal')
        self.line_numbers.delete('1.0', tk.END)
        
        line_count = int(self.text_area.index('end-1c').split('.')[0])
        
        line_numbers_text = '\n'.join(str(i) for i in range(1, line_count + 1))
        self.line_numbers.insert('1.0', line_numbers_text)
        
        self.line_numbers.config(state='disabled')
        
        max_digits = len(str(line_count))
        new_width = max(3, max_digits + 1)
        self.line_numbers.config(width=new_width)
        
        try:
            top, bottom = self.text_area.yview()
            self.line_numbers.yview_moveto(top)
        except:
            pass
    
    def set_content(self, text):
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert(tk.END, text)
        self.update_line_numbers()
    
    def get_content(self):
        return self.text_area.get("1.0", tk.END)
    
    def pack(self, **kwargs):
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        self.frame.grid(**kwargs)