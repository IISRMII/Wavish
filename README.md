# Wavish

Portable Windows app that turns a **YouTube** or **Instagram Reel** link into a high-quality **WAV** or **MP3**.

No installer. Download the `.exe`, double-click, paste a link.

<p>
  <a href="https://github.com/IISRMII/Wavish/releases/latest/download/Wavish.exe"><img alt="Download Wavish.exe" src="https://img.shields.io/badge/Download-Wavish.exe-d4af37?style=for-the-badge&labelColor=071526" /></a>
  <a href="https://github.com/IISRMII/Wavish/releases/latest"><img alt="Latest release" src="https://img.shields.io/github/v/release/IISRMII/Wavish?style=for-the-badge&color=d4af37&labelColor=071526" /></a>
</p>

---

## Download (Windows)

**[Download Wavish.exe](https://github.com/IISRMII/Wavish/releases/latest/download/Wavish.exe)** — latest release, one file.

The `.exe` lives on the [Releases](https://github.com/IISRMII/Wavish/releases) page, not in the source folders above. That’s normal for open-source desktop apps.

1. Click the download link
2. Put `Wavish.exe` anywhere you like (Desktop, a USB stick, etc.)
3. Double-click to run — nothing is installed

Windows SmartScreen may say the app is unrecognized because it isn’t code-signed. Choose **More info** → **Run anyway**. That’s expected for small open-source tools.

ffmpeg is bundled inside the exe. You don’t need to install Python, ffmpeg, or anything else.

---

## How to use

1. Open **Wavish**
2. Paste a YouTube or Instagram Reel URL
3. Pick a save folder (defaults to `Music\Wavish`)
4. Choose a format:
   - **WAV** — 48 kHz, 24-bit stereo (best quality)
   - **MP3** — 320 kbps
5. Click **Extract**

Settings are saved next to the exe in `settings.json`.

### Supported links

- YouTube videos and Shorts (`youtube.com`, `youtu.be`)
- Instagram Reels (`instagram.com/reel/…` and `/reels/…`)
- Instagram video posts (`instagram.com/p/…`)

Public links work. Private or login-only Instagram clips do not.

Only extract audio you have the right to use — your own uploads, or content you have permission for.

---

## Build from source

If you want to run or change the Python app instead of using the exe:

```powershell
git clone https://github.com/IISRMII/Wavish.git
cd Wavish
python -m venv venv
.\venv\Scripts\pip install -r requirements.txt
python app.py
```

You’ll need [ffmpeg](https://ffmpeg.org/) on your PATH, or a copy at `bin\ffmpeg.exe`.

To rebuild the portable exe (downloads ffmpeg and bundles it):

```powershell
.\build.ps1
```

The result is `dist\Wavish.exe`.

---

## License

[MIT](LICENSE) — free to use, share, and modify.
