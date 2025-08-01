import random
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import logging
import concurrent.futures
from threading import Lock
import re

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SafeCounter:
    def __init__(self):
        self._value = 0
        self._lock = Lock()
    
    def increment(self):
        with self._lock:
            self._value += 1
            return self._value

def setup_optimized_driver():
    """Setup Chrome driver optimized for complete data extraction"""
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-images")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--disable-plugins")
    # Keep JavaScript enabled for complete content loading
    opts.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    service = Service(ChromeDriverManager().install())
    browser = webdriver.Chrome(service=service, options=opts)
    browser.set_page_load_timeout(20)
    browser.implicitly_wait(10)
    
    return browser

def click_show_more_description(browser):
    """Try to click 'Show more' button for full description"""
    try:
        show_more_selectors = [
            'button[data-testid="contentReviewedByUsers"] button',
            'button:contains("Show more")',
            'a:contains("...more")',
            '.Button--inline',
            '[data-testid="showMore"]',
            '#description a',
            'a[class*="expand"]'
        ]
        
        for selector in show_more_selectors:
            try:
                elements = browser.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        text = element.text.lower()
                        if 'more' in text or 'expand' in text:
                            browser.execute_script("arguments[0].click();", element)
                            time.sleep(1)
                            logger.info("✅ Clicked 'Show more' for description")
                            return True
            except:
                continue
        return False
    except:
        return False

def extract_rating_enhanced(soup, browser):
    """Enhanced rating extraction"""
    rating = None
    rating_count = None
    
    # Rating extraction
    rating_selectors = [
        '[data-testid="reviewHeader"] div',
        'span[itemprop="ratingValue"]',
        '.RatingStatistics__rating',
        '.average',
        '.BookPageMetadataSection__ratingStats span',
        '[data-testid="rating-graph"] div'
    ]
    
    for selector in rating_selectors:
        try:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                rating_match = re.search(r'(\d+\.?\d*)', text)
                
                if rating_match:
                    try:
                        potential_rating = float(rating_match.group(1))
                        if 0 < potential_rating <= 5:  # Valid rating range (exclude 0.0)
                            rating = potential_rating
                            break
                    except ValueError:
                        continue
            if rating:
                break
        except Exception:
            continue
    
    # Rating count extraction
    rating_count_selectors = [
        'meta[itemprop="ratingCount"]',
        '[data-testid="reviewHeader"]'
    ]
    
    for selector in rating_count_selectors:
        try:
            element = soup.select_one(selector)
            if element:
                if element.get('content'):  # meta tag
                    try:
                        rating_count = int(element['content'].replace(',', ''))
                        break
                    except:
                        continue
                else:  # text element
                    text = element.get_text()
                    match = re.search(r'([\d,]+)\s*rating', text)
                    if match:
                        try:
                            rating_count = int(match.group(1).replace(',', ''))
                            break
                        except:
                            continue
        except Exception:
            continue
    
    return rating, rating_count

def extract_full_description(soup):
    """Extract complete description with multiple strategies"""
    description = None
    
    # Strategy 1: Standard description selectors
    desc_selectors = [
        '[data-testid="description"] span[style]',
        '[data-testid="description"] span',
        '#description span[style]',
        '#description span',
        '.readable span',
        '[data-testid="contentReviewedByUsers"] span',
        '.DetailsLayoutRightParagraph span'
    ]
    
    for selector in desc_selectors:
        try:
            element = soup.select_one(selector)
            if element:
                desc_text = element.get_text(strip=True)
                if desc_text and len(desc_text) > 100:  # Ensure substantial content
                    description = desc_text
                    break
        except:
            continue
    
    # Strategy 2: If still truncated, try to get full text from all description spans
    if not description or len(description) < 200:
        try:
            desc_container = soup.select_one('[data-testid="description"]') or soup.select_one('#description')
            if desc_container:
                all_spans = desc_container.find_all('span')
                full_text = ' '.join([span.get_text(strip=True) for span in all_spans])
                if len(full_text) > len(description or ""):
                    description = full_text
        except:
            pass
    
    # Strategy 3: Fallback to any substantial text in description area
    if not description:
        try:
            desc_area = soup.select_one('[data-testid="description"]') or soup.select_one('#description')
            if desc_area:
                description = desc_area.get_text(strip=True)
        except:
            pass
    
    return description

def scrape_single_book_complete(browser, url):
    """Complete book scraping with full descriptions and ratings"""
    try:
        browser.get(url)
        WebDriverWait(browser, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # Wait for content to load
        time.sleep(random.uniform(3, 5))
        
        # Try to expand description
        click_show_more_description(browser)
        time.sleep(2)
        
        soup = BeautifulSoup(browser.page_source, 'html.parser')
        
        # Extract Title
        title = None
        title_selectors = ['h1[data-testid="bookTitle"]', 'h1#bookTitle', 'h1']
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True)
                if title:
                    break
        
        # Extract Author
        author = None
        author_selectors = ['[data-testid="name"]', '.authorName', 'a.authorName span']
        for selector in author_selectors:
            element = soup.select_one(selector)
            if element:
                author = element.get_text(strip=True)
                if author:
                    break
        
        # Extract rating and rating count
        rating, rating_count = extract_rating_enhanced(soup, browser)
        
        # Extract FULL description
        description = extract_full_description(soup)
        
        # Extract genres
        genres = []
        genre_elements = soup.select('[data-testid="genresList"] a') or soup.select('a.bookPageGenreLink')
        if genre_elements:
            genres = [g.get_text(strip=True) for g in genre_elements[:5]]
        
        if title and author:
            result = {
                'title': title,
                'author': author,
                'rating': rating,
                'rating_count': rating_count,
                'description': description,
                'genres': ', '.join(genres) if genres else None
            }
            
            # Log status
            rating_status = f"Rating {rating}" if rating else "NO RATING"
            desc_length = len(description) if description else 0
            logger.info(f"✅ {title}: {rating_status} | Desc: {desc_length} chars")
            
            return result
        return None
        
    except Exception as e:
        return None

def worker_function_complete(url_chunk, worker_id):
    """Worker function for complete data extraction"""
    browser = setup_optimized_driver()
    worker_data = []
    
    try:
        for i, url in enumerate(url_chunk):
            try:
                book_data = scrape_single_book_complete(browser, url)
                if book_data:
                    worker_data.append(book_data)
                
                time.sleep(random.uniform(2, 4))
                
                if (i + 1) % 20 == 0:
                    ratings_found = sum(1 for book in worker_data if book.get('rating'))
                    avg_desc_length = sum(len(book.get('description', '')) for book in worker_data) / len(worker_data) if worker_data else 0
                    logger.info(f"Worker {worker_id}: {i+1}/{len(url_chunk)} - Books: {len(worker_data)} - Ratings: {ratings_found} - Avg Desc: {avg_desc_length:.0f} chars")
                    
            except:
                continue
    
    finally:
        browser.quit()
    
    ratings_found = sum(1 for book in worker_data if book.get('rating'))
    avg_desc_length = sum(len(book.get('description', '')) for book in worker_data) / len(worker_data) if worker_data else 0
    logger.info(f"Worker {worker_id} COMPLETED: {len(worker_data)} books - {ratings_found} ratings - Avg desc: {avg_desc_length:.0f} chars")
    return worker_data

def process_batch(batch_urls, batch_num):
    """Process a single batch of URLs"""
    logger.info(f"🔄 Processing batch {batch_num} with {len(batch_urls)} books")
    
    num_workers = 4
    chunk_size = len(batch_urls) // num_workers
    url_chunks = [batch_urls[i:i + chunk_size] for i in range(0, len(batch_urls), chunk_size)]
    
    batch_data = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(worker_function_complete, chunk, i) for i, chunk in enumerate(url_chunks)]
        
        for future in concurrent.futures.as_completed(futures):
            try:
                worker_data = future.result()
                batch_data.extend(worker_data)
            except Exception as e:
                logger.error(f"❌ Worker failed: {str(e)}")
    
    return batch_data

def main():
    """Main function with batch processing"""
    try:
        # Load all URLs
        df_urls = pd.read_csv('all_book_urls_combined.csv')
        book_urls = df_urls['book_url'].dropna().tolist()
        
        batch_size = 1000  # Process 1,000 books per batch
        total_books = len(book_urls)
        all_scraped_data = []
        
        logger.info(f"📚 Total books available: {total_books}")
        logger.info(f"🎯 Processing in batches of {batch_size}")
        
        # Process in batches
        for batch_start in range(0, total_books, batch_size):
            batch_end = min(batch_start + batch_size, total_books)
            current_batch = book_urls[batch_start:batch_end]
            batch_num = (batch_start // batch_size) + 1
            
            logger.info(f"\n{'='*60}")
            logger.info(f"📦 PROCESSING BATCH {batch_num}")
            logger.info(f"📖 Books {batch_start + 1} to {batch_end} ({len(current_batch)} books)")
            logger.info(f"{'='*60}")
            
            # Process current batch
            batch_data = process_batch(current_batch, batch_num)
            all_scraped_data.extend(batch_data)
            
            # Save batch progress
            if batch_data:
                df_batch = pd.DataFrame(batch_data)
                df_batch.to_csv(f'books_batch_{batch_num}_complete.csv', index=False)
                
                # Calculate statistics
                ratings_found = sum(1 for book in batch_data if book.get('rating'))
                avg_desc_length = sum(len(book.get('description', '')) for book in batch_data) / len(batch_data) if batch_data else 0
                
                logger.info(f"✅ Batch {batch_num} completed:")
                logger.info(f"   📊 Books scraped: {len(batch_data)}")
                logger.info(f"   ⭐ Ratings found: {ratings_found} ({ratings_found/len(batch_data)*100:.1f}%)")
                logger.info(f"   📄 Avg description length: {avg_desc_length:.0f} characters")
            
            # Save cumulative progress
            df_progress = pd.DataFrame(all_scraped_data)
            df_progress.to_csv(f'books_progress_total_{len(all_scraped_data)}.csv', index=False)
            
            logger.info(f"📊 Total collected so far: {len(all_scraped_data)} books")
            
            # Stop after 3 batches for testing (remove this line to process all)
            if batch_num >= 3:
                logger.info("🛑 Stopping after 3 batches for testing")
                break
        
        # Save final results
        if all_scraped_data:
            df_final = pd.DataFrame(all_scraped_data)
            df_final.to_csv('books_complete_final_dataset.csv', index=False)
            df_final.to_excel('books_complete_final_dataset.xlsx', index=False)
            
            # Final statistics
            total_ratings = sum(1 for book in all_scraped_data if book.get('rating'))
            avg_desc_length = sum(len(book.get('description', '')) for book in all_scraped_data) / len(all_scraped_data) if all_scraped_data else 0
            
            logger.info(f"\n🎉 ALL BATCHES COMPLETED!")
            logger.info(f"📊 Total books scraped: {len(all_scraped_data)}")
            logger.info(f"⭐ Total ratings found: {total_ratings} ({total_ratings/len(all_scraped_data)*100:.1f}%)")
            logger.info(f"📄 Average description length: {avg_desc_length:.0f} characters")
            
            print(f"\n📖 FINAL RESULTS:")
            print(f"Total books: {len(all_scraped_data)}")
            print(f"Success rate (ratings): {total_ratings/len(all_scraped_data)*100:.1f}%")
            print(f"Average description length: {avg_desc_length:.0f} characters")
        
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        import traceback
        logger.error(f"📋 Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    main()
