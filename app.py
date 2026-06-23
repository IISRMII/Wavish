import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

from downloader import download_audio
from settings_store import load_settings, save_settings
from theme import (
    BG,
    BORDER,
    GOLD,
    SURFACE,
    TEXT_MUTED,
    TitleBar,
    GoldProgressBar,
    apply_root_style,
    card,
    label,
    radio,
    styled_button,
    styled_entry,
)


class WavishApp(tk.Tk):
    WINDOW_W = 500
    WINDOW_H = 520

    def __init__(self) -> None:
        super().__init__()
        self.title("Wavish")
        self.overrideredirect(True)
        self.resizable(False, False)
        self.geometry(f"{self.WINDOW_W}x{self.WINDOW_H}")
        apply_root_style(self)

        settings = load_settings()
        self.save_dir = tk.StringVar(value=settings["save_dir"])
        self.output_format = tk.StringVar(value=settings["output_format"])
        self.url_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Paste a YouTube URL and press Extract.")
        self._busy = False
        self._download_btn: tk.Button | None = None

        self._build_ui()
        self._center_window()
        self.bind("<Escape>", lambda _e: self._close())
        self.protocol("WM_DELETE_WINDOW", self._close)

    def _close(self) -> None:
        if self._busy:
            if not messagebox.askyesno("Wavish", "A download is in progress. Close anyway?"):
                return
        self.destroy()

    def _center_window(self) -> None:
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.WINDOW_W // 2)
        y = (self.winfo_screenheight() // 2) - (self.WINDOW_H // 2)
        self.geometry(f"{self.WINDOW_W}x{self.WINDOW_H}+{x}+{y}")

    def _build_ui(self) -> None:
        outer = tk.Frame(self, bg=BG, highlightbackground=GOLD, highlightthickness=1)
        outer.pack(fill="both", expand=True)

        TitleBar(outer, self, self._close).pack(fill="x")

        body = tk.Frame(outer, bg=BG, padx=20, pady=16)
        body.pack(fill="both", expand=True)

        # URL section
        url_card = card(body)
        url_card.pack(fill="x", pady=(0, 12))

        inner = tk.Frame(url_card, bg=SURFACE, padx=16, pady=14)
        inner.pack(fill="x")

        label(inner, "YouTube URL", muted=True, small=True).pack(anchor="w")

        url_row = tk.Frame(inner, bg=SURFACE)
        url_row.pack(fill="x", pady=(6, 0))

        url_entry = styled_entry(url_row, self.url_var)
        url_entry.pack(side="left", fill="x", expand=True, ipady=6)
        url_entry.focus_set()

        self._download_btn = styled_button(url_row, "Extract", self._on_download, width=10)
        self._download_btn.pack(side="left", padx=(10, 0))

        # Settings
        settings_card = card(body)
        settings_card.pack(fill="x", pady=(0, 12))

        settings_inner = tk.Frame(settings_card, bg=SURFACE, padx=16, pady=14)
        settings_inner.pack(fill="x")

        gold_rule = tk.Frame(settings_inner, bg=GOLD, height=1)
        gold_rule.pack(fill="x", pady=(0, 10))

        settings_title = label(settings_inner, "Settings", bg=SURFACE)
        settings_title.configure(font=("Segoe UI", 11, "bold"), fg=GOLD)
        settings_title.pack(anchor="w")

        label(settings_inner, "Save to", muted=True, small=True).pack(anchor="w", pady=(10, 0))

        save_row = tk.Frame(settings_inner, bg=SURFACE)
        save_row.pack(fill="x", pady=(4, 10))

        styled_entry(save_row, self.save_dir).pack(side="left", fill="x", expand=True, ipady=5)
        styled_button(save_row, "Browse", self._pick_folder, primary=False).pack(side="left", padx=(8, 0))

        label(settings_inner, "Output format", muted=True, small=True).pack(anchor="w")

        fmt_col = tk.Frame(settings_inner, bg=SURFACE)
        fmt_col.pack(anchor="w", pady=(4, 0))

        radio(
            fmt_col,
            "WAV — 48 kHz, 24-bit (best quality)",
            self.output_format,
            "wav",
            self._persist_settings,
        ).pack(anchor="w")
        radio(
            fmt_col,
            "MP3 — 320 kbps",
            self.output_format,
            "mp3",
            self._persist_settings,
        ).pack(anchor="w", pady=(4, 0))

        # Progress + status
        progress_frame = tk.Frame(body, bg=BG)
        progress_frame.pack(fill="x", pady=(4, 8))

        self.progress = GoldProgressBar(progress_frame, width=456, height=12)
        self.progress.pack(fill="x")

        self.status_label = tk.Label(
            body,
            textvariable=self.status_var,
            font=("Segoe UI", 9),
            fg=TEXT_MUTED,
            bg=BG,
            anchor="w",
            wraplength=456,
            justify="left",
        )
        self.status_label.pack(fill="x")

        footer = tk.Label(
            body,
            text="High-quality audio extraction",
            font=("Segoe UI", 8),
            fg=BORDER,
            bg=BG,
        )
        footer.pack(side="bottom", pady=(12, 0))

        self.bind("<Return>", lambda _e: self._on_download())

    def _pick_folder(self) -> None:
        folder = filedialog.askdirectory(initialdir=self.save_dir.get() or None)
        if folder:
            self.save_dir.set(folder)
            self._persist_settings()

    def _persist_settings(self) -> None:
        fmt = self.output_format.get()
        if fmt not in ("wav", "mp3"):
            fmt = "wav"
        save_settings(self.save_dir.get().strip(), fmt)  # type: ignore[arg-type]

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        if self._download_btn:
            self._download_btn.configure(state="disabled" if busy else "normal")
        if busy:
            self.progress.set_value(2)
            self.progress.start_pulse()
        else:
            self.progress.stop_pulse()
            self.progress.set_value(0)

    def _set_progress(self, percent: float) -> None:
        self.progress.set_value(percent)

    def _on_download(self) -> None:
        if self._busy:
            return
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("Wavish", "Please paste a YouTube URL.")
            return

        save_dir = Path(self.save_dir.get().strip())
        if not save_dir:
            messagebox.showwarning("Wavish", "Choose a save folder in Settings.")
            return

        fmt = self.output_format.get()
        if fmt not in ("wav", "mp3"):
            fmt = "wav"

        self._persist_settings()
        self._set_busy(True)
        self.status_var.set("Starting…")

        def worker() -> None:
            try:
                def status(msg: str) -> None:
                    self.after(0, lambda m=msg: self.status_var.set(m))

                def progress(pct: float) -> None:
                    self.after(0, lambda p=pct: self._set_progress(p))

                path = download_audio(
                    url,
                    save_dir,
                    fmt,  # type: ignore[arg-type]
                    on_status=status,
                    on_progress=progress,
                )
                self.after(0, lambda: self._set_progress(100))
                self.after(
                    0,
                    lambda: messagebox.showinfo("Wavish", f"Saved:\n{path}"),
                )
                self.after(0, lambda: self.status_var.set(f"Saved to {path.name}"))
            except Exception as exc:
                self.after(0, lambda e=exc: messagebox.showerror("Wavish", str(e)))
                self.after(0, lambda e=exc: self.status_var.set(f"Error: {e}"))
            finally:
                self.after(0, lambda: self._set_busy(False))

        threading.Thread(target=worker, daemon=True).start()


def main() -> None:
    app = WavishApp()
    app.mainloop()


if __name__ == "__main__":
    main()
