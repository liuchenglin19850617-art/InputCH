# -*- coding: utf-8 -*-
import os
import sys
import queue
import threading
import tkinter as tk

import config
import engine
import llm_hook

try:
    import ctypes
    from ctypes import wintypes
    _HAS_WIN = True
except Exception:
    _HAS_WIN = False

# 配色（蓝皮肤）
C_BAR = "#2b7cff"
C_BG = "#ffffff"
C_INPUT = "#2b7cff"
C_TXT = "#1f1f1f"
C_IDX = "#2b7cff"
C_MUTE = "#9aa0a6"
C_HOVER = "#e8f1ff"
C_FOOT = "#f5f7fa"

PAGE_SIZE = 9
MAX_PAGES = 3
TOPN = PAGE_SIZE * MAX_PAGES


def _res(name):
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        p = os.path.join(sys._MEIPASS, name)
        if os.path.exists(p):
            return p
    return os.path.join(config.BASE_DIR, name)


class IMEBar:
    def __init__(self, root, global_mode=False):
        self.root = root
        self.global_mode = global_mode
        self.active = False
        self.pinyin = ""
        self.composition = ""
        self.candidates = []
        self.page = 0
        self.ai_text = ""
        self._target_hwnd = 0
        self._q = queue.Queue()

        root.title("InputCH")
        root.attributes("-topmost", True)
        root.overrideredirect(True)
        root.configure(bg=C_BAR)

        self._build_ui()
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        # 显式宽高，避免继承加载窗 440x130 导致候选被裁切；并置于屏幕底部中央。
        root.geometry("640x130+%d+%d" % (max(0, (sw - 640) // 2), max(0, sh - 240)))

        # 不抢焦点的扩展样式只在全局钩子真正生效时才加（本地模式需要能拿到焦点）。
        if global_mode:
            self._make_noactivate()

        self._refresh_status()
        self.refresh()

    # ---------- 界面 ----------
    def _build_ui(self):
        r = self.root

        bar = tk.Frame(r, bg=C_BAR, height=26)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        try:
            from PIL import Image, ImageTk
            img = Image.open(_res("logo.png"))
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            else:
                img = img.copy()
            px = img.load()
            for y in range(img.height):
                for x in range(img.width):
                    rr, gg, bb, aa = px[x, y]
                    if aa > 0 and rr < 24 and gg < 24 and bb < 24:
                        px[x, y] = (rr, gg, bb, 0)
            h = 18
            w = max(1, int(h * img.width / img.height))
            img = img.resize((w, h), Image.LANCZOS)
            self.logo = ImageTk.PhotoImage(img)
            tk.Label(bar, image=self.logo, bg=C_BAR).pack(side="left", padx=6)
        except Exception:
            self.logo = None
        tk.Label(bar, text="InputCH", bg=C_BAR, fg="white",
                 font=("Microsoft YaHei", 11, "bold")).pack(side="left", padx=2)
        self.act_label = tk.Label(bar, text="关", bg=C_BAR, fg="white",
                                  font=("Microsoft YaHei", 10), cursor="hand2")
        self.act_label.pack(side="left", padx=4)
        self.act_label.bind("<Button-1>", lambda e: self.set_active(not self.active))
        bar.bind("<ButtonPress-1>", self._start_drag)
        bar.bind("<B1-Motion>", self._do_drag)
        self._close_btn = tk.Label(bar, text="×", bg=C_BAR, fg="white",
                                   font=("Microsoft YaHei", 13), cursor="hand2")
        self._close_btn.pack(side="right", padx=8)
        self._close_btn.bind("<Button-1>", lambda e: self.root.destroy())

        inp = tk.Frame(r, bg=C_BG, height=36)
        inp.pack(fill="x")
        inp.pack_propagate(False)
        self.comp_label = tk.Label(inp, text="", bg=C_BG, fg=C_TXT,
                                   font=("Microsoft YaHei", 17, "bold"), anchor="w")
        self.comp_label.pack(side="left", padx=(10, 0))
        self.py_label = tk.Label(inp, text="", bg=C_BG, fg=C_INPUT,
                                 font=("Microsoft YaHei", 17), anchor="w")
        self.py_label.pack(side="left")

        self.cand_frame = tk.Frame(r, bg=C_BG, height=42)
        self.cand_frame.pack(fill="x")
        self.cand_frame.pack_propagate(False)

        foot = tk.Frame(r, bg=C_FOOT, height=26)
        foot.pack(fill="x")
        foot.pack_propagate(False)
        self.prev_btn = tk.Button(foot, text="上页", bg=C_FOOT, fg=C_IDX, bd=0,
                                  font=("Microsoft YaHei", 10), takefocus=0, command=self._page_prev)
        self.prev_btn.pack(side="left", padx=4)
        self.page_label = tk.Label(foot, text="", bg=C_FOOT, fg=C_MUTE,
                                   font=("Microsoft YaHei", 10))
        self.page_label.pack(side="left")
        self.next_btn = tk.Button(foot, text="下页", bg=C_FOOT, fg=C_IDX, bd=0,
                                  font=("Microsoft YaHei", 10), takefocus=0, command=self._page_next)
        self.next_btn.pack(side="left", padx=4)

        if llm_hook.is_available():
            tk.Button(foot, text="AI续写", bg=C_FOOT, fg=C_IDX, bd=0,
                      font=("Microsoft YaHei", 10), takefocus=0,
                      command=self._ai_suggest).pack(side="left", padx=(8, 0))
            self.ai_label = tk.Label(foot, text="", bg=C_FOOT, fg=C_TXT,
                                     font=("Microsoft YaHei", 10), cursor="hand2")
            self.ai_label.pack(side="left", padx=4)
            self.ai_label.bind("<Button-1>", lambda e: self._append_ai())

        self.status_label = tk.Label(foot, text="", bg=C_FOOT, fg=C_MUTE,
                                     font=("Microsoft YaHei", 9))
        self.status_label.pack(side="right", padx=8)

        tk.Label(foot, text="数字选词 空格首选 回车发送 Esc清空  按 ` 或点状态条开/关", bg=C_FOOT,
                 fg=C_MUTE, font=("Microsoft YaHei", 9)).pack(side="right", padx=4)

    def _make_noactivate(self):
        if not _HAS_WIN:
            return
        try:
            GWL_EXSTYLE = -20
            WS_EX_NOACTIVATE = 0x08000000
            WS_EX_TOOLWINDOW = 0x00000080
            hwnd = self.root.winfo_id()
            user32 = ctypes.windll.user32
            cur = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE, cur | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW)
        except Exception:
            pass

    # ---------- 拖动 ----------
    def _start_drag(self, e):
        self._dx, self._dy = e.x_root, e.y_root

    def _do_drag(self, e):
        x = self.root.winfo_x() + (e.x_root - self._dx)
        y = self.root.winfo_y() + (e.y_root - self._dy)
        self.root.geometry("+%d+%d" % (x, y))
        self._dx, self._dy = e.x_root, e.y_root

    # ---------- 核心动作（钩子与本地模式共用） ----------
    def feed_char(self, ch):
        if ch.isalpha():
            self.pinyin += ch.lower()
            self.page = 0
            self.refresh()

    def do_backspace(self):
        if self.pinyin:
            self.pinyin = self.pinyin[:-1]
            self.page = 0
        elif self.composition:
            self.composition = self.composition[:-1]
        self.refresh()

    def do_space(self):
        if self.candidates:
            self._select_global(self.page * PAGE_SIZE + 0)
        elif self.composition:
            self.do_commit()

    def do_select(self, idx_in_page):
        self._select_global(self.page * PAGE_SIZE + idx_in_page)

    def _select_global(self, gi):
        if gi < 0 or gi >= len(self.candidates):
            return
        self.composition += self.candidates[gi]["text"]
        self.pinyin = ""
        self.page = 0
        self.refresh()

    def do_clear(self):
        if self.pinyin:
            self.pinyin = ""
        else:
            self.composition = ""
        self.page = 0
        self.refresh()

    def do_commit(self):
        if not self.composition:
            return
        if self.global_mode:
            self._send_text(self.composition)
            self.status_label.configure(text="已发送")
        else:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.composition)
            self.status_label.configure(text="已复制")
        self.composition = ""
        self.refresh()

    def set_active(self, on):
        self.active = on
        self.act_label.configure(text="开" if on else "关")
        if on and _HAS_WIN:
            try:
                self._target_hwnd = ctypes.windll.user32.GetForegroundWindow()
            except Exception:
                self._target_hwnd = 0

    # ---------- 线程安全桥（钩子线程 -> 主线程） ----------
    def enqueue(self, fn):
        self._q.put(fn)

    def start_pump(self, root):
        def drain():
            try:
                while True:
                    fn = self._q.get_nowait()
                    fn()
            except queue.Empty:
                pass
            root.after(25, drain)
        root.after(25, drain)

    # ---------- 键盘（本地模式） ----------
    def _on_key(self, e):
        k, ch = e.keysym, e.char
        if k == "BackSpace":
            self.do_backspace()
        elif k == "Return":
            self.do_commit()
        elif k == "Escape":
            self.do_clear()
        elif k == "space" or ch == " ":
            self.do_space()
        elif k in ("1", "2", "3", "4", "5", "6", "7", "8", "9"):
            self.do_select(int(k) - 1)
        elif k in ("Prior", "Next"):
            self._page(-1 if k == "Prior" else 1)
        elif ch and ch.isalpha():
            self.feed_char(ch)
        else:
            return
        return "break"

    # ---------- 显示 ----------
    def refresh(self):
        self.py_label.configure(text=self.pinyin)
        self.comp_label.configure(text=self.composition)
        if self.pinyin:
            self.candidates = engine.decode(self.pinyin, topk=TOPN)
        else:
            self.candidates = []
            self.ai_text = ""
            if getattr(self, "ai_label", None):
                self.ai_label.configure(text="")
        self._render_candidates()
        if not self.global_mode:
            self.root.focus_set()

    def _render_candidates(self):
        for w in self.cand_frame.winfo_children():
            w.destroy()
        total = len(self.candidates)
        pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
        if self.page >= pages:
            self.page = pages - 1
        if self.page < 0:
            self.page = 0
        self.page_label.configure(text="第 %d/%d 页" % (self.page + 1, pages))
        self.prev_btn.configure(state="normal" if self.page > 0 else "disabled")
        self.next_btn.configure(state="normal" if self.page < pages - 1 else "disabled")

        if not self.pinyin:
            tk.Label(self.cand_frame, text="输入拼音 如 nihao（z/zh 模糊音 nh 简拼）",
                     bg=C_BG, fg=C_MUTE, font=("Microsoft YaHei", 13)).pack(side="left", padx=10)
            return

        start = self.page * PAGE_SIZE
        for i in range(PAGE_SIZE):
            gi = start + i
            if gi >= total:
                break
            cand = self.candidates[gi]
            cell = tk.Frame(self.cand_frame, bg=C_BG, cursor="hand2")
            cell.pack(side="left", padx=2, pady=4)
            idx = tk.Label(cell, text=str(i + 1), bg=C_BG, fg=C_IDX, font=("Microsoft YaHei", 10))
            idx.pack(side="left", padx=(4, 1))
            word = tk.Label(cell, text=cand["text"], bg=C_BG, fg=C_TXT, font=("Microsoft YaHei", 15))
            word.pack(side="left", padx=(0, 6))
            cell.bind("<Enter>", lambda e, c=cell: c.configure(bg=C_HOVER))
            cell.bind("<Leave>", lambda e, c=cell: c.configure(bg=C_BG))
            cell.bind("<Button-1>", lambda e, gi=gi: self._select_global(gi))

    def _page(self, d):
        self.page += d
        self._render_candidates()
        if not self.global_mode:
            self.root.focus_set()

    def _page_prev(self):
        self._page(-1)

    def _page_next(self):
        self._page(1)

    # ---------- AI ----------
    def _ai_suggest(self):
        ctx = self.composition + self.pinyin
        if not ctx:
            return
        self.status_label.configure(text="AI 思考中")
        try:
            sug = llm_hook.suggest(ctx)
        except Exception:
            sug = ""
        if sug:
            self.ai_text = sug
            self.ai_label.configure(text=sug)
            self.status_label.configure(text="")
        else:
            self.ai_label.configure(text="")
            self.status_label.configure(text="AI 无返回")

    def _append_ai(self):
        if self.ai_text:
            self.composition += self.ai_text
            self.ai_text = ""
            self.ai_label.configure(text="")
            self.refresh()

    # ---------- 全局注入 ----------
    def _send_text(self, s):
        if not s or not _HAS_WIN:
            return
        try:
            user32 = ctypes.windll.user32
            try:
                imm32 = ctypes.windll.imm32
            except Exception:
                imm32 = None
            try:
                kernel32 = ctypes.windll.kernel32
            except Exception:
                kernel32 = None

            # 目标窗口：当前前台（用户正输入的应用）。钩子不抢焦点，前台仍是目标。
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                hwnd = self._target_hwnd
            if not hwnd:
                return

            # 允许本进程置前，避免被前台锁拦住
            try:
                user32.AllowSetForegroundWindow(0xFFFFFFFF)
            except Exception:
                pass

            # 跨线程附着，确保 SendInput 落到目标线程（不同进程的编辑框）
            attached = False
            cur_pid = wintypes.DWORD()
            my_tid = None
            try:
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(cur_pid))
                my_tid = kernel32.GetCurrentThreadId()
                if cur_pid.value and my_tid:
                    attached = bool(user32.AttachThreadInput(cur_pid.value, my_tid, True))
            except Exception:
                pass

            # 临时摘掉目标窗口的 IME（讯飞/搜狗等），否则注入的中文会被其吞掉
            old_ctx = None
            if imm32 is not None:
                try:
                    old_ctx = imm32.ImmAssociateContext(hwnd, 0)
                except Exception:
                    old_ctx = None

            try:
                try:
                    user32.SetForegroundWindow(hwnd)
                    user32.SetFocus(hwnd)
                except Exception:
                    pass

                INPUT_KEYBOARD = 1
                KEYEVENTF_UNICODE = 0x4
                KEYEVENTF_KEYUP = 0x2

                class KBI(ctypes.Structure):
                    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                                ("dwExtraInfo", ctypes.c_ulong)]

                class INPUT(ctypes.Structure):
                    _fields_ = [("type", wintypes.DWORD), ("ki", KBI)]

                inputs = []
                for ch in s:
                    d = KBI(0, ord(ch), KEYEVENTF_UNICODE, 0, 0)
                    u = KBI(0, ord(ch), KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0, 0)
                    inputs.append(INPUT(INPUT_KEYBOARD, d))
                    inputs.append(INPUT(INPUT_KEYBOARD, u))
                arr = (INPUT * len(inputs))(*inputs)
                user32.SendInput(len(inputs), arr, ctypes.sizeof(INPUT))
            finally:
                if imm32 is not None and old_ctx is not None:
                    try:
                        imm32.ImmAssociateContext(hwnd, old_ctx)
                    except Exception:
                        pass
                if attached:
                    try:
                        user32.AttachThreadInput(cur_pid.value, my_tid, False)
                    except Exception:
                        pass
            self.status_label.configure(text="已发送")
        except Exception:
            try:
                self.status_label.configure(text="发送失败")
            except Exception:
                pass

    # ---------- 状态 ----------
    def _refresh_status(self):
        s = engine.info()
        ext = s.get("chars_dict", 0)
        py = s.get("has_pinyin")
        py_txt = "pypinyin" if py else ("开源字库%s字" % ext if ext else "内置表")
        self.status_label.configure(text="词库%s 索引%s %s" % (
            s.get("words", "-"), s.get("indexed_phrases", "-"), py_txt))


# ---------- 全局键盘钩子（B 方案） ----------
class GlobalHook:
    def __init__(self, bar, root):
        self.bar = bar
        self.root = root
        self.vk_toggle = 0xC0  # 反引号 ` 键切换开关
        self._hook = None
        self._thread = None

    def start(self):
        if not _HAS_WIN:
            raise RuntimeError("no windows api")
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        HOOKPROC = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)

        class KBDLLHOOKSTRUCT(ctypes.Structure):
            _fields_ = [("vk", wintypes.DWORD), ("scan", wintypes.DWORD),
                        ("flags", wintypes.DWORD), ("time", wintypes.DWORD),
                        ("dwExtraInfo", ctypes.c_ulong)]

        WH_KEYBOARD_LL = 0x0D
        WM_KEYDOWN = 0x0100

        def ctrl_alt_down():
            VK_CONTROL = 0x11
            VK_MENU = 0x12
            return (user32.GetAsyncKeyState(VK_CONTROL) & 0x8000) or \
                   (user32.GetAsyncKeyState(VK_MENU) & 0x8000)

        def callback(nCode, wParam, lParam):
            try:
                if nCode >= 0 and wParam == WM_KEYDOWN:
                    ks = KBDLLHOOKSTRUCT.from_address(lParam)
                    vk = ks.vk
                    if vk == self.vk_toggle:
                        self.bar.enqueue(lambda: self.bar.set_active(not self.bar.active))
                        return 1
                    if self.bar.active and not ctrl_alt_down():
                        if 65 <= vk <= 90:
                            self.bar.enqueue(lambda c=chr(vk).lower(): self.bar.feed_char(c))
                            return 1
                        if 48 <= vk <= 57:
                            self.bar.enqueue(lambda n=vk - 48: self.bar.do_select(n - 1))
                            return 1
                        if vk == 32:
                            self.bar.enqueue(self.bar.do_space)
                            return 1
                        if vk == 8:
                            self.bar.enqueue(self.bar.do_backspace)
                            return 1
                        if vk == 13:
                            self.bar.enqueue(self.bar.do_commit)
                            return 1
                        if vk == 27:
                            self.bar.enqueue(self.bar.do_clear)
                            return 1
            except Exception:
                pass
            return user32.CallNextHookEx(0, nCode, wParam, lParam)

        self._callback = HOOKPROC(callback)
        # 低层钩子(WH_KEYBOARD_LL)必须用 NULL 模块句柄；传 EXE 句柄会返回 NULL 导致安装失败。
        self._hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, self._callback, 0, 0)
        if not self._hook:
            err = ctypes.GetLastError()
            raise RuntimeError("SetWindowsHookEx failed, GetLastError=%d" % err)

        def loop():
            msg = wintypes.MSG()
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))

        self._thread = threading.Thread(target=loop, daemon=True)
        self._thread.start()

    def stop(self):
        if self._hook and _HAS_WIN:
            try:
                ctypes.windll.user32.UnhookWindowsHookEx(self._hook)
            except Exception:
                pass


def main():
    try:
        # 单一 Tk 根窗口，且全程不 withdraw：Windows 上 overrideredirect + withdraw/deiconify
        # 组合常导致窗口永久不可见。加载内容直接画在根窗上，构建完清空再画候选条。
        root = tk.Tk()
        root.title("InputCH")
        root.geometry("440x130")
        lbl = tk.Label(root, text="正在构建拼音索引 首次较慢 之后秒开",
                       font=("Microsoft YaHei", 13))
        lbl.pack(expand=True)
        root.update()

        state = {}
        def worker():
            try:
                state["stats"] = engine.build()
            except Exception as e:
                state["error"] = e
        tw = threading.Thread(target=worker, daemon=True)
        tw.start()
        while tw.is_alive():
            root.update()
            root.after(50)

        if "error" in state:
            tk.messagebox.showerror("启动失败", str(state["error"]))
            sys.exit(1)

        # 清空加载控件，在同一（始终可见的）根窗上构建候选条
        for w in root.winfo_children():
            w.destroy()

        bar = IMEBar(root, global_mode=True)
        bar.start_pump(root)
        hook = None
        try:
            hook = GlobalHook(bar, root)
            hook.start()
            bar._make_noactivate()  # 钩子生效才加“不抢焦点”样式
        except Exception as e:
            bar.global_mode = False
            try:
                root.focus_force()
                root.bind("<Key>", bar._on_key)
                root.bind("<FocusIn>", lambda ev: root.focus_set())
                bar.status_label.configure(text="钩子失败 本地模式")
            except Exception:
                pass
            try:
                tk.messagebox.showwarning(
                    "InputCH",
                    "全局键盘钩子安装失败，已退回本地模式（在候选条窗口内输入，回车复制到剪贴板）。\n错误：%s" % e)
            except Exception:
                pass

        # 默认开启：开箱即用，无需先按反引号。反引号 ` 或点状态条可随时关。
        try:
            bar.set_active(True)
        except Exception:
            pass

        root.update()

        def _cleanup():
            if hook:
                hook.stop()

        import atexit
        atexit.register(_cleanup)
        root.mainloop()
    except Exception:
        import traceback
        try:
            w = tk.Tk()
            w.withdraw()
            tk.messagebox.showerror("InputCH 启动错误", traceback.format_exc()[-3000:])
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
