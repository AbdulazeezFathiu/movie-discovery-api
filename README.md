# 🎬 Movie Discovery API

### An AI-Powered Movie Discovery and Recommendation System

A production-deployed RESTful API built with **Python, Django REST Framework, PostgreSQL, and Natural Language Processing (NLP)**.

The application goes beyond traditional movie search by integrating semantic search, hybrid retrieval, mood-based discovery, and personalized recommendations. It combines backend engineering with practical AI model integration to provide intelligent movie discovery experiences.

**Live API:** https://movie-discovery-api-1.onrender.com/

**Interactive API Documentation:** https://movie-discovery-api-1.onrender.com/api/docs/

---

## Overview

The Movie Discovery API is a backend system designed to help users discover movies through both traditional filtering and AI-powered recommendations.

It integrates movie metadata from **The Movie Database (TMDB)** and uses pretrained language models to understand the meaning behind search queries and movie descriptions.

The project demonstrates how machine learning capabilities can be incorporated into a REST API while addressing practical deployment challenges such as database persistence, authentication, inference memory consumption, and production hosting.

## Key Features

### Movie Management
- Movie retrieval, creation, updating, and deletion
- Search by movie title and description
- Filtering by genre and language
- Sorting and pagination
- TMDB API integration for importing movie metadata
- Actor, director, and genre relationships

### Authentication and User Features
- JWT-based user authentication
- User registration and login
- Protected user profile endpoints
- Personal watchlists
- Movie ratings and reviews
- Watched-movie tracking
- Personalized movie recommendations

### AI-Powered Movie Discovery

**Semantic Search**

Uses the pretrained `all-MiniLM-L6-v2` Sentence Transformer model to represent text as 384-dimensional embeddings.

User queries are compared against stored movie embeddings using cosine similarity, enabling searches based on meaning rather than exact keyword matching.

**Natural Language Search**

Uses TF-IDF vectorization to retrieve movies based on textual relevance.

**Hybrid Search**

Combines semantic similarity and TF-IDF keyword relevance using a weighted ranking strategy.

The current implementation uses:

- 70% semantic similarity
- 30% keyword relevance

These weights are configurable and can be evaluated against retrieval-quality benchmarks.

**Mood-Based Recommendations**

Converts supported user-selected moods into descriptive search queries and retrieves relevant movies using semantic similarity.

**Personalized Recommendations**

Generates content-based recommendations using a weighted representation of positively rated and watchlisted movies.

The system excludes movies the user has already rated, watched, or added to their watchlist.

## Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python |
| Backend Framework | Django, Django REST Framework |
| Database | PostgreSQL |
| Authentication | JWT, SimpleJWT |
| External API | TMDB |
| AI Model | all-MiniLM-L6-v2 |
| AI Inference | ONNX Runtime |
| NLP | Sentence Transformers, NLTK, scikit-learn |
| Numerical Computing | NumPy |
| API Documentation | Swagger UI, drf-spectacular |
| Deployment | Render, Gunicorn, WhiteNoise |
| Testing | Django Test Framework, unittest.mock |
| Version Control | Git, GitHub |

## System Architecture

```text
Client / Postman / Swagger UI
              |
              v
       Django REST API
              |
       JWT Authentication
              |
       Application Services
              |
       +------+-------+
       |              |
       v              v
  PostgreSQL      AI Search Engine
       |              |
       |        +-----+------+
       |        |            |
       |     ONNX Model   TF-IDF
       |        |            |
       |        +-----+------+
       |              |
       |       Hybrid Ranking
       |              |
       +------+-------+
              |
              v
         JSON Response
```

Movie metadata is retrieved from TMDB and persisted in PostgreSQL.

Movie embeddings are generated offline and stored in the database. At request time, the semantic search engine uses ONNX Runtime to encode the user query and compare it against the existing movie vectors.

## AI Inference Optimization

An important engineering challenge encountered during deployment was the memory consumption of PyTorch-based inference.

The initial deployment exceeded the memory available on the hosting instance.

To address this, the application was optimized to:

1. Use a pretrained ONNX version of the sentence embedding model.
2. Run query inference through ONNX Runtime instead of loading PyTorch.
3. Store generated movie embeddings persistently in PostgreSQL.
4. Avoid regenerating movie embeddings for every search request.
5. Use lazy initialization to reduce unnecessary startup memory consumption.

The optimized semantic search implementation was successfully tested on the deployed API.

## API Capabilities

| Feature | HTTP Methods |
|---|---|
| Movie collection | GET, POST |
| Individual movie | GET, PUT, PATCH, DELETE |
| User registration | POST |
| JWT login and refresh | POST |
| User profile | GET |
| Watchlist | GET, POST, DELETE |
| Reviews | GET, POST, PATCH, DELETE |
| Watched movies | GET, POST, DELETE |
| Semantic search | GET |
| Natural-language search | GET |
| Hybrid search | GET |
| Mood-based recommendations | GET |
| Personalized recommendations | GET |

For exact endpoint paths, request schemas, authentication requirements, and response formats, visit the [interactive Swagger documentation](https://movie-discovery-api-1.onrender.com/api/docs/).

### Semantic Search Example

**Request**

```http
GET /api/movies/semantic-search/?q=space
```

**Example Response Structure**

```json
{
  "query": "space",
  "count": 1,
  "search_type": "semantic",
  "results": [
    {
      "id": 35,
      "title": "Project Hail Mary",
      "overview": "Science teacher Ryland Grace wakes up on a spaceship...",
      "similarity_score": 0.3408
    }
  ]
}
```

### Hybrid Search Example

**Request**

```http
GET /api/movies/hybrid-search/?q=astronauts%20exploring%20distant%20planets
```

Hybrid search combines semantic similarity with character n-gram TF-IDF keyword relevance.

The API returns semantic, keyword, and combined ranking scores for each result.

## Local Installation

### Prerequisites

- Python 3.12
- PostgreSQL
- Git
- A TMDB API access token

### 1. Clone the repository

```bash
git clone https://github.com/AbdulazeezFathiu/movie-discovery-api.git
cd movie-discovery-api
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

On Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root.

```dotenv
DJANGO_SECRET_KEY=your_secret_key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=127.0.0.1
DB_PORT=5432

TMDB_ACCESS_TOKEN=your_tmdb_access_token
```

Keep this file private.

### 5. Apply migrations

```bash
python manage.py migrate
```

### 6. Import movies

```bash
python manage.py import_movies --pages 2
```

### 7. Generate movie embeddings

```bash
python manage.py generate_embeddings
```

Use `--force` when embeddings need to be regenerated after changing the movie representation.

### 8. Start the development server

```bash
python manage.py runserver --noreload
```

The API will be available at:

http://127.0.0.1:8000/

Swagger documentation:

http://127.0.0.1:8000/api/docs/

**Note:** ONNX semantic inference requires the compatible model and tokenizer files in the expected `onnx_model/` directory. The production build downloads these model assets during deployment.

## Authentication

Protected endpoints require a JWT access token.

**Login**

```http
POST /api/auth/login/
Content-Type: application/json
```

```json
{
  "username": "example_user",
  "password": "your_password"
}
```

Use the returned access token:

```http
Authorization: Bearer YOUR_ACCESS_TOKEN
```

Never commit real credentials or access tokens.

## Automated Testing

The application includes automated tests covering:

- JWT authentication
- Watchlist management
- Movie reviews
- Watched-movie tracking
- Natural-language search
- Semantic search
- Personalized recommendations
- Hybrid search

Run the complete test suite:

```bash
python manage.py test
```

**Latest local test run: 44 tests completed successfully.**

AI tests use controlled embeddings and mocked model inference to verify ranking behavior without repeatedly loading heavyweight ML models.

## Deployment

The application is deployed using Render.

Production configuration includes:

- Django served with Gunicorn
- Managed PostgreSQL
- Environment-based configuration
- WhiteNoise static file serving
- Swagger/OpenAPI documentation
- Offline movie embedding generation
- ONNX-based semantic inference

**Live API:** https://movie-discovery-api-1.onrender.com/

**API Documentation:** https://movie-discovery-api-1.onrender.com/api/docs/

Hosting resources may be limited, and services on free-tier infrastructure may experience cold starts or availability limitations.

## Engineering Challenges and Solutions

| Challenge | Solution |
|---|---|
| High AI inference memory usage | Replaced PyTorch inference with ONNX Runtime |
| Repeated embedding generation | Persisted movie embeddings in PostgreSQL |
| Semantic matching limitations | Implemented weighted semantic + TF-IDF hybrid ranking |
| Unauthorized access | Added JWT authentication and endpoint permissions |
| API discoverability | Integrated Swagger/OpenAPI documentation |
| Regression prevention | Added automated API and recommendation tests |

## Future Improvements

- Movie metadata validation and duplicate detection
- Improved retrieval relevance and ranking evaluation
- Dynamic hybrid-search weight optimization
- Recommendation quality benchmarking
- Redis caching
- Background jobs for movie imports and embedding updates
- More scalable vector similarity search
- Monitoring and performance profiling

## Project Focus

This project demonstrates practical experience in:

**Backend Engineering**
- REST API design
- Relational data modeling
- Authentication and authorization
- Database integration
- Automated testing
- Production deployment

**Applied AI Engineering**
- Pretrained model integration
- Sentence embeddings
- Semantic similarity
- Hybrid information retrieval
- Content-based recommendation systems
- Memory-efficient AI inference

---

Built with Python, Django REST Framework, PostgreSQL, and ONNX Runtime.