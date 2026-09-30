import os
import yt_dlp
import cloudscraper
from bs4 import BeautifulSoup

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}


# ---------- Generic yt-dlp downloader (YouTube, etc.) ----------
def download_ytdlp(url):
    opts = {
        "outtmpl": os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s"),
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "http_headers": HEADERS,
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if "entries" in info:
                info = info["entries"][0]
            path = ydl.prepare_filename(info)
            base, _ = os.path.splitext(path)
            for ext in [".mp4", ".mkv", ".webm"]:
                if os.path.exists(base + ext):
                    return base + ext
            return path if os.path.exists(path) else None
    except Exception as e:
        print(f"[yt-dlp] {e}")
        return None


# ---------- AnimePahe scraper + yt-dlp ----------
def download_animepahe(url):
    try:
        scraper = cloudscraper.create_scraper()
        r = scraper.get(url, headers=HEADERS, timeout=30)
        soup = BeautifulSoup(r.text, "html.parser")

        buttons = soup.select("a.btn.btn-primary")
        if not buttons:
            return None

        chosen = None
        for b in buttons:
            text = b.get_text(strip=True).lower()
            if "1080" in text:
                chosen = b["href"]
                break
            if "720" in text and not chosen:
                chosen = b["href"]

        if not chosen:
            chosen = buttons[0]["href"]

        return download_ytdlp(chosen)

    except Exception as e:
        print(f"[animepahe] {e}")
        return None


# ---------- Main router ----------
def smart_download(url):
    if "animepahe" in url:
        return download_animepahe(url)
    else:
        return download_ytdlp(url)
