# Import necessary libraries
import pickle as pkl
import streamlit as st 
import pandas as pd 
from sklearn.metrics.pairwise import cosine_similarity

# Load the pre-processed books data from pickle file
books_dict = pkl.load(open("books_dict.pkl","rb"))
books = pd.DataFrame(books_dict)

# Load the pre-computed TF-IDF matrix from pickle file
# This matrix contains the numerical representation of book features
tfidf_matrix = pkl.load(open("tfidf_matrix.pkl","rb"))

# Create a pandas Series that maps book titles to their indices
# drop_duplicates() ensures each title appears only once
indices = pd.Series(books.index, index=books['title']).drop_duplicates()

def recommend_books(selected_book, n=5):
    """
    Recommend books similar to the selected book using cosine similarity
    
    Args:
        selected_book (str): Title of the book to base recommendations on
        n (int): Number of recommendations to return (default: 5)
    
    Returns:
        list: List of recommended book titles
    """
    # Get the index of the selected book
    idx = indices[selected_book]
    
    # Get the TF-IDF vector for the selected book
    target_vec = tfidf_matrix[idx]
    
    # Calculate cosine similarity between selected book and all other books
    sim_scores = cosine_similarity(target_vec, tfidf_matrix).flatten()
    
    # Set similarity score of the book with itself to 0 to exclude it from recommendations
    sim_scores[idx] = 0

    # Get indices of books sorted by similarity score (highest first)
    top_indices = sim_scores.argsort()[::-1]
    
    # Filter out any invalid indices and get top n recommendations
    top_indices = [i for i in top_indices if i < len(books)][:n]

    # Get the titles of the top recommended books
    top_titles = books.iloc[top_indices]['title']
    return top_titles.tolist()

# Streamlit UI components
st.title("Book Recommendation System")

# Create a selectbox for users to choose a book
# The selectbox is populated with all book titles from the dataset
selected_book = st.selectbox(
    "Select or search for a book", books["title"].values
)

# Create a button to trigger the recommendation process
if st.button("Recommend"):
    # Get recommendations for the selected book
    recommendations = recommend_books(selected_book)
    
    # Display each recommended book title
    for title in recommendations:
        st.write(title)