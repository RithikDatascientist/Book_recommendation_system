Book Recommendation System
A sophisticated content-based book recommendation system that uses Natural Language Processing techniques to analyze book descriptions and metadata, providing personalized book suggestions based on textual similarity and content analysis.

🚀 Features
    Content-Based Filtering: Recommends books based on intrinsic features rather than user ratings

    Advanced NLP: Implements Bag of Words model using TF-IDF Vectorization for optimal performance

    Similarity Measurement: Uses cosine similarity to find related books

    Interactive Web Interface: Built with Streamlit for easy user interaction

    Real-time Recommendations: Get instant book suggestions based on your selection

📋 System Requirements
    Minimum Requirements (Using Pre-built Dataset)
    Python: 3.11 

    RAM: 8-16 GB (when using books_dataset.csv)

    Storage: 2 GB free space

    For Web Scraping (Optional)
    RAM: 24-30 GB minimum (32 GB+ recommended)

    CPU: Multi-core processor for faster processing(intel i5)

    Internet Connection: Required for scraping from Goodreads

⚠️ Important Notes
    Two Usage Options
    Option 1: Use Pre-built Dataset (Recommended)
    Use the included books_dataset.csv file

    RAM Required: 8-16 GB

    Setup Time: 5-10 minutes

    Best for: Quick setup and testing

    Option 2: Web Scraping (Advanced Users)
    Scrape fresh data from Goodreads using data_scraper.py

    RAM Required: 24-30 GB minimum

    Setup Time: Several hours

    Best for: Getting latest data or customizing dataset

    Memory Requirements by Approach
    TF-IDF with pre-built dataset: 8-16 GB RAM

    TF-IDF with full scraping: 24-30 GB RAM

    Count Vectorizer: 32 GB+ RAM (not recommended)

🛠️ Installation
    Clone the repository
    
```bash
    git clone [https://github.com/RithikDatascientist/Book_recommendation_system.git]
    cd book-recommendation-system
    Create virtual environment
```
    
```bash
    python -m venv book_rec_env
    source book_rec_env/bin/activate  # On Windows: book_rec_env\Scripts\activate
    Install dependencies
```
```bash
    pip install -r requirements.txt
    📁 Project Structure
    text
    book-recommendation-system/
    ├── app.py                           # Streamlit web application
    ├── Books_recommendation_model.ipynb # Model development notebook
    ├── data_scraper.py                  # Web scraping script (optional)
    ├── books_dataset.csv                # Pre-built dataset (recommended)
    ├── all_book_urls_combined.csv       # URLs for scraping (optional)
    ├── books_dict.pkl                   # Preprocessed data (generated)
    ├── tfidf_matrix.pkl                 # TF-IDF matrix (generated)
    └── README.md                        # This file
```
🚀 Quick Start

    Option 1: Use Pre-built Dataset (Recommended for Most Users)
    Perfect if you have 8-16 GB RAM and want quick setup:

    Use the provided dataset

    The books_dataset.csv file contains pre-processed book data

    No scraping required - saves time and memory

    Run the preprocessing notebook

```bash
    jupyter notebook Books_recommendation_model.ipynb
```
Load data from books_dataset.csv instead of scraping
Generate the required pickle files
Launch the application

```bash
    streamlit run app.py
```
Option 2: Web Scraping (For Advanced Users with 24+ GB RAM)
Only choose this if you:

Have 24-30 GB+ RAM available

Want the latest data from Goodreads

Need to customize the dataset

Prepare for scraping

Ensure all_book_urls_combined.csv is available

Verify system meets memory requirements

Run the scraper (Optional - takes several hours)

```bash
    python data_scraper.py
    # Process the scraped data
```

```bash
    jupyter notebook Books_recommendation_model.ipynb
    # Launch the application
```
```bash
    streamlit run app.py
```
📊 Dataset Information
    Pre-built Dataset (books_dataset.csv)
    Size: Optimized subset of books

    Memory Friendly: Works with 8-16 GB RAM

    Ready to Use: No scraping required

    Genres: Mystery, Romance, Science Fiction, Non-Fiction

    Features: Title, Author, Description, Genres, Ratings

    Full Scraping Dataset
    Source: Live Goodreads data

    Size: 51,000+ books

    Memory Intensive: Requires 24-30 GB RAM

    Fresh Data: Latest book information

🔧 Configuration Options
For Limited RAM Systems (< 16GB)
Use the pre-built dataset approach:

python
# In the notebook, load from CSV instead of scraping
books = pd.read_csv('books_dataset.csv')
For High-RAM Systems (24+ GB)
You can choose either approach:

python
# Option 1: Use pre-built dataset (faster)
books = pd.read_csv('books_dataset.csv')

# Option 2: Use scraped data (latest)
# Run data_scraper.py first, then load the results
Memory Optimization Settings
TF-IDF Configuration (Recommended):

python
from sklearn.feature_extraction.text import TfidfVectorizer
vectorizer = TfidfVectorizer(max_features=10000, stop_words='english')
For even lower memory usage:

python
vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')

🎯 How It Works
    Data Loading: Load from books_dataset.csv OR scraped data

    Preprocessing: Clean and process book information

    Feature Extraction: Create TF-IDF vectors from descriptions and genres

    Similarity Calculation: Compute cosine similarity between books

    Recommendation: Find and display most similar books

🐛 Troubleshooting
    Memory Issues
    Problem: "Memory Error" or system freezing
    Solutions:

    Use books_dataset.csv instead of scraping

    Reduce max_features in TF-IDF vectorizer

    Close other applications

    Use a system with more RAM

    File Not Found Errors
    Problem: Cannot find dataset files
    Solutions:

    Ensure books_dataset.csv is in project directory

    Check file paths in the notebook

    Download the dataset if missing

    Slow Performance
    Problem: System running slowly
    Solutions:

    Use pre-built dataset instead of scraping

    Reduce dataset size in notebook

    Use SSD storage if available

📈 Performance Comparison
    Approach	RAM Required	Setup Time	Data Freshness	Recommended For
    Pre-built Dataset	8-16 GB	5-10 minutes	Static	Most Users
    Web Scraping	24-30 GB	2-4 hours	Latest	Advanced Users

🤝 Contributing
    Fork the repository

    Choose your approach (dataset vs scraping)

    Test with your system specifications

    Submit pull requests with performance notes

📝 Usage Recommendations
Choose Pre-built Dataset If:
    You have 8-16 GB RAM

    You want quick setup

    You're learning/prototyping

    Static data is sufficient

Choose Web Scraping If:
    You have 24+ GB RAM

    You need latest data

    You want to customize the dataset

    You have time for longer setup