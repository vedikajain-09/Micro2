from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'warden' or 'student'
    name = db.Column(db.String(100), nullable=False)
    roll_no = db.Column(db.String(20), unique=True, nullable=True)
    room_no = db.Column(db.String(10), nullable=True)
    block = db.Column(db.String(10), nullable=True)
    phone = db.Column(db.String(15), nullable=True)
    guardian_contact = db.Column(db.String(15), nullable=True)
    blood_group = db.Column(db.String(5), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default='General')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AnnouncementRead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    announcement_id = db.Column(db.Integer, db.ForeignKey('announcement.id'), nullable=False)
    read_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'announcement_id', name='_user_announcement_uc'),)

class MessMenu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.String(10), nullable=False)
    meal = db.Column(db.String(20), nullable=False)
    items = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(10), default='Veg')

class Fee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    fee_type = db.Column(db.String(20), default='Hostel')
    student = db.relationship('User', backref='fees')

class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text, nullable=False)
    room_no = db.Column(db.String(10))
    status = db.Column(db.String(20), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    student = db.relationship('User', backref='complaints')

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='Present')
    student = db.relationship('User', backref='attendances')
    __table_args__ = (db.UniqueConstraint('student_id', 'date', name='_student_date_uc'),)
