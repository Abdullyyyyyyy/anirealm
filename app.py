from flask import Flask, jsonify, request, render_template, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, JournalEntry, WatchlistEntry, Vote, calculate_trust_level
from sentiment_models import vader_sentiment, textblob_sentiment, transformer_sentiment
from evaluation import evaluate_model
from werkzeug.security import generate_password_hash
from datetime import datetime
import re
import requests

app = Flask(__name__)
app.config["SECRET_KEY"] = "anirealm-secret-key-2024"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///anirealm.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access this page."


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Helpers

def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)


def is_strong_password(password):
    return (
        len(password) >= 8 and
        any(c.isupper() for c in password) and
        any(c.isdigit() for c in password)
    )


def fetch_anime_info(title):
    try:
        res = requests.get(
            "https://api.jikan.moe/v4/anime",
            params={"q": title, "limit": 1},
            timeout=5
        )
        data = res.json()
        if data.get("data"):
            anime = data["data"][0]
            return {
                "image": anime["images"]["jpg"]["image_url"],
                "episodes": anime.get("episodes"),
                "title": anime["title"]
            }
    except Exception:
        pass
    return {"image": None, "episodes": None, "title": title}


# Page routes

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/journal")
@login_required
def journal_page():
    return render_template("journal.html")


@app.route("/history")
@login_required
def history_page():
    return render_template("history.html")


@app.route("/comparison")
@login_required
def comparison_page():
    return render_template("comparison.html")


@app.route("/evaluation")
@login_required
def evaluation_page():
    return render_template("evaluation.html")


@app.route("/about")
def about_page():
    return render_template("about.html")


@app.route("/profile")
@login_required
def profile_page():
    return render_template("profile.html")


@app.route("/watchlist")
@login_required
def watchlist_page():
    return render_template("watchlist.html")


@app.route("/leaderboard")
def leaderboard_page():
    return render_template("leaderboard.html")


@app.route("/mood")
@login_required
def mood_page():
    return render_template("mood.html")


@app.route("/clash")
@login_required
def clash_page():
    return render_template("clash.html")


@app.route("/feed")
def feed_page():
    return render_template("feed.html")


# Auth routes

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not username or not email or not password:
            flash("All fields are required.", "error")
            return render_template("signup.html")

        if not is_valid_email(email):
            flash("Please enter a valid email address.", "error")
            return render_template("signup.html")

        if not is_strong_password(password):
            flash("Password must be at least 8 characters with one uppercase letter and one number.", "error")
            return render_template("signup.html")

        if password != confirm:
            flash("Passwords do not match.", "error")
            return render_template("signup.html")

        if User.query.filter_by(username=username).first():
            flash("Username already taken.", "error")
            return render_template("signup.html")

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "error")
            return render_template("signup.html")

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash("Invalid email or password.", "error")
            return render_template("login.html")

        login_user(user)
        return redirect(url_for("home"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


# Journal API

@app.route("/api/journal", methods=["POST"])
@login_required
def create_journal():
    data = request.get_json(silent=True) or {}

    anime_title = (data.get("anime_title") or "").strip()
    episode = data.get("episode")
    rating = data.get("rating")
    reflection_text = (data.get("reflection_text") or "").strip()
    true_label = (data.get("true_label") or "").strip()

    if not anime_title:
        return jsonify({"error": "Anime title is required"}), 400
    if not isinstance(episode, int) or episode < 1:
        return jsonify({"error": "Episode must be a number greater than 0"}), 400
    if not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({"error": "Rating must be between 1 and 5"}), 400
    if not reflection_text:
        return jsonify({"error": "Reflection is required"}), 400

    if true_label not in ["Positive", "Neutral", "Negative"]:
        true_label = None

    vader_result = vader_sentiment(reflection_text)
    textblob_result = textblob_sentiment(reflection_text)
    transformer_result = transformer_sentiment(reflection_text)

    entry = JournalEntry(
        user_id=current_user.id,
        anime_title=anime_title,
        episode=episode,
        rating=rating,
        reflection_text=reflection_text,
        true_label=true_label,
        vader_label=vader_result["label"],
        vader_score=vader_result["score"],
        textblob_label=textblob_result["label"],
        textblob_score=textblob_result["score"],
        transformer_label=transformer_result["label"],
        transformer_score=transformer_result["score"],
    )

    db.session.add(entry)

    points_earned = 10
    if vader_result["label"] == textblob_result["label"] == transformer_result["label"]:
        points_earned += 5

    current_user.add_points(points_earned)
    db.session.commit()

    return jsonify({
        "message": "Journal entry saved",
        "journal_id": entry.id,
        "points_earned": points_earned,
        "total_points": current_user.loyalty_points,
        "trust_level": current_user.trust_level,
        "vader": vader_result,
        "textblob": textblob_result,
        "transformer": transformer_result
    }), 201


@app.route("/api/journal", methods=["GET"])
@login_required
def list_journals():
    anime_title = request.args.get("anime_title", "").strip()
    vader_label = request.args.get("vader_label", "").strip()

    query = JournalEntry.query.filter_by(user_id=current_user.id)

    if anime_title:
        query = query.filter(JournalEntry.anime_title.ilike(f"%{anime_title}%"))
    if vader_label:
        query = query.filter(JournalEntry.vader_label == vader_label)

    entries = query.order_by(JournalEntry.created_at.desc()).limit(50).all()
    return jsonify([e.to_dict(current_user.id) for e in entries])


@app.route("/api/journal/<int:entry_id>", methods=["DELETE"])
@login_required
def delete_journal(entry_id):
    entry = JournalEntry.query.filter_by(
        id=entry_id, user_id=current_user.id
    ).first_or_404()
    db.session.delete(entry)
    db.session.commit()
    return jsonify({"message": "Journal entry deleted"})


@app.route("/api/journal/<int:entry_id>", methods=["PUT"])
@login_required
def update_journal(entry_id):
    entry = JournalEntry.query.filter_by(
        id=entry_id, user_id=current_user.id
    ).first_or_404()

    data = request.get_json(silent=True) or {}
    reflection_text = (data.get("reflection_text") or "").strip()
    rating = data.get("rating")
    true_label = (data.get("true_label") or "").strip()

    if not reflection_text:
        return jsonify({"error": "Reflection is required"}), 400
    if not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({"error": "Rating must be between 1 and 5"}), 400

    vader_result = vader_sentiment(reflection_text)
    textblob_result = textblob_sentiment(reflection_text)
    transformer_result = transformer_sentiment(reflection_text)

    entry.reflection_text = reflection_text
    entry.rating = rating
    entry.true_label = true_label if true_label in ["Positive", "Neutral", "Negative"] else None
    entry.vader_label = vader_result["label"]
    entry.vader_score = vader_result["score"]
    entry.textblob_label = textblob_result["label"]
    entry.textblob_score = textblob_result["score"]
    entry.transformer_label = transformer_result["label"]
    entry.transformer_score = transformer_result["score"]

    db.session.commit()
    return jsonify({"message": "Entry updated successfully"})


# Vote API

@app.route("/api/journal/<int:entry_id>/vote", methods=["POST"])
@login_required
def vote_entry(entry_id):
    entry = JournalEntry.query.get_or_404(entry_id)

    if entry.user_id == current_user.id:
        return jsonify({"error": "You cannot vote on your own entry"}), 400

    existing = Vote.query.filter_by(
        user_id=current_user.id, entry_id=entry_id
    ).first()

    if existing:
        db.session.delete(existing)
        entry.helpful_votes = max(0, entry.helpful_votes - 1)
        db.session.commit()
        return jsonify({"message": "Vote removed", "votes": entry.helpful_votes})

    vote = Vote(user_id=current_user.id, entry_id=entry_id)
    db.session.add(vote)
    entry.helpful_votes += 1
    entry.author.add_points(5)
    db.session.commit()
    return jsonify({"message": "Vote added", "votes": entry.helpful_votes})


# Evaluation API

@app.route("/api/evaluation", methods=["GET"])
@login_required
def model_evaluation():
    entries = JournalEntry.query.filter(
        JournalEntry.user_id == current_user.id,
        JournalEntry.true_label.isnot(None)
    ).all()

    if not entries:
        return jsonify({"message": "No labelled entries found for evaluation."})

    y_true = [e.true_label for e in entries]

    return jsonify({
        "vader": evaluate_model(y_true, [e.vader_label for e in entries]),
        "textblob": evaluate_model(y_true, [e.textblob_label for e in entries]),
        "transformer": evaluate_model(y_true, [e.transformer_label for e in entries]),
        "total_labelled_entries": len(entries)
    })


# Profile API

@app.route("/api/profile")
@login_required
def get_profile():
    total_entries = JournalEntry.query.filter_by(user_id=current_user.id).count()
    watchlist_count = WatchlistEntry.query.filter_by(user_id=current_user.id).count()
    completed_count = WatchlistEntry.query.filter_by(
        user_id=current_user.id, status="Completed"
    ).count()

    return jsonify({
        "username": current_user.username,
        "email": current_user.email,
        "loyalty_points": current_user.loyalty_points,
        "trust_level": current_user.trust_level,
        "total_entries": total_entries,
        "watchlist_count": watchlist_count,
        "completed_count": completed_count,
        "member_since": current_user.created_at.strftime("%B %Y")
    })


# Watchlist API

@app.route("/api/watchlist", methods=["GET"])
@login_required
def get_watchlist():
    status = request.args.get("status", "").strip()
    query = WatchlistEntry.query.filter_by(user_id=current_user.id)
    if status:
        query = query.filter_by(status=status)
    entries = query.order_by(WatchlistEntry.updated_at.desc()).all()
    return jsonify([e.to_dict() for e in entries])


@app.route("/api/watchlist", methods=["POST"])
@login_required
def add_watchlist():
    data = request.get_json(silent=True) or {}
    anime_title = (data.get("anime_title") or "").strip()

    if not anime_title:
        return jsonify({"error": "Anime title is required"}), 400

    existing = WatchlistEntry.query.filter_by(
        user_id=current_user.id, anime_title=anime_title
    ).first()
    if existing:
        return jsonify({"error": "Already in your watchlist"}), 400

    info = fetch_anime_info(anime_title)

    entry = WatchlistEntry(
        user_id=current_user.id,
        anime_title=info["title"],
        anime_image=info["image"],
        anime_episodes=info["episodes"],
        status=data.get("status", "Plan to Watch"),
        episodes_watched=data.get("episodes_watched", 0),
        score=data.get("score"),
        notes=(data.get("notes") or "").strip()
    )

    db.session.add(entry)
    db.session.commit()
    return jsonify({"message": "Added to watchlist", "entry": entry.to_dict()}), 201


@app.route("/api/watchlist/<int:entry_id>", methods=["PUT"])
@login_required
def update_watchlist(entry_id):
    entry = WatchlistEntry.query.filter_by(
        id=entry_id, user_id=current_user.id
    ).first_or_404()

    data = request.get_json(silent=True) or {}

    if "status" in data:
        entry.status = data["status"]
    if "episodes_watched" in data:
        entry.episodes_watched = data["episodes_watched"]
    if "score" in data:
        entry.score = data["score"]
    if "notes" in data:
        entry.notes = data["notes"]

    entry.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"message": "Watchlist updated", "entry": entry.to_dict()})


@app.route("/api/watchlist/<int:entry_id>", methods=["DELETE"])
@login_required
def delete_watchlist(entry_id):
    entry = WatchlistEntry.query.filter_by(
        id=entry_id, user_id=current_user.id
    ).first_or_404()
    db.session.delete(entry)
    db.session.commit()
    return jsonify({"message": "Removed from watchlist"})


# Leaderboard API

@app.route("/api/leaderboard")
def get_leaderboard():
    users = User.query.order_by(User.loyalty_points.desc()).limit(20).all()

    leaderboard = []
    for rank, user in enumerate(users, 1):
        total_entries = JournalEntry.query.filter_by(user_id=user.id).count()
        total_votes = db.session.query(
            db.func.sum(JournalEntry.helpful_votes)
        ).filter_by(user_id=user.id).scalar() or 0

        leaderboard.append({
            "rank": rank,
            "username": user.username,
            "loyalty_points": user.loyalty_points,
            "trust_level": user.trust_level,
            "total_entries": total_entries,
            "total_votes": total_votes,
            "member_since": user.created_at.strftime("%b %Y")
        })

    current_rank = None
    if current_user.is_authenticated:
        all_users = User.query.order_by(User.loyalty_points.desc()).all()
        for i, u in enumerate(all_users, 1):
            if u.id == current_user.id:
                current_rank = i
                break

    return jsonify({
        "leaderboard": leaderboard,
        "current_rank": current_rank
    })


# Mood Tracker API

@app.route("/api/mood")
@login_required
def get_mood():
    entries = JournalEntry.query.filter_by(
        user_id=current_user.id
    ).order_by(JournalEntry.created_at.asc()).all()

    if not entries:
        return jsonify({"message": "No entries found."})

    mood_data = []
    for e in entries:
        mood_data.append({
            "date": e.created_at.strftime("%d %b"),
            "anime_title": e.anime_title,
            "vader_score": e.vader_score,
            "textblob_score": e.textblob_score,
            "transformer_score": e.transformer_score,
            "avg_score": round(
                (e.vader_score + e.textblob_score + e.transformer_score) / 3, 3
            ),
            "label": e.vader_label
        })

    sentiment_counts = {"Positive": 0, "Neutral": 0, "Negative": 0}
    for e in entries:
        sentiment_counts[e.vader_label] = sentiment_counts.get(e.vader_label, 0) + 1

    top_anime = {}
    for e in entries:
        if e.anime_title not in top_anime:
            top_anime[e.anime_title] = []
        top_anime[e.anime_title].append(e.vader_score)

    top_anime_avg = {
        k: round(sum(v) / len(v), 3)
        for k, v in top_anime.items()
    }

    return jsonify({
        "mood_data": mood_data,
        "sentiment_counts": sentiment_counts,
        "top_anime": top_anime_avg
    })


# Sentiment Clash API

@app.route("/api/clash")
@login_required
def sentiment_clash():
    anime1 = request.args.get("anime1", "").strip()
    anime2 = request.args.get("anime2", "").strip()

    if not anime1 or not anime2:
        return jsonify({"error": "Two anime titles are required"}), 400

    def get_stats(title):
        entries = JournalEntry.query.filter(
            JournalEntry.anime_title.ilike(f"%{title}%")
        ).all()

        if not entries:
            return None

        vader_scores = [e.vader_score for e in entries]
        textblob_scores = [e.textblob_score for e in entries]
        transformer_scores = [e.transformer_score for e in entries]
        ratings = [e.rating for e in entries]

        sentiments = {"Positive": 0, "Neutral": 0, "Negative": 0}
        for e in entries:
            sentiments[e.vader_label] = sentiments.get(e.vader_label, 0) + 1

        return {
            "title": title,
            "total_reviews": len(entries),
            "avg_vader": round(sum(vader_scores) / len(vader_scores), 3),
            "avg_textblob": round(sum(textblob_scores) / len(textblob_scores), 3),
            "avg_transformer": round(sum(transformer_scores) / len(transformer_scores), 3),
            "avg_rating": round(sum(ratings) / len(ratings), 1),
            "sentiment_breakdown": sentiments,
            "overall_sentiment": max(sentiments, key=sentiments.get)
        }

    stats1 = get_stats(anime1)
    stats2 = get_stats(anime2)

    if not stats1:
        return jsonify({"error": f"No journal entries found for '{anime1}'"}), 404
    if not stats2:
        return jsonify({"error": f"No journal entries found for '{anime2}'"}), 404

    winner = anime1 if stats1["avg_vader"] >= stats2["avg_vader"] else anime2

    return jsonify({
        "anime1": stats1,
        "anime2": stats2,
        "winner": winner
    })


# Feed API

@app.route("/api/feed")
def get_feed():
    entries = JournalEntry.query.join(User).order_by(
        JournalEntry.helpful_votes.desc(),
        JournalEntry.created_at.desc()
    ).limit(30).all()

    return jsonify([e.to_dict() for e in entries])


# Anime search API

@app.route("/api/anime/search")
def anime_search():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify([])

    try:
        res = requests.get(
            "https://api.jikan.moe/v4/anime",
            params={"q": query, "limit": 5},
            timeout=5
        )
        data = res.json()
        results = []
        for anime in data.get("data", []):
            results.append({
                "title": anime["title"],
                "image": anime["images"]["jpg"]["image_url"],
                "episodes": anime.get("episodes"),
                "score": anime.get("score"),
                "synopsis": (anime.get("synopsis") or "")[:150]
            })
        return jsonify(results)
    except Exception:
        return jsonify([])


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)