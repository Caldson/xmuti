import tkinter as tk
root = tk.Tk()
root.title("颜色测试")
root.attributes("-topmost", True)
color="black"
label = tk.Label(root, text="             ", bg=color, fg=color)
label.pack()
def update():
    try:
        label.config(bg=color, fg=color, text="             ")
    except:
        label.config(bg="black", fg="white", text="颜色代码无效")
    root.after(1, update)
update()
inp = tk.Entry(root)
inp.pack()
def set():
    global color
    color=inp.get()
tk.Button(root, text="设置", command=set).pack()
root.mainloop()