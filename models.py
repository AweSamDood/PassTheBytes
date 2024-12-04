from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    discord_id = db.Column(db.String(50), unique=True, nullable=False)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    quota = db.Column(db.Integer, default=0)
    used_space = db.Column(db.Integer, default=0)
    is_admin = db.Column(db.Boolean, default=False)
    files = db.relationship('File', backref='user', lazy=True)


class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    filesize = db.Column(db.Integer, nullable=False)
    upload_time = db.Column(db.DateTime, default=datetime.utcnow())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_public = db.Column(db.Boolean, default=False)
    share_url = db.Column(db.String(100), unique=True, nullable=True)
    password = db.Column(db.String(255), nullable=True)
    expiration_time = db.Column(db.DateTime, nullable=True)

    @property
    def is_expired(self):
        if self.expiration_time:
            return datetime.utcnow() > self.expiration_time
        return False
