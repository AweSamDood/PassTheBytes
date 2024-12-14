from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    discord_id = db.Column(db.BigInteger, unique=True, nullable=False)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    quota = db.Column(db.BigInteger, default=0)
    used_space = db.Column(db.BigInteger, default=0)
    is_admin = db.Column(db.Boolean, default=False)
    files = db.relationship('File', backref='user', lazy=True)


class Directory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    parent_dir_id = db.Column(db.Integer, db.ForeignKey('directory.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    path = db.Column(db.String(1024), nullable=False, index=True)

    child_dirs = db.relationship(
        'Directory',
        backref=db.backref('parent_dir', remote_side=[id]),
        lazy=True
    )
    files = db.relationship('File', backref='directory', lazy=True)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'parent_dir_id', 'name', name='uq_directory_name_in_parent'),
    )

    def __repr__(self):
        return f"<Directory {self.path}>"


class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    filesize = db.Column(db.BigInteger, nullable=False)
    upload_time = db.Column(db.DateTime, default=datetime.utcnow())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    directory_id = db.Column(db.Integer, db.ForeignKey('directory.id'), nullable=True)
    is_public = db.Column(db.Boolean, default=False)
    share_url = db.Column(db.String(100), unique=True, nullable=True)
    password = db.Column(db.String(255), nullable=True)
    expiration_time = db.Column(db.DateTime, nullable=True)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'directory_id', 'filename', name='uq_file_in_directory'),
    )

    @property
    def is_expired(self):
        if self.expiration_time:
            return datetime.utcnow() > self.expiration_time
        return False

    def __repr__(self):
        return f"<File {self.filename}>"
