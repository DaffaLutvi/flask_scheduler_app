# flask_scheduler_app/models.py
from extensions import db, login_manager # <--- NEW: Import from extensions.py
from flask_login import UserMixin
from datetime import datetime

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(20), default='dosen', nullable=False) # admin, dosen, mahasiswa

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.role}')"

class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dosen_name = db.Column(db.String(100), nullable=False)
    mata_kuliah = db.Column(db.String(100), nullable=False)
    kelas = db.Column(db.String(50), nullable=False)
    day = db.Column(db.String(20), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    class_type = db.Column(db.String(20), nullable=False) # Online/Offline
    building = db.Column(db.String(50), nullable=True)
    floor = db.Column(db.Integer, nullable=True)
    room = db.Column(db.String(50), nullable=True)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Schedule('{self.mata_kuliah}', '{self.kelas}', '{self.day}', '{self.start_time}-{self.end_time}')"

# Definisi struktur gedung dan ruangan
BUILDINGS = {
    'Gedung A': {
        'floors': {
            3: ['A301', 'A302', 'A303'],
            4: ['A401', 'A402', 'A403', 'Lab. A404', 'Lab. A405'],
            5: ['A501', 'A502', 'A503']
        }
    },
    'Gedung B': {
        'floors': {
            1: ['B101', 'B102'],
            2: ['B201', 'B202', 'B203'],
            3: ['B301', 'B302', 'B303'],
            4: ['B401', 'B402'],
            5: ['B501', 'B502']
        }
    }
}

# Ruangan lab yang dikecualikan dari generate otomatis
EXCLUDED_LAB_ROOMS = ['Lab. A404', 'Lab. A405']