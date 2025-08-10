from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Poster(db.Model):
    poster_id = db.Column(db.Integer, primary_key=True)
    owner = db.Column(db.String(200), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    poster_img = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Title: {self.title}>"