import os, ctypes
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    pass


# ---------- TXTPro 风格浮动小窗（深色标题栏、可拖动、右上角X） ----------
class Window(tk.Frame):
    def __init__(self, master, window_title="窗口", width=220, height=160, placex=100, placey=100, bg="#f0f0f0", **kw):
        super().__init__(master, bd=2, relief="raised", bg=bg, **kw)
        self.place(x=placex, y=placey, width=width, height=height)
        self.width, self.height = width, height
        self.title_bar = tk.Frame(self, bg="#333", height=28)
        self.title_bar.pack(side=tk.TOP, anchor=tk.W, fill=tk.X)
        self.title_label = tk.Label(self.title_bar, text=window_title, fg="white", bg="#333")
        self.title_label.pack(side=tk.LEFT, padx=6)
        self.close_button = tk.Button(self.title_bar, text="X", command=self.destroy, bg="#333", fg="white",
                                      bd=0, relief="raised", activebackground="#333", activeforeground="white")
        self.close_button.pack(side=tk.RIGHT, padx=6)
        self.content = tk.Frame(self, bg=bg)
        self.content.pack(fill=tk.BOTH, expand=True)
        self._dx, self._dy = 0, 0
        self.title_bar.bind("<Button-1>", self._start_drag)
        self.title_bar.bind("<B1-Motion>", self._do_drag)
        self.title_label.bind("<Button-1>", self._start_drag)
        self.title_label.bind("<B1-Motion>", self._do_drag)

    def _start_drag(self, e):
        self.lift(); self._dx, self._dy = e.x, e.y

    def _do_drag(self, e):
        nx = self.winfo_x() + e.x - self._dx
        ny = self.winfo_y() + e.y - self._dy
        p = self.master
        nx = max(0, min(nx, p.winfo_width() - self.winfo_width()))
        ny = max(0, min(ny, p.winfo_height() - self.winfo_height()))
        self.place(x=nx, y=ny)


# ---------- 主编辑器 ----------
class XMutiReader:
    ColorMaps = {
        0x02: {0x00: "white", 0xFF: "black"},  # V1 黑白
        0x03: {0x00: "white", 0x01: "red", 0x02: "green", 0x03: "blue", 0xFF: "black"},  # V2 5色
        0x04: {0x00: "white", 0x01: "red", 0x02: "green", 0x03: "blue", 0x04: "yellow", 0xFF: "black"},  # V3 6色
        0x05: {0x00: "white", 0x01: "red", 0x02: "green", 0x03: "blue", 0x04: "yellow", 0x05: "orange", 0x06: "cyan", 0x07: "purple", 0x08: "lightgreen", 0x09: "lightblue", 0x0A: "lightyellow", 0x0B: "lightcyan", 0x0C: "gray", 0xFF: "black"},  # V4 14色
    }
    ImageTitles = {0x02: "黑白图像", 0x03: "5色图像", 0x04: "V3 6色图像", 0x05: "V4 14色图像"}
    AllowedSizes = {0x02: (16,), 0x03: (16,), 0x04: (16, 32), 0x05: (16, 32, 34, 36, 38, 40, 64)}
    MAX_TABS = 25  # TXTPro 风格上限

    def __init__(self, master):
        self.root = master
        self.root.title("XMuti")
        self.root.geometry("940x500")
        self.tabs_data = {}      # tab_frame -> meta
        self.tab_counter = 0
        self.FileType = None
        self.current_folder = None
        self.folder_files = []
        self._build_top_frame()
        self._build_main_frame()

    # ---------- 顶部菜单栏 ----------
    def _build_top_frame(self):
        top = tk.Frame(self.root)
        top.pack(pady=10, padx=10, fill="x")
        btn_frame = tk.Frame(top)
        btn_frame.pack(side="left", anchor="w")

        file_btn = tk.Menubutton(btn_frame, text="文件", relief=tk.RAISED)
        file_btn.pack(side="left", padx=(0, 10))
        fmenu = tk.Menu(file_btn, tearoff=0)
        fmenu.add_command(label="打开文件（Ctrl-O）", command=self.open_file)
        fmenu.add_command(label="创建文件（Ctrl-N）", command=self.create_file)
        fmenu.add_command(label="保存（Ctrl-S）", command=self.save_file)
        fmenu.add_separator()
        force_menu = tk.Menu(fmenu, tearoff=0)
        force_menu.add_command(label="以V1版本打开图像", command=lambda: self.open_file(forced=0x02))
        force_menu.add_command(label="以V2版本打开图像", command=lambda: self.open_file(forced=0x03))
        force_menu.add_command(label="以V3版本打开图像", command=lambda: self.open_file(forced=0x04))
        force_menu.add_command(label="以V4版本打开图像", command=lambda: self.open_file(forced=0x05))
        fmenu.add_cascade(label="强制打开图像", menu=force_menu)
        fmenu.add_separator()
        fmenu.add_command(label="打开文件夹", command=self.open_folder)
        fmenu.add_command(label="关闭当前标签", command=lambda: self.close_tab(self.notebook.select()))
        file_btn.config(menu=fmenu)

        self.status_label = tk.Label(top, text="", font=("Consolas", 8), fg="#666666")
        self.status_label.pack(side="right", padx=(0, 10))

    # ---------- 主区域（左文件夹列表 + 中央标签） ----------
    def _build_main_frame(self):
        main = tk.Frame(self.root)
        main.pack(fill="both", expand=True)
        # 左侧文件列表面板（定宽、带标题，整洁）
        folder_panel = tk.Frame(main, bd=1, relief=tk.SUNKEN)
        folder_panel.pack(side="left", fill="y", padx=(10, 0), pady=(0, 10))
        tk.Label(folder_panel, text="文件", font=("Consolas", 9, "bold"), bg="#e0e0e0").pack(side="top", anchor="w", fill="x")
        self.folder_listbox = tk.Listbox(folder_panel, font=("Consolas", 10), width=22)
        self.folder_listbox.pack(side="left", fill="both", expand=True)
        self.folder_listbox.bind("<<ListboxSelect>>", self._on_folder_file_select)
        # 中央标签页（父容器是 main，和文件夹面板同属 main，才会正确并排）
        self.notebook = ttk.Notebook(main)
        self.notebook.pack(side="left", fill="both", expand=True, padx=(10, 10), pady=(0, 10))
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self.notebook.bind("<Button-3>", self._on_tab_right_click)   # 右键菜单

    # ---------- 打开/强制打开 ----------
    def open_file(self, forced=None):
        path = filedialog.askopenfilename(filetypes=[("XMuti 多格式文件", "*.xmu"), ("XMuti（备份）多格式文件", "*.xmu.bak")])
        if not path:
            return
        self._load_file(path, forced)

    def open_folder(self):
        path = filedialog.askdirectory(title="选择文件夹")
        if not path:
            return
        self.current_folder = path
        self._refresh_folder()

    def _refresh_folder(self):
        if not self.current_folder:
            return
        self.folder_listbox.delete(0, tk.END)
        try:
            files = [f for f in os.listdir(self.current_folder) if os.path.isfile(os.path.join(self.current_folder, f))]
            self.folder_files = files
            for f in files:
                self.folder_listbox.insert(tk.END, f)
        except Exception as e:
            messagebox.showerror("错误", f"读取文件夹失败：{e}")

    def _load_file(self, path, forced=None):
        with open(path, "rb") as f:
            if f.read(5) != b"XMUTI":
                messagebox.showerror("错误", "文件损坏或不是XMuti文件")
                return
            f.read(1)
            self.FileType = f.read(1)[0]
        ftype = forced if forced is not None else self.FileType
        if ftype == 0x01:
            with open(path, "rb") as f:
                f.read(7)
                try:
                    content = f.read().decode("utf-8")
                except UnicodeDecodeError:
                    messagebox.showerror("错误", "文本解码失败（不是有效的UTF-8）")
                    return
            self._create_text_tab(path, content)
        elif ftype in self.ColorMaps:
            with open(path, "rb") as f:
                if f.read(5) != b"XMUTI":
                    messagebox.showerror("错误", "文件损坏或不是XMuti文件")
                    return
                f.read(1)
                self.FileType = f.read(1)[0]
                pixels = f.read()[9:]
            size = self._MatchSize(len(pixels), self.AllowedSizes[ftype])
            if size is None:
                opts = "或".join(f"{s}x{s}" for s in self.AllowedSizes[ftype])
                messagebox.showerror("错误", f"不支持的图像尺寸（此版本仅支持{opts}）")
                return
            self._create_image_tab(path, ftype, size, pixels)
        elif ftype in range(0x06, 0x09 + 1):
            messagebox.showerror("错误", "此类型是保留的类型。")
        elif ftype == 0x00:
            messagebox.showerror("错误", "此类型是未定义的保留的类型。")
        else:
            messagebox.showerror("错误", "此类型是未定义的类型。")

    # ---------- 文本标签（带行号栏，仿TXTPro） ----------
    def _create_text_tab(self, file_path, content):
        if len(self.tabs_data) >= self.MAX_TABS:
            messagebox.showwarning("提示", f"标签页数量已达上限（{self.MAX_TABS}）")
            return None
        self.tab_counter += 1
        tab_frame = tk.Frame(self.notebook)
        tab_text = os.path.basename(file_path) if file_path else "新文件"
        self.notebook.add(tab_frame, text=tab_text)
        self.notebook.select(tab_frame)

        top_text_frame = tk.Frame(tab_frame)
        top_text_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        line_no = tk.Text(top_text_frame, width=4, padx=5, pady=5, state=tk.DISABLED, wrap=tk.NONE,
                          bg="#f0f0f0", fg="#666666", font=("Consolas", 10), relief=tk.FLAT)
        line_no.pack(side=tk.LEFT, fill=tk.Y)
        text_container = tk.Frame(top_text_frame)
        text_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        text_widget = tk.Text(text_container, wrap=tk.NONE, padx=5, pady=5, font=("Consolas", 10), undo=True)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_sb = tk.Scrollbar(text_container, orient=tk.VERTICAL, command=text_widget.yview)
        v_sb.pack(side=tk.RIGHT, fill=tk.Y)
        h_sb = tk.Scrollbar(tab_frame, orient=tk.HORIZONTAL, command=text_widget.xview)
        h_sb.pack(side=tk.BOTTOM, fill=tk.X)

        meta = {"file_path": file_path, "original_content": content, "text_widget": text_widget,
                "line_number_widget": line_no, "v_sb": v_sb, "h_sb": h_sb, "ftype": 0x01, "editable": True}
        self.tabs_data[tab_frame] = meta
        text_widget.config(yscrollcommand=lambda *a, tf=tab_frame: (v_sb.set(*a), self._sync_scroll(tf, *a)))
        text_widget.config(xscrollcommand=h_sb.set)
        text_widget.bind("<KeyRelease>", lambda e, tf=tab_frame: self._on_text_change(tf))
        text_widget.bind("<Button-1>", lambda e, tf=tab_frame: self._on_text_change(tf))
        text_widget.bind("<ButtonRelease-1>", lambda e: self.root.after_idle(self._update_cursor_position))
        if content:
            text_widget.insert("1.0", content)
        self._update_line_numbers(tab_frame)
        self._update_tab_title(tab_frame)
        self._update_window_title()
        return tab_frame

    # ---------- 图像标签 ----------
    def _create_image_tab(self, path, ftype, size, pixels):
        if len(self.tabs_data) >= self.MAX_TABS:
            messagebox.showwarning("提示", f"标签页数量已达上限（{self.MAX_TABS}）")
            return None
        self.tab_counter += 1
        tab_frame = tk.Frame(self.notebook)
        self.notebook.add(tab_frame, text=os.path.basename(path))
        self.notebook.select(tab_frame)
        # 可滚动视口：大的图像能在标签内横向/纵向滚动，不会溢出
        canvas = tk.Canvas(tab_frame, highlightthickness=0)
        vsb = tk.Scrollbar(tab_frame, orient=tk.VERTICAL, command=canvas.yview)
        hsb = tk.Scrollbar(tab_frame, orient=tk.HORIZONTAL, command=canvas.xview)
        canvas.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        inner = tk.Frame(canvas)
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        # 尺寸>40x40时用更小的格子（height/width必须是整数，用height=1+小字体压小）
        if size > 40:
            lopt = dict(width=1, height=1, text=" ", font=("TkDefaultFont", 2))
        else:
            lopt = dict(width=2, height=1, text="  ")
        colormap = self.ColorMaps[ftype]
        unknown = set()
        for i in range(size):
            for j in range(size):
                val = pixels[i * size + j]
                color = colormap.get(val)
                if color is None:
                    unknown.add(val)
                    color = "white"
                tk.Label(inner, bg=color, fg=color, **lopt).grid(row=i, column=j)
        self.tabs_data[tab_frame] = {"file_path": path, "ftype": ftype, "size": size, "pixels": pixels, "editable": False}
        self._update_window_title()
        if unknown:
            hexlist = ", ".join(f"0x{v:02X}" for v in sorted(unknown))
            messagebox.showwarning("警告", f"图像中存在不支持的颜色（{hexlist}），已渲染为白色。")

    # ---------- 创建文件向导 ----------
    def create_file(self):
        win = Window(self.root, "创建文件向导", width=380, height=240, placex=160, placey=90)
        vartype = tk.StringVar(value="text")
        tk.Label(win.content, text="文件类型：", bg="#f0f0f0").grid(row=0, column=0, sticky="w", padx=8, pady=8)
        tk.Radiobutton(win.content, text="文本", variable=vartype, value="text", bg="#f0f0f0").grid(row=0, column=1, sticky="w")
        tk.Radiobutton(win.content, text="图像", variable=vartype, value="image", bg="#f0f0f0").grid(row=0, column=2, sticky="w")

        tk.Label(win.content, text="图像版本：", bg="#f0f0f0").grid(row=1, column=0, sticky="w", padx=8, pady=8)
        varver = tk.StringVar()
        ver_disp = ["V1（黑白）", "V2（5色）", "V3（6色）", "V4（14色）"]
        ver_types = [0x02, 0x03, 0x04, 0x05]
        verbox = ttk.Combobox(win.content, textvariable=varver, state="readonly", width=16)
        verbox["values"] = ver_disp
        verbox.current(1); varver.set(ver_disp[1])
        verbox.grid(row=1, column=1, columnspan=2, sticky="w")

        tk.Label(win.content, text="图像大小：", bg="#f0f0f0").grid(row=2, column=0, sticky="w", padx=8, pady=8)
        varsize = tk.StringVar()
        sizebox = ttk.Combobox(win.content, textvariable=varsize, state="readonly", width=16)
        sizebox.grid(row=2, column=1, columnspan=2, sticky="w")

        def update_sizes(*_):
            idx = verbox.current()
            if idx < 0:
                return
            sizes = list(self.AllowedSizes[ver_types[idx]])
            sizebox["values"] = [f"{s}x{s}" for s in sizes]
            if sizes:
                sizebox.current(0)
            ad = "readonly" if vartype.get() == "image" else "disabled"
            verbox.config(state=ad); sizebox.config(state=ad)

        verbox.bind("<<ComboboxSelected>>", update_sizes)
        vartype.trace_add("write", update_sizes)
        update_sizes()

        def do_create():
            if vartype.get() == "image":
                ftype = ver_types[verbox.current()]
                sstr = varsize.get()
                if not sstr:
                    messagebox.showerror("错误", "请选择图像大小。")
                    return
                size = int(sstr.split("x")[0])
                savepath = filedialog.asksaveasfilename(title="保存新建的图像文件", defaultextension=".xmu",
                                                       filetypes=[("XMuti 多格式文件", "*.xmu")])  # 不含 *.xmu.bak
                if not savepath:
                    return
                with open(savepath, "wb") as f:
                    f.write(b"XMUTI\x00" + bytes([ftype]) + bytes(9) + bytes(size * size))
                win.destroy()
                self._load_file(savepath)
            else:
                savepath = filedialog.asksaveasfilename(title="保存新建的文本文件", defaultextension=".xmu",
                                                       filetypes=[("XMuti 多格式文件", "*.xmu")])
                if not savepath:
                    return
                with open(savepath, "wb") as f:
                    f.write(b"XMUTI\x00\x01")
                win.destroy()
                self._load_file(savepath)

        tk.Button(win.content, text="创建并保存...", command=do_create).grid(row=3, column=0, columnspan=3, pady=12)

    # ---------- 保存 ----------
    def save_file(self, tab_id=None):
        tab_data = self._get_tab_data(tab_id)
        if not tab_data:
            messagebox.showerror("错误", "没有活动的标签页！")
            return
        if tab_data.get("ftype") == 0x01:
            content = tab_data["text_widget"].get("1.0", tk.END + "-1c")
            path = tab_data["file_path"]
            with open(path, "wb") as f:
                f.write(b"XMUTI\x00\x01" + content.encode("utf-8"))
            tab_data["original_content"] = content
            self._update_tab_title(tab_id)
            self._update_window_title()
            messagebox.showinfo("保存成功", f"文件已保存到：{path}")
        else:
            messagebox.showinfo("提示", "图像标签（显示模式）无可保存内容。")

    # ---------- 关闭标签（右键菜单） ----------
    def close_tab(self, tab_frame):
        if tab_frame not in self.tabs_data:
            return
        if self._is_modified(tab_frame):
            r = messagebox.askyesnocancel("提示", "文件有未保存的修改，是否保存？")
            if r is True:
                self.notebook.select(tab_frame)
                self.save_file(tab_frame)
            elif r is None:
                return
        self.notebook.forget(tab_frame)
        del self.tabs_data[tab_frame]
        self._update_window_title()

    def _on_tab_right_click(self, event):
        try:
            idx = self.notebook.index(f"@{event.x},{event.y}")
            if idx == -1:
                return
        except Exception:
            return
        try:
            tab_frame = self.notebook.nametowidget(self.notebook.tabs()[idx])
        except Exception:
            return
        if tab_frame not in self.tabs_data:
            return
        self.notebook.select(tab_frame)
        ctx = tk.Menu(self.root, tearoff=0)
        ctx.add_command(label="关闭", command=lambda tf=tab_frame: self.close_tab(tf))
        try:
            ctx.tk_popup(event.x_root, event.y_root)
        finally:
            ctx.grab_release()

    # ---------- 标题 / 行号 / 状态 ----------
    def _get_tab_data(self, tab_id=None):
        if tab_id is None:
            cur = self.notebook.select()
            if not cur:
                return None
            tab_id = self.notebook.nametowidget(cur)
        if tab_id not in self.tabs_data:
            try:
                tab_id = self.notebook.nametowidget(tab_id)
            except Exception:
                return None
        return self.tabs_data.get(tab_id)

    def _is_modified(self, tab_frame):
        tab = self.tabs_data.get(tab_frame)
        if not tab or tab.get("ftype") != 0x01:
            return False
        return tab["text_widget"].get("1.0", tk.END + "-1c") != tab["original_content"]

    def _update_line_numbers(self, tab_id=None):
        tab = self._get_tab_data(tab_id)
        if not tab or tab.get("ftype") != 0x01:
            return
        text = tab["text_widget"]
        content = text.get("1.0", tk.END + "-1c")
        line_count = content.count("\n") + 1
        nums = "".join(f"{i}\n" for i in range(1, line_count + 1))
        ln = tab["line_number_widget"]
        ln.config(state=tk.NORMAL)
        ln.delete("1.0", tk.END)
        ln.insert("1.0", nums)
        ln.config(state=tk.DISABLED)
        ln.yview_moveto(text.yview()[0])

    def _sync_scroll(self, tab_frame, *args):
        tab = self.tabs_data.get(tab_frame)
        if tab:
            tab["line_number_widget"].yview_moveto(tab["text_widget"].yview()[0])

    def _on_text_change(self, tab_id=None):
        self.root.after_idle(lambda: (self._update_line_numbers(tab_id), self._update_tab_title(tab_id),
                                      self._update_window_title(), self._update_cursor_position()))

    def _update_tab_title(self, tab_ref=None):
        # tab_ref 可以是标签frame，None则取当前选中标签
        if tab_ref is None:
            cur = self.notebook.select()
            if not cur:
                return
            tab_ref = self.notebook.nametowidget(cur)
        tab = self.tabs_data.get(tab_ref)
        if not tab:
            return
        base = os.path.basename(tab.get("file_path") or "新文件")
        mod = "*" if self._is_modified(tab_ref) else ""
        try:
            self.notebook.tab(tab_ref, text=f"{mod}{base}")
        except Exception:
            pass

    def _update_window_title(self):
        tab = self._get_tab_data()
        if not tab:
            self.root.title("XMuti")
            self.status_label.config(text="")
            return
        base = os.path.basename(tab.get("file_path") or "新文件")
        mod = "*" if self._is_modified(self.notebook.nametowidget(self.notebook.select())) else ""
        self.root.title(f"XMuti - {mod}{base}")
        ftype = tab.get("ftype")
        kind = "文本" if ftype == 0x01 else self.ImageTitles.get(ftype, "图像")
        self.status_label.config(text=f"{base}  |  {kind}")

    def _update_cursor_position(self):
        self.root.after_idle(self._update_window_title)

    def _on_tab_changed(self, event):
        self._update_window_title()

    def _on_folder_file_select(self, event):
        if not self.current_folder:
            return
        sel = self.folder_listbox.curselection()
        if not sel:
            return
        path = os.path.join(self.current_folder, self.folder_listbox.get(sel[0]))
        self._load_file(path)

    # ---------- 快捷键 ----------
    def bind_shortcuts(self):
        def _save(e=None): self.save_file(); return "break"
        def _create(e=None): self.create_file(); return "break"
        def _open(e=None): self.open_file(); return "break"
        self.root.bind("<Control-s>", _save)
        self.root.bind("<Control-n>", _create)
        self.root.bind("<Control-o>", _open)

    @staticmethod
    def _MatchSize(length, allowed):
        for s in allowed:
            if length == s * s:
                return s
        return None


if __name__ == "__main__":
    r = tk.Tk()
    r.resizable(False, False)
    app = XMutiReader(r)
    app.bind_shortcuts()
    r.mainloop()
