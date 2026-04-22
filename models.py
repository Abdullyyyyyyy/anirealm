from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy()


def calculate_trust_level(points):
    if points >= 200:
        return "Elite Recommender"
    elif points >= 100:
        return "Trusted Fan"
    elif points >= 50:
        return "Regular Reviewer"
    return "New User"


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    loyalty_points = db.Column(db.Integer, default=0)
    trust_level = db.Column(db.String(50), default="New User")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    entries = db.relationship("JournalEntry", backref="author", lazy=True)
    watchlist = db.relationship("WatchlistEntry", backref="owner", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def add_points(self, points):
        self.loyalty_points += points
        self.trust_level = calculate_trust_level(self.loyalty_points)


class JournalEntry(db.Model):
    __tablename__ = "journal_entries"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    anime_title = db.Column(db.String(200), nullable=False)
    episode = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    reflection_text = db.Column(db.Text, nullable=False)
    true_label = db.Column(db.String(20), nullable=True)
    vader_label = db.Column(db.String(20), nullable=False)
    vader_score = db.Column(db.Float, nullable=False)
    textblob_label = db.Column(db.String(20), nullable=False)
    textblob_score = db.Column(db.Float, nullable=False)
    transformer_label = db.Column(db.String(20), nullable=False)
    transformer_score = db.Column(db.Float, nullable=False)
    helpful_votes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    votes = db.relationship("Vote", backref="entry", lazy=True,
                            cascade="all, delete-orphan")

    def to_dict(self, current_user_id=None):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.author.username if self.author else "Unknown",
            "trust_level": self.author.trust_level if self.author else "New User",
            "anime_title": self.anime_title,
            "episode": self.episode,
            "rating": self.rating,
            "reflection_text": self.reflection_text,
            "true_label": self.true_label,
            "vader_label": self.vader_label,
            "vader_score": self.vader_score,
            "textblob_label": self.textblob_label,
            "textblob_score": self.textblob_score,
            "transformer_label": self.transformer_label,
            "transformer_score": self.transformer_score,
            "helpful_votes": self.helpful_votes,
            "created_at": self.created_at.isoformat(),
        }


class WatchlistEntry(db.Model):
    __tablename__ = "watchlist"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    anime_title = db.Column(db.String(200), nullable=False)
    anime_image = db.Column(db.String(500), nullable=True)
    anime_episodes = db.Column(db.Integer, nullable=True)
    episodes_watched = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), nullable=False, default="Plan to Watch")
    score = db.Column(db.Integer, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "anime_title": self.anime_title,
            "anime_image": self.anime_image,
            "anime_episodes": self.anime_episodes,
            "episodes_watched": self.episodes_watched,
            "status": self.status,
            "score": self.score,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
        }


class Vote(db.Model):
    __tablename__ = "votes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    entry_id = db.Column(db.Integer, db.ForeignKey("journal_entries.id"),
                         nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("user_id", "entry_id", name="unique_vote"),
    )