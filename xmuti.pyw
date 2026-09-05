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
        tk.Button(self.root, text="强制以V2版本打开图像", height=2, width=20, command=self.FileRead_V2Image).pack(side=tk.LEFT)
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
            self.FileType = f.read(2)[1:2] # 文件类型
            
            if self.FileType[0] == 0x01: # 文本类型
                win = tk.Toplevel(self.root)
                win.resizable(False, False)
                win.title("结果（文本）")
                tk.Label(win, text=f.read().decode("utf-8")).pack()
            elif self.FileType[0] == 0x02: # 图像（黑白）类型
                self.ImageTypeContent = f.read()[9:] # 读取剩余内容
                if len(self.ImageTypeContent) != 16*16:
                    messagebox.showerror("错误", "不支持的图像尺寸（仅支持16x16）")
                else:
                    win = tk.Toplevel(self.root)
                    win.resizable(False, False)
                    win.title("结果（黑白图像）")
                    HasCannotColor = False
                    for i in range(16):
                        for j in range(16):
                            nowIndex = self.ImageTypeContent[i*16+j]
                            if nowIndex in (0x00, 0xFF):
                                color = "black" if nowIndex == 0xFF else "white"
                            else:
                                HasCannotColor = True
                                color = "white"
                            tk.Label(win, bg=color, fg=color, text="  ",width=2, height=1).grid(row=i, column=j)
                    if HasCannotColor:
                        messagebox.showwarning("警告", "图像中存在不支持的颜色，将渲染为白色。如果想要支持更多颜色，请改用V2或更高版本的图像类型。")
                    else:
                        messagebox.showinfo("提醒", "新版本已经支持了更多颜色，建议使用V2或更高版本的图像类型，它们也兼容低版本。")
            elif self.FileType[0] == 0x03: # 图像（红、绿、蓝、黑、白）类型
                self.FileRead_V2Image(path)
            elif self.FileType[0] in list(range(0x04, 0x09+1)):
                messagebox.showerror("错误", "此类型是保留的类型。")
            elif self.FileType[0] == 0x00:
                messagebox.showerror("错误", "此类型是未定义的保留的类型。")
            else:
                messagebox.showerror("错误", "此类型是未定义的类型。")
    def FileRead_V2Image(self, inppath=None):
        if not inppath:
            path = filedialog.askopenfilename()
            if not path:
                return
        else:
            path = inppath
        self.FileType = None
        with open(path, "rb") as f:
            # 无论从哪个入口进来都重新打开文件，指针都在第0字节，统一按下面读
            self.FileHeader = f.read(5)
            if self.FileHeader != b"XMUTI":
                messagebox.showerror("错误", "文件损坏或不是XMuti文件")
                return
            f.read(1)  # 占位符
            self.FileType = f.read(1)  # 文件类型（02旧黑白 / 03五色）
            # 此时已读到第7字节；文件头(5)+占位符(1)+类型(1)+预留(9)=16字节后才是图像数据
            self.ImageTypeContent = f.read()[9:]
            if len(self.ImageTypeContent) != 16*16:
                messagebox.showerror("错误", "不支持的图像尺寸（仅支持16x16）")
            else:
                win = tk.Toplevel(self.root)
                win.resizable(False, False)
                win.title("结果（5色图像）")
                HasCannotColor = False
                for i in range(16):
                    for j in range(16):
                        nowIndex = self.ImageTypeContent[i*16+j]
                        ColorMap = {
                            0x00: "white",
                            0x01: "red",
                            0x02: "green",
                            0x03: "blue",
                            0xFF: "black"
                        }
                        if nowIndex not in ColorMap:
                            HasCannotColor = True
                            color = "white"
                        else:
                            color = ColorMap[nowIndex]
                        tk.Label(win, bg=color, fg=color, text="  ",width=2, height=1).grid(row=i, column=j)
                if HasCannotColor:
                    messagebox.showwarning("警告", "图像中存在不支持的颜色，将渲染为白色。")

if __name__ == "__main__":
    r = tk.Tk()
    r.resizable(False, False)
    r.title("XMuti Workspace 0.1.0v")
    XMutiReader(r)
    r.mainloop()