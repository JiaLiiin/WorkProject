# main_app.py
# A comprehensive Event Management System using Flask.
#
# To run this application:
# 1. Make sure you have Python installed.
# 2. Install the required libraries:
#    pip install Flask Flask-SQLAlchemy Flask-Login qrcode[pil]
# 3. Save this file as `main_app.py`.
# 4. Create a folder named `templates` in the same directory as `main_app.py`.
# 5. Save all the provided .html files into the `templates` folder.
# 6. Create a folder named `static` in the same directory.
# 7. Inside `static`, create a folder named `qrcodes`. This is where QR images will be saved.
# 8. Run the script from your terminal: `python main_app.py`
# 9. Open your web browser and navigate to http://127.0.0.1:5000.
#
# Initial Setup:
# - The first time you run the app, a database file `events.db` will be created.
# - An initial admin user will be created with username 'admin' and password 'password'.
# - You can register new users (who will be 'attenders' by default) from the registration page.

import os
import uuid
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import qrcode
from PIL import Image

# --- Application Setup ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'a-very-secret-key-that-should-be-changed'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'events.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# --- Database Models ---

class User(UserMixin, db.Model):
    """User model for authentication and roles."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='attender')  # Roles: 'admin', 'attender'
    invitations = db.relationship('Invitation', backref='attender', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Event(db.Model):
    """Event model."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    schedules = db.relationship('Schedule', backref='event', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Event {self.name}>'

class Location(db.Model):
    """Location model for where events take place."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(200), nullable=False, unique=True)
    schedules = db.relationship('Schedule', backref='location', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Location {self.name}>'

class Schedule(db.Model):
    """Schedule model linking an Event to a Location at a specific time."""
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False)
    invitations = db.relationship('Invitation', backref='schedule', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Schedule for {self.event.name} at {self.start_time}>'

class Invitation(db.Model):
    """Invitation model linking a User to a scheduled Event."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedule.id'), nullable=False)
    attended = db.Column(db.Boolean, default=False, nullable=False)
    qr_code_uid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    qr_code_path = db.Column(db.String(200), nullable=True)
    seatings = db.relationship('Seating', backref='invitation', lazy='dynamic', cascade="all, delete-orphan")

    __table_args__ = (db.UniqueConstraint('user_id', 'schedule_id', name='_user_schedule_uc'),)

    def __repr__(self):
        return f'<Invitation for {self.attender.username} to {self.schedule.event.name}>'

class Seating(db.Model):
    """Seating model."""
    id = db.Column(db.Integer, primary_key=True)
    seat_number = db.Column(db.String(20), nullable=False)
    invitation_id = db.Column(db.Integer, db.ForeignKey('invitation.id'), nullable=False)

    def __repr__(self):
        return f'<Seat {self.seat_number}>'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Decorators ---
def admin_required(f):
    """Decorator to restrict access to admins only."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin':
            flash('This area is restricted to administrators.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# --- Helper Functions ---
def generate_qr_code(invitation):
    """Generates a QR code for an invitation and saves it."""
    qr_data = invitation.qr_code_uid
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Ensure the directory exists
    static_dir = os.path.join(basedir, 'static', 'qrcodes')
    os.makedirs(static_dir, exist_ok=True)
    
    filename = f'{qr_data}.png'
    filepath = os.path.join(static_dir, filename)
    img.save(filepath)
    
    invitation.qr_code_path = f'qrcodes/{filename}'
    db.session.commit()


# --- Routes ---

# --- Authentication Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', title='Login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash('Username already exists. Please choose a different one.', 'warning')
            return redirect(url_for('register'))

        new_user = User(username=username, role='attender')
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


# --- Main Dashboard ---
@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    else:
        return redirect(url_for('attender_dashboard'))


# --- Attender Routes ---
@app.route('/attender/dashboard')
@login_required
def attender_dashboard():
    if current_user.role != 'attender':
        return redirect(url_for('dashboard'))
    
    # Only show invitations for upcoming events.
    now = datetime.now()
    invitations = Invitation.query.join(Schedule).filter(
        Invitation.user_id == current_user.id,
        Schedule.end_time > now
    ).order_by(Schedule.start_time).all()
    
    return render_template('attender_dashboard.html', title='My Events', invitations=invitations)

@app.route('/attender/invitation/<int:invitation_id>')
@login_required
def view_invitation(invitation_id):
    invitation = Invitation.query.get_or_404(invitation_id)
    # Allow viewing of past events via this direct link
    if invitation.attender.id != current_user.id and current_user.role != 'admin':
        flash('You are not authorized to view this invitation.', 'danger')
        return redirect(url_for('dashboard'))
        
    return render_template('view_invitation.html', title='Event Invitation', invitation=invitation)

# --- Admin Routes ---
@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    events = Event.query.all()
    locations = Location.query.all()
    schedules = Schedule.query.order_by(Schedule.start_time.desc()).all()
    users = User.query.all()
    invitations = Invitation.query.all()
    return render_template('admin_dashboard.html', title='Admin Dashboard',
                           events=events, locations=locations, schedules=schedules,
                           users=users, invitations=invitations, now=datetime.now())

# --- Admin: Events CRUD ---
@app.route('/admin/event/add', methods=['POST'])
@login_required
@admin_required
def add_event():
    name = request.form.get('name')
    description = request.form.get('description')
    if name:
        new_event = Event(name=name, description=description)
        db.session.add(new_event)
        db.session.commit()
        flash('Event created successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/event/delete/<int:event_id>', methods=['POST'])
@login_required
@admin_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted successfully.', 'success')
    return redirect(url_for('admin_dashboard'))
    
# --- Admin: Locations CRUD ---
@app.route('/admin/location/add', methods=['POST'])
@login_required
@admin_required
def add_location():
    name = request.form.get('name')
    address = request.form.get('address')
    if name and address:
        existing_location = Location.query.filter_by(address=address).first()
        if existing_location:
            flash('A location with this address already exists.', 'warning')
        else:
            new_location = Location(name=name, address=address)
            db.session.add(new_location)
            db.session.commit()
            flash('Location added successfully!', 'success')
    else:
        flash('Both location name and address are required.', 'danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/location/delete/<int:location_id>', methods=['POST'])
@login_required
@admin_required
def delete_location(location_id):
    location = Location.query.get_or_404(location_id)
    db.session.delete(location)
    db.session.commit()
    flash('Location deleted successfully.', 'success')
    return redirect(url_for('admin_dashboard'))

# --- Admin: Schedules CRUD ---
@app.route('/admin/schedule/add', methods=['POST'])
@login_required
@admin_required
def add_schedule():
    event_id = request.form.get('event_id')
    location_id = request.form.get('location_id')
    start_time_str = request.form.get('start_time')
    end_time_str = request.form.get('end_time')

    if event_id and location_id and start_time_str and end_time_str:
        try:
            start_time = datetime.fromisoformat(start_time_str)
            end_time = datetime.fromisoformat(end_time_str)
            if end_time <= start_time:
                flash('End time must be after start time.', 'danger')
                return redirect(url_for('admin_dashboard'))
            
            new_schedule = Schedule(event_id=event_id, location_id=location_id, start_time=start_time, end_time=end_time)
            db.session.add(new_schedule)
            db.session.commit()
            flash('Schedule created!', 'success')
        except ValueError:
            flash('Invalid date format.', 'danger')
    else:
        flash('All fields are required for scheduling.', 'danger')
        
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/schedule/delete/<int:schedule_id>', methods=['POST'])
@login_required
@admin_required
def delete_schedule(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    db.session.delete(schedule)
    db.session.commit()
    flash('Schedule deleted successfully.', 'success')
    return redirect(url_for('admin_dashboard'))

# --- Admin: Invitations and Seating ---
@app.route('/admin/invite/add', methods=['POST'])
@login_required
@admin_required
def add_invitation():
    user_id = request.form.get('user_id')
    schedule_id = request.form.get('schedule_id')
    
    if not user_id or not schedule_id:
        flash('User and Schedule are required.', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    existing_invitation = Invitation.query.filter_by(user_id=user_id, schedule_id=schedule_id).first()
    if existing_invitation:
        flash('This user is already invited to this event.', 'warning')
        return redirect(url_for('admin_dashboard'))

    new_invitation = Invitation(user_id=user_id, schedule_id=schedule_id)
    db.session.add(new_invitation)
    db.session.commit()
    
    # Generate QR code after invitation is created and has an ID
    generate_qr_code(new_invitation)
    
    flash('Invitation sent successfully!', 'success')
    return redirect(url_for('admin_dashboard'))
    
@app.route('/admin/seating/add/<int:invitation_id>', methods=['POST'])
@login_required
@admin_required
def add_seating(invitation_id):
    seat_number = request.form.get('seat_number')
    if seat_number:
        new_seating = Seating(seat_number=seat_number, invitation_id=invitation_id)
        db.session.add(new_seating)
        db.session.commit()
        flash(f"Seat '{seat_number}' assigned.", 'success')
    else:
        flash('Seat number is required.', 'danger')
    return redirect(url_for('view_invitation', invitation_id=invitation_id))

# --- Admin: QR Code Scanning ---
@app.route('/admin/scan')
@login_required
@admin_required
def scan_qr():
    return render_template('scan_qr.html', title='Scan QR Code')

@app.route('/admin/verify_attendance', methods=['POST'])
@login_required
@admin_required
def verify_attendance():
    qr_uid = request.json.get('qr_data')
    if not qr_uid:
        return jsonify({'success': False, 'message': 'No QR data received.'})
        
    invitation = Invitation.query.filter_by(qr_code_uid=qr_uid).first()
    
    if not invitation:
        return jsonify({'success': False, 'message': 'Invalid QR Code. Invitation not found.'})
    
    seats = [s.seat_number for s in invitation.seatings]
    seat_info = ', '.join(seats) if seats else 'No seat assigned'
    
    # Provide info even if already attended
    if invitation.attended:
        return jsonify({
            'success': False, 
            'message': 'Attendance was ALREADY marked for this user.',
            'attender_info': {
                'username': invitation.attender.username,
                'event': invitation.schedule.event.name,
                'seat': seat_info
            }
        })
    
    # Check if event has ended
    if invitation.schedule.end_time < datetime.now():
        return jsonify({
            'success': False,
            'message': 'This event has already ended. Cannot mark attendance.',
            'attender_info': {
                'username': invitation.attender.username,
                'event': invitation.schedule.event.name,
                'seat': seat_info
            }
        })

    invitation.attended = True
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Success! Attendance marked.',
        'attender_info': {
            'username': invitation.attender.username,
            'event': invitation.schedule.event.name,
            'seat': seat_info
        }
    })

# --- Main Application Runner ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create a default admin user if one doesn't exist
        if not User.query.filter_by(username='admin').first():
            print("Creating default admin user...")
            admin_user = User(username='admin', role='admin')
            admin_user.set_password('password')
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created. Username: admin, Password: password")
    app.run(debug=True)
