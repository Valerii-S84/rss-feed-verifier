import sys
import re
import json
import csv
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# -------- SETTINGS --------
USER_AGENT = "Mozilla/5.0 (compatible; FeedVerifier/1.0; +https://example.local)"
TIMEOUT = 12
RETRIES = 2
SLEEP_BETWEEN = 0.4  # сек, щоб не лупити надто часто
HEADERS = {"User-Agent": USER_AGENT, "Accept": "*/*"}

# Кандидатні шляхи, якщо на сайті немає <link rel="alternate"...>
CANDIDATE_SUFFIXES = [
    "/feed", "/feed/", "/rss", "/rss/", "/rss.xml", "/atom.xml",
    "/category/nutrition/feed", "/tag/nutrition/feed"
]

# -------- HELPERS --------
def is_xml_feed(text: str) -> bool:
    if not text:
        return False
    head = text.strip()[:2048].lower()
    # типові сигнатури RSS/Atom
    return head.startswith("<?xml") or head.startswith("<rss") or head.startswith("<feed") or "<channel" in head

def fetch(url: str):
    last_exc = None
    for _ in range(RETRIES):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
            return resp
        except Exception as e:
            last_exc = e
            time.sleep(0.6)
    if last_exc:
        raise last_exc

def normalize_url(base: str, href: str) -> str:
    if not href:
        return ""
    u = urljoin(base, href)
    # прибираємо фрагменти типу #something
    parts = urlparse(u)
    u = parts._replace(fragment="").geturl()
    return u

def unique_keep_order(seq):
    seen = set()
    out = []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out

# -------- DISCOVERY --------
def discover_feeds(site_url: str):
    """Повертає список валідних фідів для конкретного сайту."""
    feeds = []

    # 1) Якщо це вже фід — просто перевіримо
    try:
        r = fetch(site_url)
        ctype = (r.headers.get("Content-Type") or "").lower()
        text = r.text
        if ("xml" in ctype or "rss" in ctype or "atom" in ctype) and is_xml_feed(text):
            return [site_url]
    except Exception:
        pass

    # 2) Парсимо HTML та витягуємо <link rel="alternate" type="application/rss+xml|application/atom+xml">
    try:
        if 'r' not in locals():
            r = fetch(site_url)
        if "text/html" in (r.headers.get("Content-Type") or "") or "<html" in r.text.lower():
            soup = BeautifulSoup(r.text, "html.parser")
            link_tags = soup.find_all("link", attrs={"rel": re.compile("alternate", re.I)})
            for lt in link_tags:
                t = (lt.get("type") or "").lower()
                if "rss" in t or "atom" in t or "xml" in t:
                    href = lt.get("href")
                    cand = normalize_url(site_url, href)
                    if cand:
                        feeds.append(cand)
    except Exception:
        pass

    # 3) Якщо нічого не знайшли — перебираємо кандидатні шляхи
    if not feeds:
        for suf in CANDIDATE_SUFFIXES:
            feeds.append(normalize_url(site_url, suf))

    # 4) Валідуємо кожного кандидата
    valid = []
    for f in unique_keep_order(feeds):
        try:
            resp = fetch(f)
            ctype = (resp.headers.get("Content-Type") or "").lower()
            if ("xml" in ctype or "rss" in ctype or "atom" in ctype) and is_xml_feed(resp.text):
                valid.append(f)
                continue
            # навіть якщо content-type текстовий — інколи це фід
            if is_xml_feed(resp.text):
                valid.append(f)
        except Exception:
            continue

    return unique_keep_order(valid)

# -------- IO --------
def read_input_urls(xlsx_path: Path):
    # читаємо Excel, колонка має називатись "Інтернет-адреса"
    try:
        import pandas as pd
    except ImportError:
        print("Встанови залежність: pip install pandas openpyxl")
        sys.exit(1)

    df = pd.read_excel(xlsx_path)
    col = None
    for c in df.columns:
        if str(c).strip().lower() in ["інтернет-адреса", "internet-address", "url", "адреса", "link"]:
            col = c
            break
    if col is None:
        raise ValueError("Не знайдено колонку з URL. Перейменуй колонку на 'Інтернет-адреса'.")

    urls = []
    for v in df[col].dropna().tolist():
        s = str(v).strip()
        if s and s.startswith("http"):
            urls.append(s)
    return urls

def save_js(feeds, path: Path):
    with path.open("w", encoding="utf-8") as f:
        f.write("const feeds = [\n")
        for u in feeds:
            f.write(f'  "{u}",\n')
        f.write("];\n")
    print(f"[OK] Збережено JS: {path}")

def save_json(feeds, path: Path):
    with path.open("w", encoding="utf-8") as f:
        json.dump(feeds, f, ensure_ascii=False, indent=2)
    print(f"[OK] Збережено JSON: {path}")

def save_audit(audit_rows, path: Path):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Site URL", "Found Feed URL"])
        for row in audit_rows:
            w.writerow(row)
    print(f"[OK] Збережено аудит: {path}")

# -------- MAIN --------
def main():
    if len(sys.argv) < 2:
        print("Використання: python verify_feeds.py \"/шлях/до/Новий Microsoft Excel Worksheet.xlsx\"")
        sys.exit(2)

    xlsx_path = Path(sys.argv[1]).expanduser().resolve()
    if not xlsx_path.exists():
        print(f"Файл не знайдено: {xlsx_path}")
        sys.exit(2)

    urls = read_input_urls(xlsx_path)
    print(f"Знайдено {len(urls)} сайт(ів) для перевірки.")

    all_valid = []
    audit = []

    for i, site in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] {site}")
        try:
            feeds = discover_feeds(site)
            if feeds:
                for f in feeds:
                    audit.append([site, f])
                all_valid.extend(feeds)
            else:
                audit.append([site, "—"])
        except Exception as e:
            audit.append([site, f"ERROR: {e}"])
        time.sleep(SLEEP_BETWEEN)

    all_valid = unique_keep_order(all_valid)

    out_dir = Path(".").resolve()
    save_js(all_valid, out_dir / "feeds.js")
    save_json(all_valid, out_dir / "feeds.json")
    save_audit(audit, out_dir / "feed_audit.csv")

    print(f"\nГотово. Валідних фідів: {len(all_valid)}")
    print("Використай feeds.js у своєму коді.")

if __name__ == "__main__":
    main()
