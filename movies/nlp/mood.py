
from .semantic_search import semantic_movie_search


MOOD_DESCRIPTIONS = {
    "happy": (
        "A cheerful uplifting funny movie about friendship, "
        "love, joy, laughter and happy experiences"
    ),
    "sad": (
        "An emotional heartbreaking dramatic story about "
        "loss, grief, relationships and difficult life experiences"
    ),
    "excited": (
        "An action packed adventure filled with thrilling missions, "
        "danger, suspense, fast paced events and excitement"
    ),
    "scared": (
        "A terrifying horror story with supernatural creatures, "
        "dark mysteries, fear, danger and suspense"
    ),
    "romantic": (
        "A touching romantic love story about relationships, "
        "falling in love, affection and emotional connection"
    ),
    "curious": (
        "A thought provoking science fiction or mystery story "
        "about exploration, discoveries, technology, space and secrets"
    ),
}


def recommend_by_mood(mood, limit=5):
    mood = mood.strip().lower()

    if mood not in MOOD_DESCRIPTIONS:
        return None

    description = MOOD_DESCRIPTIONS[mood]

    return semantic_movie_search(
        query=description,
        limit=limit
    )
