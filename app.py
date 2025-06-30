# flask_scheduler_app/app.py
from flask import Flask
from config import Config
from extensions import db, bcrypt, login_manager # <--- NEW: Import from extensions.py

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions WITH the app instance.
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login' # Moved from global scope to within create_app
    login_manager.login_message_category = 'info' # Moved from global scope to within create_app


    # Import models *after* db.init_app(app)
    from models import User, Schedule

    # Flask-Login user loader needs to be defined after User model is imported
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Import routes after everything else is mostly set up
    from routes import (
        landing_page, register, login, logout,
        view_schedules, delete_schedule, delete_all_schedules,
        download_schedules_excel, manual_booking, get_floors, get_rooms,
        generate_schedule, download_template, available_rooms
    )

    # Register routes with the app.
    app.add_url_rule('/', 'landing_page', landing_page)
    app.add_url_rule('/landing_page', 'landing_page_alias', landing_page)
    app.add_url_rule('/register', 'register', register, methods=['GET', 'POST'])
    app.add_url_rule('/login', 'login', login, methods=['GET', 'POST'])
    app.add_url_rule('/logout', 'logout', logout)
    app.add_url_rule('/schedules', 'view_schedules', view_schedules, methods=['GET', 'POST'])
    app.add_url_rule('/schedules/delete/<int:schedule_id>', 'delete_schedule', delete_schedule, methods=['POST'])
    app.add_url_rule('/schedules/delete_all', 'delete_all_schedules', delete_all_schedules, methods=['POST'])
    app.add_url_rule('/schedules/download_excel', 'download_schedules_excel', download_schedules_excel, methods=['GET'])
    app.add_url_rule('/manual_booking', 'manual_booking', manual_booking, methods=['GET', 'POST'])
    app.add_url_rule('/get_floors/<building_name>', 'get_floors', get_floors)
    app.add_url_rule('/get_rooms/<building_name>/<int:floor_num>', 'get_rooms', get_rooms)
    app.add_url_rule('/generate_schedule', 'generate_schedule', generate_schedule, methods=['GET', 'POST'])
    app.add_url_rule('/download_template', 'download_template', download_template)
    app.add_url_rule('/available_rooms', 'available_rooms', available_rooms, methods=['GET', 'POST'])

    return app

# Create the app instance when app.py is executed
app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # User model is available through the app context via db.Model
        from models import User # Import User specifically here for direct use
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            hashed_password = bcrypt.generate_password_hash('adminpassword').decode('utf-8')
            admin_user = User(username='admin', email='admin@example.com', password=hashed_password, role='admin')
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user 'admin' created with password 'adminpassword'. Please change this in production!")
    app.run(debug=True)