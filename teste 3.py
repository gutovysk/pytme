import tkinter as tk

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.pack()
        self.create_widgets()
        self.cursor_on = True
        self.update_cursor()

    def create_widgets(self):
        self.canvas = tk.Canvas(self, width=500, height=500)
        self.canvas.pack()

    def update_cursor(self):
        if self.cursor_on:
            self.canvas.create_rectangle(100, 100, 150, 150, fill='black')
            self.cursor_on = False
        else:
            self.canvas.delete("all")
            self.cursor_on = True
        self.after(500, self.update_cursor)

root = tk.Tk()
app = Application(master=root)
app.mainloop()
