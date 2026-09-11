"""Wavish navy + gold visual theme."""

from __future__ import annotations

from typing import Callable

import tkinter as tk
import tkinter.font as tkfont

# Navy palette with gold trim
BG = "#071526"
SURFACE = "#0D2138"
SURFACE_RAISED = "#122A45"
INPUT_BG = "#0A1C30"
BORDER = "#1E3A5F"
GOLD = "#D4AF37"
GOLD_BRIGHT = "#E8C547"
GOLD_DIM = "#8B6914"
TEXT = "#E8EDF4"
TEXT_MUTED = "#8FA3BF"
TEXT_DIM = "#5C7290"
DANGER = "#C45C5C"
SUCCESS = "#4CAF82"

FONT_FAMILY = "Segoe UI"
FONT_TITLE = (FONT_FAMILY, 18, "bold")
FONT_HEADING = (FONT_FAMILY, 10, "bold")
FONT_BODY = (FONT_FAMILY, 10)
FONT_SMALL = (FONT_FAMILY, 9)
FONT_MONO = ("Consolas", 9)


def apply_root_style(root: tk.Tk) -> None:
    root.configure(bg=BG)


def card(parent: tk.Widget, **kwargs) -> tk.Frame:
    frame = tk.Frame(
        parent,
        bg=SURFACE,
        highlightbackground=BORDER,
        highlightthickness=1,
        **kwargs,
    )
    return frame


class GoldProgressBar(tk.Canvas):
    """Determinate progress bar with gold fill on navy track."""

    def __init__(self, master: tk.Widget, width: int = 440, height: int = 10, **kwargs) -> None:
        super().__init__(
            master,
            width=width,
            height=height,
            bg=BG,
            highlightthickness=0,
            borderwidth=0,
            **kwargs,
        )
        self._width = width
        self._height = height
        self._value = 0.0
        self._pulse = 0
        self._animating = False
        self._draw()

    def set_value(self, percent: float) -> None:
        self._value = max(0.0, min(100.0, percent))
        self._draw()

    def start_pulse(self) -> None:
        if self._animating:
            return
        self._animating = True
        self._pulse_tick()

    def stop_pulse(self) -> None:
        self._animating = False

    def _pulse_tick(self) -> None:
        if not self._animating:
            return
        self._pulse = (self._pulse + 4) % 100
        if self._value < 8:
            self.set_value(5 + self._pulse * 0.03)
        self.after(60, self._pulse_tick)

    def _draw(self) -> None:
        self.delete("all")
        pad = 1
        track_h = self._height - pad * 2
        self.create_rectangle(
            pad,
            pad,
            self._width - pad,
            pad + track_h,
            fill=INPUT_BG,
            outline=BORDER,
            width=1,
        )
        fill_w = max(0, (self._width - pad * 2) * (self._value / 100.0))
        if fill_w > 2:
            self.create_rectangle(
                pad + 1,
                pad + 1,
                pad + fill_w,
                pad + track_h - 1,
                fill=GOLD,
                outline="",
            )
            # subtle highlight strip
            self.create_line(
                pad + 1,
                pad + 2,
                pad + fill_w,
                pad + 2,
                fill=GOLD_BRIGHT,
            )


class TitleBar(tk.Frame):
    """Custom draggable title bar with gold accent."""

    def __init__(self, master: tk.Widget, root: tk.Tk, on_close: Callable[[], None]) -> None:
        super().__init__(master, bg=SURFACE, height=44)
        self.root = root
        self._drag_x = 0
        self._drag_y = 0
        self.pack_propagate(False)

        accent = tk.Frame(self, bg=GOLD, height=2)
        accent.pack(fill="x", side="top")

        row = tk.Frame(self, bg=SURFACE)
        row.pack(fill="both", expand=True, padx=14)

        brand = tkfont.Font(family=FONT_FAMILY, size=15, weight="bold")
        title = tk.Label(
            row,
            text="Wavish",
            font=brand,
            fg=GOLD_BRIGHT,
            bg=SURFACE,
            anchor="w",
        )
        title.pack(side="left", pady=8)

        subtitle = tk.Label(
            row,
            text="YouTube & Reels to WAV / MP3",
            font=FONT_SMALL,
            fg=TEXT_MUTED,
            bg=SURFACE,
            anchor="w",
        )
        subtitle.pack(side="left", padx=(10, 0), pady=10)

        close_btn = tk.Label(
            row,
            text="✕",
            font=(FONT_FAMILY, 12),
            fg=TEXT_MUTED,
            bg=SURFACE,
            cursor="hand2",
            padx=8,
        )
        close_btn.pack(side="right", pady=6)
        close_btn.bind("<Enter>", lambda _e: close_btn.configure(fg=TEXT, bg=SURFACE_RAISED))
        close_btn.bind("<Leave>", lambda _e: close_btn.configure(fg=TEXT_MUTED, bg=SURFACE))
        close_btn.bind("<Button-1>", lambda _e: on_close())

        for widget in (self, row, title, subtitle):
            widget.bind("<ButtonPress-1>", self._start_move)
            widget.bind("<B1-Motion>", self._on_move)

    def _start_move(self, event: tk.Event) -> None:
        self._drag_x = event.x_root - self.root.winfo_x()
        self._drag_y = event.y_root - self.root.winfo_y()

    def _on_move(self, event: tk.Event) -> None:
        self.root.geometry(f"+{event.x_root - self._drag_x}+{event.y_root - self._drag_y}")


def styled_button(
    parent: tk.Widget,
    text: str,
    command: Callable[[], None],
    *,
    primary: bool = True,
    width: int | None = None,
) -> tk.Button:
    if primary:
        bg, fg, active_bg, active_fg = GOLD, BG, GOLD_BRIGHT, BG
        border = GOLD_DIM
    else:
        bg, fg, active_bg, active_fg = SURFACE_RAISED, TEXT, BORDER, TEXT
        border = BORDER

    btn = tk.Button(
        parent,
        text=text,
        command=command,
        font=FONT_HEADING if primary else FONT_BODY,
        bg=bg,
        fg=fg,
        activebackground=active_bg,
        activeforeground=active_fg,
        relief="flat",
        borderwidth=1,
        highlightthickness=1,
        highlightbackground=border,
        highlightcolor=border,
        cursor="hand2",
        padx=14,
        pady=8,
    )
    if width:
        btn.configure(width=width)
    return btn


def styled_entry(parent: tk.Widget, textvariable: tk.StringVar, **kwargs) -> tk.Entry:
    return tk.Entry(
        parent,
        textvariable=textvariable,
        font=FONT_BODY,
        bg=INPUT_BG,
        fg=TEXT,
        insertbackground=GOLD_BRIGHT,
        relief="flat",
        highlightthickness=1,
        highlightbackground=BORDER,
        highlightcolor=GOLD_DIM,
        **kwargs,
    )


def label(parent: tk.Widget, text: str, *, muted: bool = False, small: bool = False, **kwargs) -> tk.Label:
    return tk.Label(
        parent,
        text=text,
        font=FONT_SMALL if small else FONT_BODY,
        fg=TEXT_MUTED if muted else TEXT,
        bg=kwargs.pop("bg", SURFACE),
        anchor="w",
        **kwargs,
    )


def radio(parent: tk.Widget, text: str, variable: tk.StringVar, value: str, command: Callable[[], None]) -> tk.Radiobutton:
    return tk.Radiobutton(
        parent,
        text=text,
        variable=variable,
        value=value,
        command=command,
        font=FONT_BODY,
        fg=TEXT,
        bg=SURFACE,
        activebackground=SURFACE,
        activeforeground=TEXT,
        selectcolor=INPUT_BG,
        highlightthickness=0,
        anchor="w",
    )
