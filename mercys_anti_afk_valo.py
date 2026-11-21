"""
Mercy's Anti Afk Valo  (Windows only)
Glass-theme GUI. Run as Administrator.

Run:    pip install keyboard
        python mercys_anti_afk_valo.py
Or double-click build_exe.bat to make MercysAntiAFKValo.exe
"""
import ctypes
import math
import os
import random
import sys
import threading
import time
import tkinter as tk

import keyboard

APP_NAME = "Mercy's Anti Afk Valo"
ICON_FILE = "mercys_anti_afk_valo.ico"


def resource_path(name):
    """Find a bundled file (works both as .py and as PyInstaller .exe)."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)

# =====================================================================
#  LOW LEVEL INPUT (SendInput with scan codes)
# =====================================================================
SC = {"w": 0x11, "a": 0x1E, "s": 0x1F, "d": 0x20, "space": 0x39, "ctrl": 0x1D}
KEYEVENTF_SCANCODE, KEYEVENTF_KEYUP = 0x0008, 0x0002
MOUSEEVENTF_MOVE, MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP = 0x0001, 0x0002, 0x0004
PUL = ctypes.POINTER(ctypes.c_ulong)


class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]


class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong), ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_ushort)]


class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong), ("dwExtraInfo", PUL)]


class InputUnion(ctypes.Union):
    _fields_ = [("ki", KeyBdInput), ("mi", MouseInput), ("hi", HardwareInput)]


class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("ii", InputUnion)]


def _send(inp):
    ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))


def _key(name, flags):
    extra = ctypes.c_ulong(0)
    ii = InputUnion()
    ii.ki = KeyBdInput(0, SC[name], KEYEVENTF_SCANCODE | flags, 0, ctypes.pointer(extra))
    _send(Input(1, ii))


def key_down(n): _key(n, 0)
def key_up(n): _key(n, KEYEVENTF_KEYUP)


def mouse(flags, dx=0, dy=0):
    extra = ctypes.c_ulong(0)
    ii = InputUnion()
    ii.mi = MouseInput(dx, dy, 0, flags, 0, ctypes.pointer(extra))
    _send(Input(0, ii))


# =====================================================================
#  ANTI-AFK LOGIC
# =====================================================================
cfg = {"min_gap": 0.4, "max_gap": 2.5, "min_hold": 0.15, "max_hold": 1.2, "aim_range": 400}
enabled = {k: True for k in
           ["forward", "left", "back", "right", "jump", "crouch", "fire", "aim"]}

running = threading.Event()
quit_flag = threading.Event()
log_queue = []


def hold(name):
    key_down(name)
    time.sleep(random.uniform(cfg["min_hold"], cfg["max_hold"]))
    key_up(name)


def act_fire():
    for _ in range(random.randint(1, 4)):
        mouse(MOUSEEVENTF_LEFTDOWN)
        time.sleep(random.uniform(0.05, 0.18))
        mouse(MOUSEEVENTF_LEFTUP)
        time.sleep(random.uniform(0.05, 0.2))


def act_aim():
    r = int(cfg["aim_range"])
    tx, ty = random.randint(-r, r), random.randint(-r // 5, r // 5)
    steps = random.randint(8, 20)
    for _ in range(steps):
        mouse(MOUSEEVENTF_MOVE, tx // steps, ty // steps)
        time.sleep(random.uniform(0.005, 0.02))


ACTIONS = {
    "forward": lambda: hold("w"), "left": lambda: hold("a"),
    "back": lambda: hold("s"), "right": lambda: hold("d"),
    "jump": lambda: hold("space"), "crouch": lambda: hold("ctrl"),
    "fire": act_fire, "aim": act_aim,
}


def release_all():
    for k in SC:
        key_up(k)
    mouse(MOUSEEVENTF_LEFTUP)


def worker():
    history = []
    while not quit_flag.is_set():
        if not running.is_set():
            time.sleep(0.1)
            continue
        active = [a for a in ACTIONS if enabled[a]]
        if not active:
            time.sleep(0.2)
            continue
        # never repeat the last action (and avoid the last 2 when possible)
        pool = [a for a in active if a not in history[-2:]] \
            or [a for a in active if not history or a != history[-1]] \
            or active
        choice = random.choice(pool)
        history = (history + [choice])[-5:]
        log_queue.append(choice)
        ACTIONS[choice]()
        lo, hi = sorted((cfg["min_gap"], cfg["max_gap"]))
        end = time.time() + random.uniform(lo, hi)
        while time.time() < end and running.is_set():
            time.sleep(0.05)
    release_all()


# =====================================================================
#  GLASS THEME
# =====================================================================
W, H = 400, 690
ACCENT, ACCENT_LIGHT = "#8b5cf6", "#a78bfa"
CYAN, ROSE, GREEN = "#67e8f9", "#f43f5e", "#34d399"
TXT, TXT_DIM, TXT_FAINT = "#f1f0ff", "#a5a4c8", "#6a6990"
GLASS_EDGE, GLASS_SHEEN = "#3f3e6a", "#5a5994"
TRACK, CHIP_OFF, CHIP_OFF_EDGE = "#2c2b50", "#25244a", "#3a3963"

CARDS = {
    "status":  (20, 96, 380, 196, 22),
    "hotkey":  (20, 210, 380, 268, 18),
    "timing":  (20, 282, 380, 490, 22),
    "actions": (20, 504, 380, 622, 22),
}

TX1, TX2 = 150, 300   # slider track x-range
SLIDERS = [  # label, key, min, max, integer, y
    ("Min gap", "min_gap", 0.1, 5, False, 336),
    ("Max gap", "max_gap", 0.5, 10, False, 370),
    ("Min hold", "min_hold", 0.05, 2, False, 404),
    ("Max hold", "max_hold", 0.1, 3, False, 438),
    ("Aim range (px)", "aim_range", 50, 1000, True, 472),
]
CHIP_NAMES = ["forward", "left", "back", "right", "jump", "crouch", "fire", "aim"]


def bake_rows():
    """Pre-render the glass background (gradient + glow orbs + frosted cards)
    at half resolution. Returns rows of hex colours."""
    hw, hh = W // 2, H // 2
    top, bot = (11, 14, 31), (37, 18, 58)
    orbs = [  # x, y, radius, colour, strength (half-res coords)
        (150, 55, 80, (124, 58, 237), 0.60),
        (25, 270, 75, (6, 182, 212), 0.42),
        (170, 215, 55, (236, 72, 153), 0.30),
        (60, 160, 60, (59, 130, 246), 0.20),
    ]
    cx = [[math.exp(-((x - o[0]) / o[2]) ** 2) * o[4] for x in range(hw)] for o in orbs]
    cy = [[math.exp(-((y - o[1]) / o[2]) ** 2) for y in range(hh)] for o in orbs]
    cards = [(a // 2, b // 2, c // 2, d // 2, r // 2) for (a, b, c, d, r) in CARDS.values()]

    rows = []
    for y in range(hh):
        t = y / hh
        br = top[0] + (bot[0] - top[0]) * t
        bg = top[1] + (bot[1] - top[1]) * t
        bb = top[2] + (bot[2] - top[2]) * t

        span, tint = None, 0.0
        for (x1, y1, x2, y2, r) in cards:
            if y1 <= y < y2:
                inset = 0.0
                if y < y1 + r:
                    d = y1 + r - y
                    inset = r - math.sqrt(max(r * r - d * d, 0))
                elif y >= y2 - r:
                    d = y - (y2 - r) + 1
                    inset = r - math.sqrt(max(r * r - d * d, 0))
                span = (x1 + inset, x2 - inset)
                tint = 0.045 + 0.085 * (1 - (y - y1) / (y2 - y1))
                break

        row = []
        for x in range(hw):
            r_, g_, b_ = br, bg, bb
            for i, o in enumerate(orbs):
                f = cx[i][x] * cy[i][y]
                if f > 0.004:
                    col = o[3]
                    r_ += (col[0] - r_) * f
                    g_ += (col[1] - g_) * f
                    b_ += (col[2] - b_) * f
            if span and span[0] <= x < span[1]:
                r_ += (255 - r_) * tint
                g_ += (255 - g_) * tint
                b_ += (255 - b_) * tint
            row.append("#%02x%02x%02x" % (int(r_), int(g_), int(b_)))
        rows.append(" ".join(row))
    return rows


def rr_pts(x1, y1, x2, y2, r):
    return [x1 + r, y1, x1 + r, y1, x2 - r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
            x2, y1 + r, x2, y2 - r, x2, y2 - r, x2, y2, x2 - r, y2, x2 - r, y2,
            x1 + r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y2 - r, x1, y1 + r,
            x1, y1 + r, x1, y1]


def dark_titlebar(root):
    try:
        root.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        one = ctypes.c_int(1)
        for attr in (20, 19):  # immersive dark mode
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(one), 4)
        cap = ctypes.c_int(0x001F0E0B)  # caption colour (BGR) = #0b0e1f
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(cap), 4)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 34, ctypes.byref(cap), 4)
    except Exception:
        pass


# =====================================================================
#  APP
# =====================================================================
class App:
    def __init__(self, root):
        self.root = root
        self.hotkey = "f8"
        self.hotkey_handle = None
        self.capturing = False
        self.drag = None
        self.hits = []

        root.title(APP_NAME)
        root.geometry(f"{W}x{H}")
        root.resizable(False, False)
        root.configure(bg="#0b0e1f")
        root.attributes("-topmost", True)
        root.attributes("-alpha", 0.97)
        try:
            root.iconbitmap(resource_path(ICON_FILE))
        except Exception:
            pass
        dark_titlebar(root)

        self.c = tk.Canvas(root, width=W, height=H, highlightthickness=0, bd=0, bg="#0b0e1f")
        self.c.pack()

        small = tk.PhotoImage(width=W // 2, height=H // 2)
        small.put(" ".join("{%s}" % r for r in bake_rows()))
        self.bg = small.zoom(2, 2)
        self.c.create_image(0, 0, image=self.bg, anchor="nw")

        self.build_static()
        self.draw_status()
        self.draw_button()
        self.draw_hotkey()
        for s in SLIDERS:
            self.draw_slider(s)
        for i, n in enumerate(CHIP_NAMES):
            self.draw_chip(i, n)

        self.c.bind("<Button-1>", self.on_press)
        self.c.bind("<B1-Motion>", self.on_motion)
        self.c.bind("<Motion>", self.on_motion)
        self.c.bind("<ButtonRelease-1>", lambda e: setattr(self, "drag", None))

        self.bind_hotkey()
        self.poll()
        root.protocol("WM_DELETE_WINDOW", self.close)

    # ---------- helpers ----------
    def rr(self, x1, y1, x2, y2, r, tag, **kw):
        return self.c.create_polygon(rr_pts(x1, y1, x2, y2, r), smooth=True, tags=tag, **kw)

    def add_hit(self, box, kind, data):
        self.hits.append((box, kind, data))

    # ---------- static layer ----------
    def build_static(self):
        c = self.c
        c.create_text(200, 32, text="MERCY’S", fill=CYAN, font=("Segoe UI Semibold", 10))
        c.create_text(200, 60, text="Anti AFK Valo", fill=TXT, font=("Segoe UI", 24, "bold"))

        for (x1, y1, x2, y2, r) in CARDS.values():
            self.rr(x1, y1, x2, y2, r, "card", fill="", outline=GLASS_EDGE)
            c.create_line(x1 + r, y1 + 1, x2 - r, y1 + 1, fill=GLASS_SHEEN)

        c.create_text(42, 304, text="TIMING (SECONDS)", fill=TXT_FAINT,
                      font=("Segoe UI", 8, "bold"), anchor="w")
        c.create_text(42, 524, text="ACTIONS", fill=TXT_FAINT,
                      font=("Segoe UI", 8, "bold"), anchor="w")

        self.last = c.create_text(200, 646, text="Last action: -", fill=TXT_DIM,
                                  font=("Segoe UI", 10))
        c.create_text(200, 668, text="Use in Range / custom game  •  Run as Admin",
                      fill=TXT_FAINT, font=("Segoe UI", 8))

        self.add_hit((40, 146, 360, 184), "click", self.toggle)
        self.add_hit((270, 224, 358, 254), "click", self.change_hotkey)
        for s in SLIDERS:
            self.add_hit((TX1 - 12, s[5] - 14, TX2 + 12, s[5] + 14), "slider", s)
        for i, n in enumerate(CHIP_NAMES):
            x1, y1, x2, y2 = self.chip_box(i)
            self.add_hit((x1, y1, x2, y2), "click", lambda n=n: self.toggle_chip(n))

    # ---------- dynamic pieces ----------
    def draw_status(self):
        c = self.c
        c.delete("status")
        on = running.is_set()
        col = GREEN if on else "#fb7185"
        glow = "#164e3f" if on else "#5a2340"
        c.create_oval(36, 112, 60, 136, fill=glow, outline="", tags="status")
        c.create_oval(42, 118, 54, 130, fill=col, outline="", tags="status")
        c.create_text(70, 124, text="RUNNING" if on else "STOPPED", fill=col,
                      font=("Segoe UI", 15, "bold"), anchor="w", tags="status")
        c.create_text(360, 124, text=f"{self.hotkey.upper()} to toggle", fill=TXT_FAINT,
                      font=("Segoe UI", 9), anchor="e", tags="status")

    def draw_button(self):
        c = self.c
        c.delete("btn")
        on = running.is_set()
        fill = ROSE if on else ACCENT
        edge = "#fda4af" if on else ACCENT_LIGHT
        self.rr(40, 146, 360, 184, 19, "btn", fill=fill, outline=edge)
        c.create_line(58, 149, 342, 149, fill=edge, tags="btn")
        c.create_text(200, 165, text="Stop" if on else "Start", fill="white",
                      font=("Segoe UI", 12, "bold"), tags="btn")

    def draw_hotkey(self):
        c = self.c
        c.delete("hk")
        c.create_text(42, 239, text="Hotkey", fill=TXT_DIM, font=("Segoe UI", 10),
                      anchor="w", tags="hk")
        self.rr(110, 224, 230, 254, 15, "hk", fill=CHIP_OFF, outline=CHIP_OFF_EDGE)
        label = "press a key..." if self.capturing else self.hotkey.upper()
        c.create_text(170, 239, text=label, fill=CYAN if self.capturing else TXT,
                      font=("Segoe UI", 10, "bold"), tags="hk")
        self.rr(270, 224, 358, 254, 15, "hk", fill=CHIP_OFF, outline=ACCENT)
        c.create_text(314, 239, text="Change", fill=ACCENT_LIGHT,
                      font=("Segoe UI", 10, "bold"), tags="hk")

    def draw_slider(self, s):
        label, key, lo, hi, integer, y = s
        c = self.c
        tag = f"sl_{key}"
        c.delete(tag)
        v = cfg[key]
        f = (v - lo) / (hi - lo)
        kx = TX1 + max(0, min(1, f)) * (TX2 - TX1)
        c.create_text(42, y, text=label, fill=TXT_DIM, font=("Segoe UI", 9),
                      anchor="w", tags=tag)
        c.create_line(TX1, y, TX2, y, fill=TRACK, width=5, capstyle="round", tags=tag)
        c.create_line(TX1, y, kx, y, fill=ACCENT, width=5, capstyle="round", tags=tag)
        c.create_oval(kx - 13, y - 13, kx + 13, y + 13, fill="#3a2d78", outline="", tags=tag)
        c.create_oval(kx - 8, y - 8, kx + 8, y + 8, fill="white", outline=ACCENT_LIGHT,
                      width=2, tags=tag)
        c.create_text(358, y, text=str(v), fill=TXT, font=("Segoe UI", 9, "bold"),
                      anchor="e", tags=tag)

    @staticmethod
    def chip_box(i):
        col, row = i % 4, i // 4
        x1 = 40 + col * 82
        y1 = 540 + row * 38
        return x1, y1, x1 + 74, y1 + 30

    def draw_chip(self, i, name):
        tag = f"chip_{name}"
        self.c.delete(tag)
        x1, y1, x2, y2 = self.chip_box(i)
        on = enabled[name]
        self.rr(x1, y1, x2, y2, 15, tag, fill="#5b3fd6" if on else CHIP_OFF,
                outline=ACCENT_LIGHT if on else CHIP_OFF_EDGE)
        self.c.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=name.capitalize(),
                           fill="white" if on else TXT_FAINT,
                           font=("Segoe UI Semibold", 9), tags=tag)

    # ---------- interaction ----------
    def hit_test(self, x, y):
        for box, kind, data in self.hits:
            if box[0] <= x <= box[2] and box[1] <= y <= box[3]:
                return kind, data
        return None, None

    def on_press(self, e):
        kind, data = self.hit_test(e.x, e.y)
        if kind == "click":
            data()
        elif kind == "slider":
            self.drag = data
            self.set_slider(data, e.x)

    def on_motion(self, e):
        if self.drag and (e.state & 0x100):
            self.set_slider(self.drag, e.x)
            return
        kind, _ = self.hit_test(e.x, e.y)
        self.c.config(cursor="hand2" if kind else "")

    def set_slider(self, s, x):
        label, key, lo, hi, integer, y = s
        f = min(1.0, max(0.0, (x - TX1) / (TX2 - TX1)))
        v = lo + f * (hi - lo)
        cfg[key] = int(round(v)) if integer else round(v, 2)
        self.draw_slider(s)

    def toggle_chip(self, name):
        enabled[name] = not enabled[name]
        self.draw_chip(CHIP_NAMES.index(name), name)

    # ---------- hotkey ----------
    def bind_hotkey(self):
        if self.hotkey_handle is not None:
            keyboard.remove_hotkey(self.hotkey_handle)
        self.hotkey_handle = keyboard.add_hotkey(
            self.hotkey, lambda: self.root.after(0, self.toggle))

    def change_hotkey(self):
        if self.capturing:
            return
        self.capturing = True
        self.draw_hotkey()

        def grab():
            k = keyboard.read_key()
            time.sleep(0.2)
            self.root.after(0, lambda: self.set_hotkey(k))
        threading.Thread(target=grab, daemon=True).start()

    def set_hotkey(self, k):
        self.hotkey = k
        self.capturing = False
        self.bind_hotkey()
        self.draw_hotkey()
        self.draw_status()

    # ---------- run / stop ----------
    def toggle(self):
        if running.is_set():
            running.clear()
            time.sleep(0.05)
            release_all()
        else:
            running.set()
        self.draw_status()
        self.draw_button()

    def poll(self):
        while log_queue:
            self.c.itemconfig(self.last, text=f"Last action: {log_queue.pop(0)}")
        self.root.after(100, self.poll)

    def close(self):
        running.clear()
        quit_flag.set()
        time.sleep(0.1)
        release_all()
        self.root.destroy()


if __name__ == "__main__":
    threading.Thread(target=worker, daemon=True).start()
    root = tk.Tk()
    App(root)
    root.mainloop()
