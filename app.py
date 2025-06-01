from flask import Flask, render_template, request, redirect, url_for, flash, abort, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import re
import time

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Replace with a real secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///goVroom.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize login manager
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Import models and initialize database
from models import db, User, CarModel, BookingModel, PaymentModel

# Initialize the database with the app
db.init_app(app)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# Admin decorator
def admin_required(f):
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/')
def index():
    cars = CarModel.query.filter_by(status='approved', is_available=True).all()
    return render_template('index.html', cars=cars)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        phone_number = request.form.get('phone_number')
        
        # Validate email format
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('Invalid email format')
            return redirect(url_for('register'))
        
        # Validate phone number format (Malaysian format)
        if not re.match(r"^(\+?6?01)[0-46-9]-*[0-9]{7,8}$", phone_number):
            flash('Invalid phone number format. Please use Malaysian format (e.g., 601X-XXXXXXX)')
            return redirect(url_for('register'))
        
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists')
            return redirect(url_for('register'))
        
        # Create username from email (part before @)
        username = email.split('@')[0]
        # Check if username exists, if so, append a number
        base_username = username
        counter = 1
        while User.query.filter_by(username=username).first():
            username = f"{base_username}{counter}"
            counter += 1
        
        new_user = User(
            username=username,
            email=email, 
            name=name, 
            phone_number=phone_number
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid email or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/add-car', methods=['GET', 'POST'])
@login_required
def add_car():
    if request.method == 'POST':
        make = request.form.get('make')
        model = request.form.get('model')
        year = request.form.get('year')
        price_per_day = request.form.get('price_per_day')
        description = request.form.get('description')
        address = request.form.get('address')
        license_number = request.form.get('license_number')
        license_expiry = request.form.get('license_expiry')
        image = request.files.get('image')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        location = f"{latitude},{longitude}" if latitude and longitude else None
        if not all([make, model, year, price_per_day, description]):
            flash('All fields are required')
            return redirect(url_for('add_car'))
        if image and image.filename:
            image_filename = secure_filename(image.filename)
            image_path = os.path.join('static', 'images', 'cars', image_filename)
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            image.save(image_path)
            image_url = '/' + image_path
        else:
            image_url = 'https://via.placeholder.com/400x300?text=No+Image+Available'
        new_car = CarModel(
            make=make,
            model=model,
            year=int(year),
            price_per_day=float(price_per_day),
            description=description,
            owner_id=current_user.id,
            image_filename=image_url,
            location=location,
            address=address,
            license_number=license_number,
            license_expiry=datetime.strptime(license_expiry, '%Y-%m-%d').date(),
            status='pending'
        )
        db.session.add(new_car)
        db.session.commit()
        flash('Car added successfully and is pending admin approval!', 'info')
        return redirect(url_for('car_pending'))
    return render_template('add_car.html')

@app.route('/car_pending')
@login_required
def car_pending():
    return render_template('car_pending.html')

@app.route('/book-car/<int:car_id>', methods=['GET', 'POST'])
@login_required
def book_car(car_id):
    car = CarModel.query.get_or_404(car_id)
    if request.method == 'POST':
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
        end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d')
        
        # Calculate number of days and total price
        days = (end_date - start_date).days + 1
        total_price = days * car.price_per_day
        
        booking = BookingModel(
            car_id=car_id,
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date,
            total_price=total_price
        )
        db.session.add(booking)
        db.session.commit()
        
        # Redirect to payment page
        return redirect(url_for('payment', booking_id=booking.id))
    return render_template('book_car.html', car=car)

# Admin routes
@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    users = User.query.all()
    pending_cars = CarModel.query.filter_by(status='pending').all()
    all_cars = CarModel.query.all()
    print('DEBUG: Pending cars:', [(car.id, car.make, car.model, car.status) for car in pending_cars])
    bookings = BookingModel.query.options(
        db.joinedload(BookingModel.user),
        db.joinedload(BookingModel.car)
    ).all()
    return render_template('admin/dashboard.html', 
                         users=users, 
                         pending_cars=pending_cars,
                         all_cars=all_cars,
                         bookings=bookings)

@app.route('/admin/toggle-admin/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def admin_toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user.id != current_user.id:  # Prevent self-demotion
        user.is_admin = not user.is_admin
        db.session.commit()
        flash(f"Admin status for {user.name} has been {'granted' if user.is_admin else 'revoked'}")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id != current_user.id:  # Prevent self-deletion
        db.session.delete(user)
        db.session.commit()
        flash(f"User {user.name} has been deleted")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete-car/<int:car_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_car(car_id):
    car = CarModel.query.get_or_404(car_id)
    db.session.delete(car)
    db.session.commit()
    flash(f"Car {car.make} {car.model} has been deleted")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/update-booking-status/<int:booking_id>', methods=['POST'])
@login_required
@admin_required
def admin_update_booking_status(booking_id):
    booking = BookingModel.query.get_or_404(booking_id)
    new_status = request.form.get('status')
    if new_status in ['pending', 'confirmed', 'completed', 'cancelled']:
        booking.status = new_status
        if new_status == 'completed' or new_status == 'cancelled':
            booking.car.is_available = True
        db.session.commit()
        flash(f"Booking status updated to {new_status}")
    return redirect(url_for('admin_dashboard'))

@app.route('/payment/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def payment(booking_id):
    booking = BookingModel.query.get_or_404(booking_id)
    
    # Ensure user owns this booking
    if booking.user_id != current_user.id:
        abort(403)
    
    if request.method == 'POST':
        payment_method = request.form.get('payment_method')
        
        # Create payment record
        payment = PaymentModel(
            booking_id=booking.id,
            user_id=current_user.id,
            amount=booking.total_price,
            payment_method=payment_method,
            transaction_id=f"TRX-{datetime.now().strftime('%Y%m%d%H%M%S')}-{booking.id}"
        )
        
        # Update booking status
        booking.status = 'confirmed'
        booking.car.is_available = False
        
        db.session.add(payment)
        db.session.commit()
        
        flash('Payment successful! Your booking has been confirmed.')
        return redirect(url_for('booking_history'))
        
    return render_template('payment.html', booking=booking)

@app.route('/booking-history')
@login_required
def booking_history():
    # Get user's bookings ordered by creation date
    bookings = BookingModel.query.filter_by(user_id=current_user.id)\
        .order_by(BookingModel.created_at.desc()).all()
    return render_template('booking_history.html', bookings=bookings)

@app.route('/admin/update-car-image/<int:car_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_update_car_image(car_id):
    car = CarModel.query.get_or_404(car_id)
    
    if request.method == 'POST':
        image_url = request.form.get('image_url')
        if image_url:
            car.image_filename = image_url
            db.session.commit()
            flash(f"Image updated for {car.make} {car.model}")
            return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/update_car_image.html', car=car)

@app.route('/debug/db')
def debug_db():
    # Comment out authentication for development
    # @login_required
    # @admin_required
    users = User.query.all()
    cars = CarModel.query.all()
    bookings = BookingModel.query.all()
    payments = PaymentModel.query.all()
    
    return render_template('debug_db.html', 
                         users=users, 
                         cars=cars, 
                         bookings=bookings, 
                         payments=payments)

@app.route('/api/car-locations')
def car_locations():
    # Get all cars with location data
    cars = CarModel.query.filter(CarModel.location.isnot(None)).all()
    
    # Prepare the location data
    locations = []
    for car in cars:
        # If location is stored as "lat,lng" string, parse it
        if car.location and ',' in car.location:
            try:
                lat, lng = car.location.split(',')
                locations.append({
                    'id': car.id,
                    'lat': float(lat),
                    'lng': float(lng),
                    'make': car.make,
                    'model': car.model
                })
            except (ValueError, TypeError):
                # Skip if location format is invalid
                continue
    
    return jsonify(locations)

@app.before_request
def before_request():
    if current_user.is_authenticated:
        session.permanent = True  # Make session permanent for logged in users

@app.route('/admin/approve_car/<int:car_id>', methods=['POST'])
@login_required
@admin_required
def approve_car(car_id):
    car = CarModel.query.get_or_404(car_id)
    car.status = 'approved'
    db.session.commit()
    flash('Car approved successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject_car/<int:car_id>', methods=['POST'])
@login_required
@admin_required
def reject_car(car_id):
    car = CarModel.query.get_or_404(car_id)
    car.status = 'rejected'
    db.session.commit()
    flash('Car rejected.', 'info')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/toggle-car-availability/<int:car_id>', methods=['POST'])
@login_required
@admin_required
def toggle_car_availability(car_id):
    car = CarModel.query.get_or_404(car_id)
    car.is_available = not car.is_available
    db.session.commit()
    flash(f"Car '{car.make} {car.model}' availability updated.", 'success')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Create an admin user if none exists
        admin = User.query.filter_by(email='admin@govroom.com').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@govroom.com',
                name='Administrator',
                phone_number='60123456789',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()

        # Add sample cars if none exist
        if not CarModel.query.first():
            sample_cars = [
                {
                    'make': 'Perodua',
                    'model': 'Bezza',
                    'year': 2024,
                    'price_per_day': 120.00,
                    'description': 'Popular Malaysian sedan with excellent fuel efficiency. Perfect for city driving and small families.',
                    'owner_id': admin.id,
                    'is_available': True,
                    'image_filename': 'https://paultan.org/image/2023/07/2024-Perodua-Bezza-render-3-1200x675.jpg',
                    'address': 'Petaling Jaya, Selangor, Malaysia',
                    'location': '3.1073,101.6068'
                },
                {
                    'make': 'Perodua',
                    'model': 'Axia',
                    'year': 2024,
                    'price_per_day': 100.00,
                    'description': 'Compact and economical car ideal for city commuting. Great fuel efficiency and easy to park.',
                    'owner_id': admin.id,
                    'is_available': True,
                    'image_filename': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRRF9B2PpySOf9ycZuo3VFaq603wrUYVEqMmg&s',
                    'address': 'Subang Jaya, Selangor, Malaysia',
                    'location': '3.0657,101.5823'
                },
                {
                    'make': 'Perodua',
                    'model': 'Myvi',
                    'year': 2024,
                    'price_per_day': 130.00,
                    'description': "Malaysia's favorite hatchback. Spacious interior with modern features and reliable performance.",
                    'owner_id': admin.id,
                    'is_available': True,
                    'image_filename': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTb8ZLs7NiZdaPfIuavRLjNFpufriu2Df5Udw&s',
                    'address': 'Shah Alam, Selangor, Malaysia',
                    'location': '3.0734,101.5215'
                },
                {
                    'make': 'Proton',
                    'model': 'Saga',
                    'year': 2024,
                    'price_per_day': 110.00,
                    'description': 'Classic Malaysian sedan with modern updates. Comfortable ride with good value for money.',
                    'owner_id': admin.id,
                    'is_available': True,
                    'image_filename': 'https://www.proton.com/assets/ps2022/saga/img/New-Front-Bumper-and-Grille.jpg',
                    'address': 'Kuala Lumpur, Malaysia',
                    'location': '3.1390,101.6869'
                },
                {
                    'make': 'Toyota',
                    'model': 'Vios',
                    'year': 2024,
                    'price_per_day': 180.00,
                    'description': 'Reliable sedan with premium features. Smooth driving experience and excellent build quality.',
                    'owner_id': admin.id,
                    'is_available': True,
                    'image_filename': 'https://paultan.org/image/2015/01/2015-toyota-vios-updates-2.jpg',
                    'address': 'Puchong, Selangor, Malaysia',
                    'location': '3.0477,101.6170'
                },
                {
                    'make': 'Honda',
                    'model': 'City',
                    'year': 2024,
                    'price_per_day': 190.00,
                    'description': 'Modern sedan with sporty design. Advanced features and comfortable interior.',
                    'owner_id': admin.id,
                    'is_available': True,
                    'image_filename': 'https://evault.honda.com.my/pixelvault/2023-08/9c7c10d2dcf1e4a7fc35454327f208c719a27d3225175.jpg',
                    'address': 'Damansara, Kuala Lumpur, Malaysia',
                    'location': '3.1565,101.6303'
                },
                {
                    'make': 'Proton',
                    'model': 'X50',
                    'year': 2024,
                    'price_per_day': 220.00,
                    'description': 'Premium SUV with modern technology. Stylish design with powerful performance.',
                    'owner_id': admin.id,
                    'is_available': True,
                    'image_filename': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTPRH_PeYEOSn-xe59_2g6rfT0ppX9h9znImg&s',
                    'address': 'Cheras, Kuala Lumpur, Malaysia',
                    'location': '3.1095,101.7524'
                },
                {
                    'make': 'Toyota',
                    'model': 'Hilux',
                    'year': 2024,
                    'price_per_day': 250.00,
                    'description': 'Robust pickup truck perfect for both work and leisure. Powerful and reliable.',
                    'owner_id': admin.id,
                    'is_available': True,
                    'image_filename': 'https://www.toyota.com.my/content/dam/malaysia/models/veloz/overview/toyota-my-veloz-overview.jpg',
                    'address': 'Kajang, Selangor, Malaysia',
                    'location': '2.9848,101.7861'
                }
            ]

            for car_data in sample_cars:
                car = CarModel(**car_data)
                db.session.add(car)
            
            db.session.commit()

    app.run(debug=True) 