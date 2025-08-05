# fast_goodreads_scraper.py
import os, sys, time, math, random, threading, concurrent.futures, re
from collections import defaultdict
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging

# ────────────────────────────── CONFIG ──────────────────────────────
NUM_WORKERS      = 12      # headless Chrome instances
URLS_PER_WORKER  = 200     # ≈200 gives good balance of speed/RAM
DASH_INTERVAL    = 10      # seconds between dashboard refreshes
CSV_INPUT        = "all_book_urls_combined.csv"

# ──────────────────────────── LOGGING SETUP ─────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ──────────────────────── DRIVER & NOISE SUPPRESSION ────────────────
def build_driver() -> webdriver.Chrome:
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-webgl")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-background-networking")
    opts.add_argument("--disable-sync")
    opts.add_argument("--disable-speech-api")
    opts.add_argument("--log-level=3")  # INFO=0 … FATAL=3
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])
    opts.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115 Safari/537.36"
    )

    # keep Chromedriver silent
    null_log = "NUL" if os.name == "nt" else "/dev/null"
    service = Service(ChromeDriverManager().install(), log_path=null_log)
    driver = webdriver.Chrome(service=service, options=opts)
    driver.set_page_load_timeout(20)
    driver.implicitly_wait(10)
    return driver

# ────────────────────────── SCRAPING HELPERS ────────────────────────
title_css   = ['h1[data-testid="bookTitle"]', 'h1#bookTitle', 'h1']
author_css  = ['[data-testid="name"]', '.authorName', 'a.authorName span']
rating_css  = [
    '[data-testid="reviewHeader"] div',
    'span[itemprop="ratingValue"]',
    '.RatingStatistics__rating',
]
rating_ct_css = ['meta[itemprop="ratingCount"]', '[data-testid="reviewHeader"]']
desc_css = [
    '[data-testid="description"] span[style]',
    '[data-testid="description"] span',
    '#description span[style]',
    '#description span',
    '.readable span',
]

def click_expand(driver):
    try:
        btns = driver.find_elements(By.CSS_SELECTOR, 'button, a')
        for b in btns:
            if b.is_displayed() and ("more" in b.text.lower() or "expand" in b.text.lower()):
                driver.execute_script("arguments[0].click();", b)
                time.sleep(0.5)
                break
    except Exception:
        pass

def extract_book(html: str) -> dict | None:
    soup = BeautifulSoup(html, "html.parser")

    def first_text(selectors):
        for sel in selectors:
            el = soup.select_one(sel)
            if el and (txt := el.get_text(strip=True)):
                return txt
        return None

    title  = first_text(title_css)
    author = first_text(author_css)

    rating = None
    for sel in rating_css:
        for el in soup.select(sel):
            m = re.search(r"(\d+\.\d+)", el.get_text(strip=True))
            if m:
                r = float(m.group(1))
                if 0 < r <= 5:
                    rating = r
                    break
        if rating:
            break

    rating_count = None
    el_ct = soup.select_one(rating_ct_css[0])
    if el_ct and el_ct.get("content"):
        rating_count = int(el_ct["content"].replace(",", ""))
    if rating_count is None:
        el_ct = soup.select_one(rating_ct_css[1])
        if el_ct:
            m = re.search(r"([\d,]+)\s*rating", el_ct.get_text())
            if m:
                rating_count = int(m.group(1).replace(",", ""))

    # description
    desc = None
    for sel in desc_css:
        el = soup.select_one(sel)
        if el and len((txt := el.get_text(strip=True))) > 50:
            desc = txt
            break

    # genres
    genres = [
        g.get_text(strip=True)
        for g in soup.select('[data-testid="genresList"] a, a.bookPageGenreLink')[:5]
    ]
    return (
        {
            "title": title,
            "author": author,
            "rating": rating,
            "rating_count": rating_count,
            "description": desc,
            "genres": ", ".join(genres) if genres else None,
        }
        if title and author
        else None
    )

# ──────────────────────────── WORKER LOGIC ──────────────────────────
progress_lock   = threading.Lock()
worker_progress = defaultdict(int)   # {worker_id: books_done}

def worker(urls: list[str], wid: int) -> list[dict]:
    drv = build_driver()
    data = []
    try:
        for u in urls:
            try:
                drv.get(u)
                WebDriverWait(drv, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                click_expand(drv)
                bk = extract_book(drv.page_source)
                if bk:
                    data.append(bk)
                # update dashboard counter
                with progress_lock:
                    worker_progress[wid] += 1
            except Exception:
                continue
            time.sleep(random.uniform(1.5, 3.0))
    finally:
        drv.quit()
    return data

# ───────────────────────────── DASHBOARD ────────────────────────────
def dashboard(stop_event: threading.Event):
    while not stop_event.is_set():
        time.sleep(DASH_INTERVAL)
        with progress_lock:
            total = sum(worker_progress.values())
            detail = " | ".join(f"W{w}:{c}" for w, c in sorted(worker_progress.items()))
        print(
            f"\r{time.strftime('%H:%M:%S')}  "
            f"Workers:{len(worker_progress):2d}  "
            f"Total:{total:5d}  {detail.ljust(80)}",
            end="",
            flush=True,
        )

# ────────────────────────────── MAIN FLOW ───────────────────────────
def run_batch(batch_urls: list[str], batch_no: int) -> list[dict]:
    logger.info(f"Batch {batch_no}: {len(batch_urls)} URLs")
    chunk = math.ceil(len(batch_urls) / NUM_WORKERS)
    chunks = [batch_urls[i : i + chunk] for i in range(0, len(batch_urls), chunk)]

    results = []
    with concurrent.futures.ThreadPoolExecutor(NUM_WORKERS) as ex:
        futs = {ex.submit(worker, ch, i): i for i, ch in enumerate(chunks)}
        for f in concurrent.futures.as_completed(futs):
            wid = futs[f]
            scraped = f.result()
            results.extend(scraped)
            logger.info(f"Worker {wid} finished – {len(scraped)} books")
    return results

def main():
    if not os.path.exists(CSV_INPUT):
        logger.error(f"{CSV_INPUT} not found"); return

    urls = pd.read_csv(CSV_INPUT)["book_url"].dropna().tolist()
    if not urls:
        logger.error("CSV has no URLs"); return

    batch_size = NUM_WORKERS * URLS_PER_WORKER
    batches = [urls[i : i + batch_size] for i in range(0, len(urls), batch_size)]
    logger.info(f"Total URLs: {len(urls)}  |  "
                f"{len(batches)} batches  (≈{URLS_PER_WORKER} per worker)")

    stop_dash = threading.Event()
    threading.Thread(target=dashboard, args=(stop_dash,), daemon=True).start()

    grand = []
    t0 = time.time()
    for bno, burls in enumerate(batches, 1):
        res = run_batch(burls, bno)
        grand.extend(res)

        # save batch
        dfb = pd.DataFrame(res)
        dfb.to_csv(f"batch_{bno}_books_{len(res)}.csv", index=False, encoding="utf-8")
        logger.info(f"Batch {bno} saved – {len(res)} books")

    # final save
    stop_dash.set()
    df = pd.DataFrame(grand)
    df.to_csv("books_complete.csv", index=False, encoding="utf-8")

    elapsed = time.time() - t0
    logger.info(
        f"FINISHED – {len(grand)} books  |  "
        f"{elapsed/60:.1f} min  |  "
        f"{len(grand)/elapsed:.1f} books/sec"
    )

if __name__ == "__main__":
    main()
