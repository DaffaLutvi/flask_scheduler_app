# forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TimeField, BooleanField, FileField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from models import User, Schedule # This import is now safe
import datetime

# ... (rest of your forms.py code remains the same) ...
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username itu sudah dipakai. Mohon pilih yang lain.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email itu sudah dipakai. Mohon pilih yang lain.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Ingat Saya')
    submit = SubmitField('Login')

class ManualBookingForm(FlaskForm):
    dosen_name = StringField('Nama Dosen', validators=[DataRequired()])
    mata_kuliah = StringField('Mata Kuliah', validators=[DataRequired()])
    kelas = StringField('Kelas', validators=[DataRequired()])
    day = SelectField('Hari', choices=[
        ('Senin', 'Senin'), ('Selasa', 'Selasa'), ('Rabu', 'Rabu'), ('Kamis', 'Kamis'),
        ('Jumat', 'Jumat'), ('Sabtu', 'Sabtu'), ('Minggu', 'Minggu')
    ], validators=[DataRequired()])
    start_time = TimeField('Jam Mulai', validators=[DataRequired()], format='%H:%M')
    end_time = TimeField('Jam Selesai', validators=[DataRequired()], format='%H:%M')
    class_type = SelectField('Tipe Kelas', choices=[('Online', 'Online'), ('Offline', 'Offline')], validators=[DataRequired()])
    building = SelectField('Gedung', choices=[], coerce=str) # Akan diisi dinamis
    floor = SelectField('Lantai', choices=[], coerce=int) # Akan diisi dinamis
    room = SelectField('Ruangan', choices=[], coerce=str) # Akan diisi dinamis
    submit = SubmitField('Tambah Jadwal')

    def validate_start_time(self, field):
        if self.start_time.data >= self.end_time.data:
            raise ValidationError('Jam Mulai harus lebih awal dari Jam Selesai.')

    def validate_timeslot(self):
        start = self.start_time.data
        end = self.end_time.data

        # Cek bentrokan dengan jam istirahat (12:00-13:00)
        break_start = datetime.time(12, 0)
        break_end = datetime.time(13, 0)

        if (start < break_end and end > break_start):
            raise ValidationError('Jadwal bentrok dengan jam istirahat (12:00-13:00).')

        # Cek bentrokan dengan jadwal yang sudah ada
        # (Implementasi detail di routes.py karena butuh akses database)

class UploadScheduleForm(FlaskForm):
    file = FileField('Pilih File Excel/CSV', validators=[DataRequired()])
    submit = SubmitField('Unggah dan Generate Jadwal')

class FilterScheduleForm(FlaskForm):
    day = SelectField('Hari', choices=[('', 'Semua Hari'), ('Senin', 'Senin'), ('Selasa', 'Selasa'), ('Rabu', 'Rabu'), ('Kamis', 'Kamis'), ('Jumat', 'Jumat'), ('Sabtu', 'Sabtu'), ('Minggu', 'Minggu')])
    room = StringField('Ruangan')
    kelas = StringField('Kelas')
    dosen = StringField('Dosen')
    submit = SubmitField('Filter')

class AvailableRoomFilterForm(FlaskForm):
    day = SelectField('Pilih Hari', choices=[
        ('Senin', 'Senin'), ('Selasa', 'Selasa'), ('Rabu', 'Rabu'), ('Kamis', 'Kamis'),
        ('Jumat', 'Jumat'), ('Sabtu', 'Sabtu'), ('Minggu', 'Minggu')
    ], validators=[DataRequired()])
    submit = SubmitField('Lihat Ketersediaan')