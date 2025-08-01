import random
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By 
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import logging

# Set up detailed logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize data storage
books_data = []
book_urls = []

# Genre/shelf URLs - You can add more genres here
genre_urls = [
    "https://www.goodreads.com/shelf/show/mystery",
    "https://www.goodreads.com/shelf/show/romance", 
    "https://www.goodreads.com/shelf/show/fantasy",
    "https://www.goodreads.com/shelf/show/science-fiction",
    "https://www.goodreads.com/shelf/show/thriller",
    "https://www.goodreads.com/shelf/show/historical-fiction",
    "https://www.goodreads.com/shelf/show/non-fiction",
    "https://www.goodreads.com/shelf/show/biography"
]

def setup_driver():
    """Setup Chrome driver with robust options to prevent crashes"""
    logger.info("🚀 Setting up Chrome WebDriver...")
    
    opts = Options()
    
    # Basic stability options
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-features=VizDisplayCompositor")
    
    # Prevent crashes
    opts.add_argument("--disable-extensions")
    opts.add_argument("--disable-plugins")
    opts.add_argument("--disable-background-timer-throttling")
    opts.add_argument("--disable-backgrounding-occluded-windows")
    opts.add_argument("--disable-renderer-backgrounding")
    opts.add_argument("--disable-web-security")
    opts.add_argument("--disable-features=TranslateUI")
    opts.add_argument("--disable-features=BlinkGenPropertyTrees")
    
    # Memory and performance
    opts.add_argument("--memory-pressure-off")
    opts.add_argument("--max_old_space_size=4096")
    
    # User agent
    opts.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Window size
    opts.add_argument("--window-size=1920,1080")
    
    # Enable headless for faster scraping
    opts.add_argument("--headless")
    
    try:
        logger.info("📥 Setting up ChromeDriver...")
        service = Service(ChromeDriverManager().install())
        service.creation_flags = 0
        
        browser = webdriver.Chrome(service=service, options=opts)
        browser.set_page_load_timeout(30)
        browser.implicitly_wait(10)
        
        logger.info("✅ Chrome WebDriver setup successful!")
        return browser
        
    except Exception as e:
        logger.error(f"❌ Failed to setup Chrome WebDriver: {str(e)}")
        raise

def scrape_genre_extensively(browser, genre_url, target_books=600):
    """Enhanced scraping with multiple strategies to get more books"""
    book_urls = set()  # Use set to avoid duplicates automatically
    genre_name = genre_url.split('/')[-1]
    
    logger.info(f"📚 Starting extensive scraping of {genre_name} (target: {target_books} books)")
    
    # Strategy 1: Regular pagination
    page_num = 1
    max_pages = 100  # Increased from 50
    
    logger.info("🔥 Strategy 1: Regular pagination")
    while len(book_urls) < target_books and page_num <= max_pages:
        try:
            if page_num == 1:
                page_url = genre_url
            else:
                page_url = f"{genre_url}?page={page_num}"
            
            logger.info(f"🔍 Page {page_num} - Current: {len(book_urls)}/{target_books}")
            browser.get(page_url)
            
            WebDriverWait(browser, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(random.uniform(2, 4))
            
            # Multiple selectors for book links
            book_selectors = [
                'a[href*="/book/show/"]',
                'a[href*="/book/"]',
                '.bookTitle',
                '.bookCover a'
            ]
            
            page_books_added = 0
            for selector in book_selectors:
                elements = browser.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    try:
                        url = element.get_attribute('href')
                        if url and '/book/show/' in url:
                            clean_url = url.split('?')[0].split('#')[0]
                            if clean_url not in book_urls:
                                book_urls.add(clean_url)
                                page_books_added += 1
                                
                                if len(book_urls) >= target_books:
                                    break
                    except:
                        continue
                
                if len(book_urls) >= target_books:
                    break
            
            logger.info(f"✅ Added {page_books_added} new books from page {page_num}")
            
            if page_books_added == 0:
                logger.info(f"🔚 No new books on page {page_num}")
                break
            
            page_num += 1
            time.sleep(random.uniform(1, 3))
            
        except Exception as e:
            logger.error(f"❌ Error on page {page_num}: {str(e)}")
            page_num += 1
            continue
    
    # Strategy 2: Different sorting methods if still need more books
    if len(book_urls) < target_books:
        logger.info(f"🔥 Strategy 2: Different sorting (current: {len(book_urls)})")
        
        sorting_options = [
            "?sort=rating",
            "?sort=num_ratings", 
            "?sort=date_added",
            "?sort=date_pub",
            "?sort=title"
        ]
        
        for sort_option in sorting_options:
            if len(book_urls) >= target_books:
                break
                
            logger.info(f"🔄 Trying sort: {sort_option}")
            
            for page in range(1, 21):  # 20 pages per sorting method
                try:
                    url = f"{genre_url}{sort_option}&page={page}"
                    browser.get(url)
                    
                    WebDriverWait(browser, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    time.sleep(random.uniform(1, 2))
                    
                    elements = browser.find_elements(By.CSS_SELECTOR, 'a[href*="/book/show/"]')
                    page_added = 0
                    
                    for element in elements:
                        try:
                            url = element.get_attribute('href')
                            if url and '/book/show/' in url:
                                clean_url = url.split('?')[0].split('#')[0]
                                if clean_url not in book_urls:
                                    book_urls.add(clean_url)
                                    page_added += 1
                                    
                                    if len(book_urls) >= target_books:
                                        break
                        except:
                            continue
                    
                    if page_added == 0:
                        break
                        
                    if len(book_urls) >= target_books:
                        break
                        
                except Exception as e:
                    continue
    
    # Strategy 3: Search within genre if still need more
    if len(book_urls) < target_books:
        logger.info(f"🔥 Strategy 3: Search within genre (current: {len(book_urls)})")
        
        search_terms = [
            "award", "bestseller", "popular", "classic", "novel", "fiction",
            "mystery", "thriller", "romance", "adventure", "series", "book"
        ]
        
        for term in search_terms:
            if len(book_urls) >= target_books:
                break
                
            try:
                search_url = f"https://www.goodreads.com/search?q={term}+{genre_name}"
                logger.info(f"🔍 Searching: {term}")
                
                for page in range(1, 6):  # 5 pages per search term
                    try:
                        url = f"{search_url}&page={page}"
                        browser.get(url)
                        time.sleep(random.uniform(1, 2))
                        
                        elements = browser.find_elements(By.CSS_SELECTOR, 'a[href*="/book/show/"]')
                        
                        for element in elements:
                            try:
                                url = element.get_attribute('href')
                                if url and '/book/show/' in url:
                                    clean_url = url.split('?')[0].split('#')[0]
                                    book_urls.add(clean_url)
                                    
                                    if len(book_urls) >= target_books:
                                        break
                            except:
                                continue
                        
                        if len(book_urls) >= target_books:
                            break
                            
                    except:
                        continue
                        
            except Exception as e:
                continue
    
    final_urls = list(book_urls)
    logger.info(f"🎉 Finished scraping {genre_name}: {len(final_urls)} books collected")
    return final_urls

def scrape_all_genres_extensively(browser, target_books_per_genre=600):
    """Scrape multiple genres extensively"""
    all_books_by_genre = {}
    
    logger.info(f"🌟 Starting extensive scraping of {len(genre_urls)} genres")
    logger.info(f"🎯 Target: {target_books_per_genre} books per genre")
    
    for i, genre_url in enumerate(genre_urls, 1):
        genre_name = genre_url.split('/')[-1]
        logger.info(f"\n{'='*60}")
        logger.info(f"📖 PROCESSING GENRE {i}/{len(genre_urls)}: {genre_name.upper()}")
        logger.info(f"{'='*60}")
        
        try:
            genre_books = scrape_genre_extensively(browser, genre_url, target_books_per_genre)
            all_books_by_genre[genre_name] = genre_books
            
            logger.info(f"✅ {genre_name}: {len(genre_books)} books collected")
            
            # Save progress after each genre
            save_progress(all_books_by_genre)
            
            # Check if we achieved target
            if len(genre_books) >= target_books_per_genre:
                logger.info(f"🎯 TARGET ACHIEVED for {genre_name}!")
            else:
                logger.warning(f"⚠️ Only got {len(genre_books)}/{target_books_per_genre} for {genre_name}")
            
            # Longer delay between genres
            if i < len(genre_urls):
                delay = random.uniform(5, 10)
                logger.info(f"⏳ Waiting {delay:.1f} seconds before next genre...")
                time.sleep(delay)
                
        except Exception as e:
            logger.error(f"❌ Failed to scrape genre {genre_name}: {str(e)}")
            all_books_by_genre[genre_name] = []
            continue
    
    return all_books_by_genre

def save_progress(all_books_by_genre):
    """Save progress to CSV files"""
    try:
        # Save individual genre files
        for genre_name, book_urls in all_books_by_genre.items():
            if book_urls:
                df = pd.DataFrame({
                    'book_url': book_urls,
                    'genre': genre_name
                })
                filename = f'book_urls_{genre_name}.csv'
                df.to_csv(filename, index=False)
                logger.info(f"💾 Saved {len(book_urls)} URLs for {genre_name} to {filename}")
        
        # Save combined file
        all_urls = []
        for genre_name, urls in all_books_by_genre.items():
            for url in urls:
                all_urls.append({'book_url': url, 'genre': genre_name})
        
        if all_urls:
            combined_df = pd.DataFrame(all_urls)
            combined_df.to_csv('all_book_urls_combined.csv', index=False)
            logger.info(f"💾 Saved combined file with {len(all_urls)} total URLs")
            
    except Exception as e:
        logger.error(f"❌ Error saving progress: {str(e)}")

def main():
    """Main function to scrape 600+ books per genre"""
    browser = None
    
    try:
        # Setup driver
        browser = setup_driver()
        
        # Test basic functionality
        logger.info("🧪 Testing basic navigation...")
        browser.get("https://www.goodreads.com")
        time.sleep(3)
        logger.info("✅ Basic navigation successful!")
        
        # Start extensive scraping
        target_books = 600  # Target 600 books per genre
        all_books_by_genre = scrape_all_genres_extensively(browser, target_books)
        
        # Final summary
        logger.info("\n" + "="*70)
        logger.info("📊 FINAL SCRAPING SUMMARY")
        logger.info("="*70)
        
        total_books = 0
        for genre_name, book_urls in all_books_by_genre.items():
            count = len(book_urls)
            total_books += count
            status = "✅ TARGET MET" if count >= target_books else f"⚠️ SHORT BY {target_books - count}"
            logger.info(f"📚 {genre_name:20}: {count:4} books {status}")
        
        logger.info(f"\n🎉 TOTAL BOOKS COLLECTED: {total_books}")
        logger.info(f"📈 Average per genre: {total_books/len(genre_urls):.0f}")
        
        # Display sample URLs
        print("\n" + "="*50)
        print("SAMPLE BOOK URLS BY GENRE")
        print("="*50)
        for genre_name, urls in all_books_by_genre.items():
            if urls:
                print(f"\n{genre_name.upper()} ({len(urls)} books):")
                for i, url in enumerate(urls[:3], 1):
                    print(f"  {i}. {url}")
                if len(urls) > 3:
                    print(f"  ... and {len(urls) - 3} more")
        
    except Exception as e:
        logger.error(f"❌ Main process error: {str(e)}")
        import traceback
        logger.error(f"📋 Full traceback: {traceback.format_exc()}")
        
    finally:
        if browser:
            logger.info("🔒 Closing browser...")
            try:
                browser.quit()
                logger.info("✅ Browser closed successfully")
            except:
                logger.warning("⚠️ Error closing browser, but continuing...")

if __name__ == "__main__":
    main()
