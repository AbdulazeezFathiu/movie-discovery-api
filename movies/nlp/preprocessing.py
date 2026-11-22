import re

from nltk.stem import PorterStemmer
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS


stemmer = PorterStemmer()


def preprocess_text(text):
    if not text:
        return ""

    # Convert text to lowercase
    text = text.lower()

    # Remove punctuation and numbers
    text = re.sub(r"[^a-z\s]", " ", text)

    # Split text into individual words
    words = text.split()

    # Remove stop words
    words = [
        word for word in words
        if word not in ENGLISH_STOP_WORDS
    ]

    # Reduce words to their root forms
    words = [stemmer.stem(word) for word in words]

    return " ".join(words)