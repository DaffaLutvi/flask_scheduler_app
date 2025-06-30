# flask_scheduler_app/routes.py
from flask import render_template, url_for, flash, redirect, request, jsonify, send_file
from extensions import db, bcrypt, login_manager # <--- NEW: Import from extensions.py
from forms import RegistrationForm, LoginForm, ManualBookingForm, UploadScheduleForm, FilterScheduleForm, AvailableRoomFilterForm
from models import User, Schedule, BUILDINGS, EXCLUDED_LAB_ROOMS
from flask_login import login_user, current_user, logout_user, login_required
import pandas as pd
import io
import datetime
import scheduler_logic # This import is fine

# Helper function
def role_required(required_role):
    def decorator(f):
        @login_required
        def decorated_function(*args, **kwargs):
            if current_user.role != required_role and current_user.role != 'admin':
                flash('Anda tidak memiliki izin untuk mengakses halaman ini.', 'danger')
                return redirect(url_for('landing_page'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- All your route functions here. They can now safely use db, bcrypt. ---

def landing_page():
    return render_template('landing_page.html', title='Selamat Datang')

def register():
    if current_user.is_authenticated:
        return redirect(url_for('landing_page'))
    form = RegistrationForm()
    if form.validate_on_submit():
        # bcrypt is now imported from extensions and available directly
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password, role='dosen')
        db.session.add(user) # db is now imported from extensions and available directly
        db.session.commit()
        flash('Akun Anda berhasil dibuat! Anda sekarang dapat login.', 'success')
        return redirect(url_for('login'))
    return render_template('auth/register.html', title='Register', form=form)

def login():
    if current_user.is_authenticated:
        return redirect(url_for('landing_page'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        # bcrypt is now imported from extensions and available directly
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash(f'Selamat datang, {user.username}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('landing_page'))
        else:
            flash('Login gagal. Mohon periksa email dan password Anda.', 'danger')
    return render_template('auth/login.html', title='Login', form=form)

def logout():
    logout_user()
    flash('Anda telah logout.', 'info')
    return redirect(url_for('landing_page'))

@login_required
def view_schedules():
    form = FilterScheduleForm()
    query = Schedule.query # Schedule.query implicitly uses db

    if request.method == 'POST' and form.validate():
        if form.day.data:
            query = query.filter_by(day=form.day.data)
        if form.room.data:
            query = query.filter(Schedule.room.ilike(f'%{form.room.data}%'))
        if form.kelas.data:
            query = query.filter(Schedule.kelas.ilike(f'%{form.kelas.data}%'))
        if form.dosen.data:
            query = query.filter(Schedule.dosen_name.ilike(f'%{form.dosen.data}%'))
    elif request.method == 'GET':
        day = request.args.get('day')
        room = request.args.get('room')
        kelas = request.args.get('kelas')
        dosen = request.args.get('dosen')

        if day:
            query = query.filter_by(day=day)
            form.day.data = day
        if room:
            query = query.filter(Schedule.room.ilike(f'%{room}%'))
            form.room.data = room
        if kelas:
            query = query.filter(Schedule.kelas.ilike(f'%{kelas}%'))
            form.kelas.data = kelas
        if dosen:
            query = query.filter(Schedule.dosen_name.ilike(f'%{dosen}%'))
            form.dosen.data = dosen

    schedules = query.order_by(Schedule.day, Schedule.start_time).all()
    return render_template('schedules/view_schedules.html', title='Lihat Jadwal', schedules=schedules, form=form)

@role_required('admin')
def delete_schedule(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    db.session.delete(schedule) # db is available
    db.session.commit()
    flash('Jadwal berhasil dihapus.', 'success')
    return redirect(url_for('view_schedules'))

@role_required('admin')
def delete_all_schedules():
    num_rows_deleted = db.session.query(Schedule).delete() # db is available
    db.session.commit()
    flash(f'{num_rows_deleted} jadwal berhasil dihapus.', 'success')
    return redirect(url_for('view_schedules'))

@login_required
def download_schedules_excel():
    day = request.args.get('day')
    room = request.args.get('room')
    kelas = request.args.get('kelas')
    dosen = request.args.get('dosen')

    query = Schedule.query
    if day:
        query = query.filter_by(day=day)
    if room:
        query = query.filter(Schedule.room.ilike(f'%{room}%'))
    if kelas:
        query = query.filter(Schedule.kelas.ilike(f'%{kelas}%'))
    if dosen:
        query = query.filter(Schedule.dosen_name.ilike(f'%{dosen}%'))

    schedules = query.order_by(Schedule.day, Schedule.start_time).all()

    data = []
    for sched in schedules:
        data.append({
            'Nama Dosen': sched.dosen_name,
            'Mata Kuliah': sched.mata_kuliah,
            'Kelas': sched.kelas,
            'Hari': sched.day,
            'Jam Mulai': sched.start_time.strftime('%H:%M'),
            'Jam Selesai': sched.end_time.strftime('%H:%M'),
            'Tipe Kelas': sched.class_type,
            'Gedung': sched.building if sched.building else '',
            'Lantai': sched.floor if sched.floor else '',
            'Ruangan': sched.room if sched.room else ''
        })

    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Jadwal')
    output.seek(0)

    return send_file(output, download_name='jadwal_filtered.xlsx', as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@login_required
def manual_booking():
    form = ManualBookingForm()

    if current_user.role == 'dosen':
        form.dosen_name.data = current_user.username
        form.dosen_name.render_kw = {'readonly': True}

    if request.method == 'GET':
        form.day.data = request.args.get('day', form.day.data)
        form.start_time.data = datetime.datetime.strptime(request.args.get('start_time'), '%H:%M').time() if request.args.get('start_time') else form.start_time.data
        form.end_time.data = datetime.datetime.strptime(request.args.get('end_time'), '%H:%M').time() if request.args.get('end_time') else form.end_time.data
        form.class_type.data = request.args.get('class_type', form.class_type.data)
        form.building.data = request.args.get('building', form.building.data)
        form.floor.data = int(request.args.get('floor')) if request.args.get('floor') else form.floor.data
        form.room.data = request.args.get('room', form.room.data)


    if form.class_type.data == 'Offline':
        form.building.choices = [(b, b) for b in BUILDINGS.keys()]
        if form.building.data and form.building.data in BUILDINGS:
            selected_building = BUILDINGS[form.building.data]
            form.floor.choices = [(f, str(f)) for f in selected_building['floors'].keys()]
            if form.floor.data and form.floor.data in selected_building['floors']:
                form.room.choices = [(r, r) for r in selected_building['floors'][form.floor.data]]
        else:
            if BUILDINGS:
                first_building_name = list(BUILDINGS.keys())[0]
                first_building_data = BUILDINGS[first_building_name]
                form.building.choices = [(b, b) for b in BUILDINGS.keys()]
                form.floor.choices = [(f, str(f)) for f in first_building_data['floors'].keys()]
                if first_building_data['floors']:
                    first_floor_num = list(first_building_data['floors'].keys())[0]
                    form.room.choices = [(r, r) for r in first_building_data['floors'][first_floor_num]]
    else:
        form.building.choices = []
        form.floor.choices = []
        form.room.choices = []

    if form.validate_on_submit():
        start_time = form.start_time.data
        end_time = form.end_time.data
        day = form.day.data
        kelas = form.kelas.data
        dosen_name = form.dosen_name.data
        room = form.room.data if form.class_type.data == 'Offline' else None

        conflict_room_exists = False
        if form.class_type.data == 'Offline':
            conflict_room_exists = Schedule.query.filter_by(day=day, room=room).filter(
                (Schedule.start_time < end_time) & (Schedule.end_time > start_time)
            ).first()
        if conflict_room_exists:
            flash('Ruangan ini sudah digunakan pada jam tersebut.', 'danger')
            return render_template('schedules/manual_booking.html', title='Booking Manual', form=form)

        conflict_kelas_exists = Schedule.query.filter_by(day=day, kelas=kelas).filter(
            (Schedule.start_time < end_time) & (Schedule.end_time > start_time)
        ).first()
        if conflict_kelas_exists:
            flash('Kelas ini sudah memiliki jadwal pada jam tersebut.', 'danger')
            return render_template('schedules/manual_booking.html', title='Booking Manual', form=form)

        conflict_dosen_exists = Schedule.query.filter_by(day=day, dosen_name=dosen_name).filter(
            (Schedule.start_time < end_time) & (Schedule.end_time > start_time)
        ).first()
        if conflict_dosen_exists:
            flash('Dosen ini sudah memiliki jadwal pada jam tersebut.', 'danger')
            return render_template('schedules/manual_booking.html', title='Booking Manual', form=form)


        schedule = Schedule(
            dosen_name=form.dosen_name.data,
            mata_kuliah=form.mata_kuliah.data,
            kelas=form.kelas.data,
            day=form.day.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            class_type=form.class_type.data,
            building=form.building.data if form.class_type.data == 'Offline' else None,
            floor=form.floor.data if form.class_type.data == 'Offline' else None,
            room=form.room.data if form.class_type.data == 'Offline' else None
        )
        db.session.add(schedule)
        db.session.commit()
        flash('Jadwal baru berhasil ditambahkan!', 'success')
        return redirect(url_for('view_schedules'))

    return render_template('schedules/manual_booking.html', title='Booking Manual', form=form)


def get_floors(building_name):
    floors = []
    if building_name in BUILDINGS:
        floors = [(f, str(f)) for f in BUILDINGS[building_name]['floors'].keys()]
    return jsonify(floors)


def get_rooms(building_name, floor_num):
    rooms = []
    if building_name in BUILDINGS and floor_num in BUILDINGS[building_name]['floors']:
        rooms = [(r, r) for r in BUILDINGS[building_name]['floors'][floor_num]]
    return jsonify(rooms)


@role_required('admin')
def generate_schedule():
    form = UploadScheduleForm()
    if form.validate_on_submit():
        file = form.file.data
        if file and (file.filename.endswith('.xlsx') or file.filename.endswith('.csv')):
            try:
                df = None
                if file.filename.endswith('.xlsx'):
                    df = pd.read_excel(file)
                else: # .csv
                    df = pd.read_csv(file)

                new_schedules, errors = scheduler_logic.generate_schedules_from_excel(df, db.session)

                if errors:
                    for error_msg in errors:
                        flash(error_msg, 'warning')

                if new_schedules:
                    flash(f'{len(new_schedules)} jadwal berhasil dibuat secara otomatis.', 'success')
                else:
                    flash('Tidak ada jadwal baru yang berhasil dibuat.', 'info')

                return redirect(url_for('view_schedules'))

            except Exception as e:
                flash(f'Terjadi kesalahan saat memproses file: {str(e)}', 'danger')
        else:
            flash('Mohon unggah file Excel (.xlsx) atau CSV (.csv) yang valid.', 'danger')
    return render_template('schedules/generate_schedule.html', title='Generate Jadwal Otomatis', form=form)


@login_required
def download_template():
    data = {'MATA KULIAH': [''], 'SKS': [''], 'KELAS': [''], 'DOSEN PENGAJAR': [''],
            'SEMESTER': [''], 'DOSEN_HARI_KAMPUS': [''], 'DOSEN_JAM_KAMPUS': [''],
            'TIPE_KELAS': [''], 'PRIORITAS_RUANGAN': ['']}
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Template Jadwal')
    output.seek(0)
    return send_file(output, download_name='template_jadwal.xlsx', as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@role_required('dosen')
def available_rooms():
    form = AvailableRoomFilterForm()
    available_slots_data = {}
    selected_day = None

    if form.validate_on_submit():
        selected_day = form.day.data
        available_slots_data = scheduler_logic.get_available_time_slots(selected_day, db.session)

    return render_template('schedules/available_rooms.html', title='Ruangan Tersedia', form=form,
                           available_slots_data=available_slots_data, selected_day=selected_day)