import os, ctypes
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

class XMutiReader:
    def __init__(self, master: tk.Tk): # 为了兼容frame，不强制使用tk.Tk()。
        self.FileType = None # 打开文件后为0x01（文本）或0x02（图像/黑白）
        self.root = master
        tk.Button(self.root, text="打开文件", height=2, width=20, command=self.FileRead).pack(side=tk.LEFT)
        tk.Button(self.root, text="编辑文件", state="disabled", height=2, width=20).pack(side=tk.LEFT)

    def FileRead(self):
        path = filedialog.askopenfilename()
        if not path:
            return
        self.FileType = None
        with open(path, "rb") as f:
            self.FileHeader = f.read(5)
            # 如果文件不是以58 4D 55 54 49（也就是字符串"XMUTI"）开头的话直接messagebox.showerror("错误", "文件损坏或不是XMuti文件")
            if self.FileHeader != b"XMUTI":
                messagebox.showerror("错误", "文件损坏或不是XMuti文件")
            self.FileType = f.read(2)[1:2] # 文件类型：0x01文本 / 0x02图像（黑白）
            if len(self.FileType) != 1 or self.FileType[0] not in (0x01, 0x02):
                messagebox.showerror("错误", "不支持的文件类型")
            
            if self.FileType[0] == 0x01: # 文本类型
                win = tk.Toplevel(self.root)
                win.resizable(False, False)
                win.title("结果（文本）")
                tk.Label(win, text=f.read().decode("utf-8")).pack()
            elif self.FileType[0] == 0x02: # 图像（黑白）类型
                #messagebox.showerror("错误", "暂不支持0x02（图像/黑白）类型文件")
                #return
                self.ImageTypeContent = f.read()[9:] # 读取剩余内容
                if len(self.ImageTypeContent) != 16*16:
                    messagebox.showerror("错误", "不支持的图像尺寸（仅支持16x16）")
                else:
                    win = tk.Toplevel(self.root)
                    win.resizable(False, False)
                    win.title("结果（黑白图像）")
                    for i in range(16):
                        for j in range(16):
                            nowIndex = self.ImageTypeContent[i*16+j]
                            color = "black" if nowIndex == 0xFF else "white"
                            tk.Label(win, bg=color, fg=color, text="  ",width=2, height=1).grid(row=i, column=j)

if __name__ == "__main__":
    r = tk.Tk()
    r.resizable(False, False)
    r.title("XMuti Workspace 0.1.0v")
    XMutiReader(r)
    r.mainloop()