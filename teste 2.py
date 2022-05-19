from PyTME import *

def iii():
	print("foi")

x=Pytme()
x.text("oko","kkk",7,x)
import pdb;pdb.set_trace()
x.window.after(2000,iii())
y=x.type_text("kokko"," 000:")
x.goto_xy(10,10)
x.text(y)
x.delay(4000)
z=x.type_textln("ok:"," ")
x.goto_xy(10,10)
x.text(z)
x.delay(4000)
try:
    import Tkinter as tk
except:
    import tkinter as tk
    
import time

class Clock():
    def __init__(self):
        self.root = tk.Tk()
        self.label = tk.Label(text="", font=('Helvetica', 48), fg='red')
        self.label.pack()
        self.update_clock()
        self.root.mainloop()

    def update_clock(self):
        now = time.strftime("%H:%M:%S")
        self.label.configure(text=now)
        self.root.after(1000, self.update_clock)

app=Clock()

import pdb;pdb.set_trace()