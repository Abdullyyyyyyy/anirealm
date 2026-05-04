# AniRealm 🎌

> **An Emotion-Aware Anime Journaling and Recommendation Platform**
> Integrating Multi-Model Sentiment Analysis and User Reflection for Personalised Anime Discovery

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.x-green.svg)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

---

## 📖 About

AniRealm is a full-stack web application developed as a Final Year Project for the **BSc Computer Science and Software Engineering** degree at the **University of Roehampton** (2024/2025).

The platform allows anime viewers to write structured episode reflections and receive automatic sentiment analysis from **three AI models simultaneously** — VADER, TextBlob, and DistilBERT — compared side by side. Model performance is evaluated using accuracy, precision, recall, and F1-score against user-supplied true labels.

**Student:** Abdulrahman Nooh
**Supervisor:** Dr Mamoona Humayun
**University:** University of Roehampton

---

## ✨ Features

| Feature | Description |
|---|---|
| 📓 **Multi-Model Journal** | Write episode reflections and get VADER, TextBlob, and DistilBERT results simultaneously |
| 📋 **Journal History** | Search and filter past entries by anime title or sentiment label |
| 🎬 **Watchlist Tracker** | Track anime with cover images and episode progress via Jikan API |
| 💜 **Mood Tracker** | Visualise sentiment trends over time with Chart.js line, doughnut, and bar charts |
| ⚔️ **Sentiment Clash** | Compare two anime head-to-head by community sentiment scores |
| 🌍 **Community Feed** | Browse all user entries ranked by helpful votes with trust-level filtering |
| 🏆 **Leaderboard** | Users ranked by loyalty points with trust level badges |
| 👤 **Profile** | View loyalty points, trust level progress, and journal statistics |
| 📊 **Evaluation** | Accuracy, precision, recall, and F1-score per model using scikit-learn |
| 🔒 **Authentication** | Secure signup and login with PBKDF2-SHA256 password hashing |

---

## 🤖 Sentiment Analysis Models

AniRealm compares three fundamentally different NLP approaches on the same reflection text:

| Model | Type | Strength | Library |
|---|---|---|---|
| **VADER** | Lexicon rule-based | Fast, handles informal text | vaderSentiment |
| **TextBlob** | Lexicon polarity-based | Independent baseline comparison | textblob |
| **DistilBERT** | Transformer deep learning | Context-aware, highest accuracy | HuggingFace Transformers |

DistilBERT uses the `distilbert-base-uncased-finetuned-sst-2-english` checkpoint fine-tuned on the Stanford Sentiment Treebank dataset.

---

## 🗂️ Project Structure

```
anirealm/
│
├── app.py                  # All Flask routes and API endpoints
├── models.py               # SQLAlchemy database models
├── sentiment_models.py     # VADER, TextBlob, DistilBERT functions
├── evaluation.py           # Scikit-learn evaluation metrics
├── requirements.txt        # Python dependencies
├── .gitignore              # Excludes venv, database, cache
│
├── static/
│   ├── style.css           # Anime-themed stylesheet
│   ├── app.js              # Journal page JavaScript
│   └── pages.js            # All other pages JavaScript
│
└── templates/
    ├── home.html
    ├── journal.html
    ├── history.html
    ├── comparison.html
    ├── evaluation.html
    ├── watchlist.html
    ├── mood.html
    ├── clash.html
    ├── leaderboard.html
    ├── feed.html
    ├── profile.html
    ├── about.html
    ├── login.html
    └── signup.html
```

---

## 🗄️ Database Models

**User**
- id, username, email, password_hash
- loyalty_points, trust_level, created_at

**JournalEntry**
- id, user_id, anime_title, episode, rating
- reflection_text, true_label
- vader_label, vader_score
- textblob_label, textblob_score
- transformer_label, transformer_score
- helpful_votes, created_at

**WatchlistEntry**
- id, user_id, anime_title, anime_image
- anime_episodes, episodes_watched
- status, created_at, updated_at

**Vote**
- id, user_id, entry_id, created_at
- UNIQUE constraint on (user_id, entry_id)

---

## 🏅 Loyalty and Trust System

| Action | Points Awarded |
|---|---|
| Submit a journal entry | +10 points |
| All three models agree | +5 bonus points |
| Receive a helpful vote | +5 points |

| Trust Level | Points Required |
|---|---|
| 🌱 New User | 0 – 49 points |
| ⭐ Regular Reviewer | 50 – 99 points |
| 🌀 Trusted Fan | 100 – 199 points |
| 👑 Elite Recommender | 200+ points |

---

## 🚀 Installation and Setup

### Prerequisites

- Python 3.10 or higher
- pip
- Git

### Step 1 — Clone the repository

```bash
git clone https://github.com/Abdullyyyyyyy/anirealm.git
cd anirealm
```

### Step 2 — Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Run the application

```bash
python app.py
```

### Step 5 — Open in browser

```
http://127.0.0.1:5000
```

> **Note:** On first run, DistilBERT will download approximately 250MB of model weights. This only happens once. The model loads at server startup — you will see a confirmation message in the terminal when it is ready.

---

## 📡 API Routes

| Method | Route | Description | Auth Required |
|---|---|---|---|
| GET | `/` | Home page | Yes |
| GET | `/journal` | Journal entry form | Yes |
| POST | `/api/journal` | Submit journal entry, run all 3 models | Yes |
| GET | `/history` | Journal history page | Yes |
| GET | `/api/history` | Get user journal entries | Yes |
| DELETE | `/api/journal/<id>` | Delete journal entry | Yes |
| GET | `/watchlist` | Watchlist page | Yes |
| POST | `/api/watchlist` | Add anime to watchlist | Yes |
| PUT | `/api/watchlist/<id>` | Update watch status/progress | Yes |
| DELETE | `/api/watchlist/<id>` | Remove from watchlist | Yes |
| GET | `/api/search-anime` | Search anime via Jikan API | Yes |
| GET | `/mood` | Mood tracker page | Yes |
| GET | `/api/mood` | Get mood data for charts | Yes |
| GET | `/clash` | Sentiment clash page | Yes |
| POST | `/api/clash` | Compare two anime sentiment | Yes |
| GET | `/leaderboard` | Leaderboard page | No |
| GET | `/api/leaderboard` | Get ranked users | No |
| GET | `/feed` | Community feed page | No |
| GET | `/api/feed` | Get community entries | No |
| POST | `/api/vote/<id>` | Vote on an entry | Yes |
| GET | `/evaluation` | Evaluation page | Yes |
| GET | `/api/evaluation` | Get model metrics | Yes |
| GET | `/profile` | Profile page | Yes |
| GET | `/api/profile` | Get user profile data | Yes |
| GET | `/comparison` | Model comparison page | Yes |
| GET | `/api/comparison` | Get comparison data | Yes |
| GET | `/about` | About page | No |
| GET | `/login` | Login page | No |
| POST | `/login` | Process login | No |
| GET | `/signup` | Signup page | No |
| POST | `/signup` | Process signup | No |
| GET | `/logout` | Logout user | Yes |

---

## 🔒 Security Features

- **Password hashing** — PBKDF2-SHA256 with auto-generated salt via Werkzeug
- **Session management** — Flask-Login with secure session cookies
- **Route protection** — @login_required on all authenticated pages
- **SQL injection prevention** — All queries parameterised via SQLAlchemy ORM
- **Input validation** — Server-side validation on all form submissions
- **Ownership checks** — Users can only delete their own entries
- **Duplicate vote prevention** — Unique constraint on Vote model

---

## 📦 Dependencies

```
Flask
Flask-SQLAlchemy
Flask-Login
Werkzeug
vaderSentiment
textblob
transformers
torch
scikit-learn
requests
```

Install all with:
```bash
pip install -r requirements.txt
```

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Database | SQLite, SQLAlchemy ORM |
| Authentication | Flask-Login, Werkzeug |
| NLP Model 1 | VADER (vaderSentiment) |
| NLP Model 2 | TextBlob |
| NLP Model 3 | DistilBERT (HuggingFace Transformers) |
| Evaluation | Scikit-learn |
| Frontend | HTML, CSS, JavaScript |
| Charts | Chart.js (Cloudflare CDN) |
| Anime Data | Jikan API (MyAnimeList) |
| Fonts | Google Fonts (Nunito, Bangers) |
| Version Control | Git, GitHub |

---

## 🎓 Academic Context

This project was developed as a Final Year Project investigating:

1. How a web-based system can integrate anime tracking, user journaling, and sentiment-aware processing to support personalised recommendations and improved user experience.

2. To what extent sentiment analysis of user journal reflections can improve the relevance of anime recommendations compared to traditional genre-based approaches.

The multi-model comparison between VADER, TextBlob, and DistilBERT constitutes the primary NLP academic contribution of the project, demonstrating the difference between lexicon-based and transformer-based sentiment classification on user-generated informal text.

---

## 🔮 Future Work

- Implement the recommendation engine using stored sentiment history and watchlist data
- Add RoBERTa as a fourth sentiment model for extended comparison
- Deploy to cloud environment using Gunicorn and Nginx
- Conduct formal usability testing using the System Usability Scale
- Add mobile responsive design for smaller screens
- Implement account management including password reset and GDPR-compliant deletion
- Expand evaluation dataset with more labelled entries for statistically significant results

---

## 📄 License

This project is submitted in partial fulfilment of the requirements for the degree of BSc Computer Science and Software Engineering at the University of Roehampton. All rights reserved by the author.

---

*AniRealm © 2024/2025 — Anime Sentiment Journal*