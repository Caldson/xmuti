import os, ctypes
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    pass


class XMutiReader:
    # 颜色码表（与README.md一致）：所有图像类型 00=白 / FF=黑，中间数值随版本扩展
    ColorMaps = {
        0x02: {0x00: "white", 0xFF: "black"},  # V1 黑白（2色）
        0x03: {0x00: "white", 0x01: "red", 0x02: "green", 0x03: "blue", 0xFF: "black"},  # V2 5色
        0x04: {0x00: "white", 0x01: "red", 0x02: "green", 0x03: "blue", 0x04: "yellow", 0xFF: "black"},  # V3 6色
    }
    ImageTitles = {
        0x02: "结果（黑白图像）",
        0x03: "结果（5色图像）",
        0x04: "结果（V3 6色图像）",
    }
    AllowedSizes = {0x02: (16,), 0x03: (16,), 0x04: (16, 32)}  # 只有V3起支持32x32

    def __init__(self, master: tk.Tk): # 为了兼容frame，不强制使用tk.Tk()。
        self.root = master
        self.FileType = None # 打开文件后为0x01（文本）/ 0x02-0x04（图像）
        tk.Button(self.root, text="打开文件", height=2, width=20, command=self.FileRead).pack(side=tk.LEFT)
        tk.Button(self.root, text="强制以V2版本打开图像", height=2, width=20, command=lambda: self.OpenImage(0x03)).pack(side=tk.LEFT)
        tk.Button(self.root, text="强制以V3版本打开图像", height=2, width=20, command=lambda: self.OpenImage(0x04)).pack(side=tk.LEFT)
        tk.Button(self.root, text="编辑文件", state="disabled", height=2, width=20).pack(side=tk.LEFT)

    def FileRead(self):
        path = filedialog.askopenfilename(filetypes=[("XMuti 多格式文件", "*.xmu")])
        if not path:
            return
        self.FileType = None
        with open(path, "rb") as f:
            # 如果文件不是以58 4D 55 54 49（也就是字符串"XMUTI"）开头的话直接报错
            if f.read(5) != b"XMUTI":
                messagebox.showerror("错误", "文件损坏或不是XMuti文件")
                return
            f.read(1) # 占位符（建议00或20，不读取）
            self.FileType = f.read(1)[0] # 文件类型

        if self.FileType == 0x01: # 文本类型
            with open(path, "rb") as f:
                f.read(7) # 文件头(5)+占位符(1)+类型(1)，正文从第7字节开始
                try:
                    text = f.read().decode("utf-8")
                except UnicodeDecodeError:
                    messagebox.showerror("错误", "文本解码失败（不是有效的UTF-8）")
                    return
            win = tk.Toplevel(self.root)
            win.title("结果（文本）")
            win.geometry("600x420") # 初始尺寸，可缩放
            # 文本框 + 垂直/水平滚动条（长文本可滚动）
            frame = tk.Frame(win)
            frame.pack(fill=tk.BOTH, expand=True)
            text_widget = tk.Text(frame, wrap="none", undo=True, font=("SimHei", 12))
            vsb = tk.Scrollbar(frame, orient=tk.VERTICAL, command=text_widget.yview)
            hsb = tk.Scrollbar(frame, orient=tk.HORIZONTAL, command=text_widget.xview)
            text_widget.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
            text_widget.insert("1.0", text) # 显示文本
            vsb.pack(side=tk.RIGHT, fill=tk.Y)
            hsb.pack(side=tk.BOTTOM, fill=tk.X)
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        elif self.FileType in self.ColorMaps: # 0x02/0x03/0x04 图像类型
            self.OpenImage(self.FileType, path)
        elif self.FileType in range(0x05, 0x09 + 1): # 0x05-0x09 保留
            messagebox.showerror("错误", "此类型是保留的类型。")
        elif self.FileType == 0x00:
            messagebox.showerror("错误", "此类型是未定义的保留的类型。")
        else:
            messagebox.showerror("错误", "此类型是未定义的类型。")

    def OpenImage(self, ftype, inppath=None):
        """按指定图像版本解读文件：ftype=0x02/0x03/0x04。
        自动打开时 ftype=文件里声明的类型；两个“强制”按钮则是强行用V2/V3的色表解读文件。"""
        if not inppath:
            inppath = filedialog.askopenfilename(filetypes=[("XMuti 多格式文件", "*.xmu")])
            if not inppath:
                return
        with open(inppath, "rb") as f:
            if f.read(5) != b"XMUTI":
                messagebox.showerror("错误", "文件损坏或不是XMuti文件")
                return
            f.read(1) # 占位符
            self.FileType = f.read(1)[0] # 实际声明类型
            if self.FileType == 0x01: # 文本类型不属于图像，报错
                messagebox.showerror("错误", "这是文本类型（0x01）文件，不是图像，请用“打开文件”查看。")
                return
            # 预留(9)不读取：文件头(5)+占位(1)+类型(1)+预留(9)=16字节后是像素数据
            pixels = f.read()[9:]
        size = self._MatchSize(len(pixels), self.AllowedSizes[ftype])
        if size is None:
            opts = "或".join(f"{s}x{s}" for s in self.AllowedSizes[ftype])
            messagebox.showerror("错误", f"不支持的图像尺寸（此版本仅支持{opts}）")
            return
        colormap = self.ColorMaps[ftype]
        win = tk.Toplevel(self.root)
        win.resizable(False, False)
        win.title("渲染中...")
        unknown = set()
        for i in range(size):
            for j in range(size):
                nowIndex = pixels[i * size + j]
                color = colormap.get(nowIndex)
                if color is None:
                    unknown.add(nowIndex)
                    color = "white"
                tk.Label(win, bg=color, fg=color, text="  ", width=2, height=1).grid(row=i, column=j)
        win.title(self.ImageTitles[ftype])
        if unknown:
            hexlist = ", ".join(f"0x{v:02X}" for v in sorted(unknown))
            messagebox.showwarning("警告", f"图像中存在不支持的颜色（{hexlist}），已渲染为白色。")

    @staticmethod
    def _MatchSize(length, allowed):
        for s in allowed:
            if length == s * s:
                return s
        return None


if __name__ == "__main__":
    r = tk.Tk()
    r.resizable(False, False)
    r.title("XMuti Workspace 0.1.0v")
    XMutiReader(r)
    r.mainloop()