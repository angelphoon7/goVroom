from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    cars = db.relationship('CarModel', backref='owner', lazy=True)
    bookings = db.relationship('BookingModel', backref='user', lazy=True)
    payments = db.relationship('PaymentModel', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class CarModel(db.Model):
    __tablename__ = 'cars'
    
    id = db.Column(db.Integer, primary_key=True)
    make = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    price_per_day = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    image_filename = db.Column(db.String(255), nullable=True)  # New field for storing image filename
    location = db.Column(db.String(255), nullable=True)  # New field for storing location
    address = db.Column(db.String(255), nullable=True)  # New field for storing address
    license_number = db.Column(db.String(50), nullable=False)  # New field for storing license number
    license_expiry = db.Column(db.Date, nullable=False)  # New field for storing license expiry date
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    
    # Relationships
    bookings = db.relationship('BookingModel', backref='car', lazy=True)
    service_records = db.relationship('ServiceRecordModel', backref='car', lazy=True)

class BookingModel(db.Model):
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    car_id = db.Column(db.Integer, db.ForeignKey('cars.id'), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with Payment
    payment = db.relationship('PaymentModel', backref='booking', lazy=True, uselist=False)

class PaymentModel(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_method = db.Column(db.String(50))
    transaction_id = db.Column(db.String(100))

class ServiceRecordModel(db.Model):
    __tablename__ = 'service_records'
    
    id = db.Column(db.Integer, primary_key=True)
    car_id = db.Column(db.Integer, db.ForeignKey('cars.id'), nullable=False)
    service_date = db.Column(db.Date, nullable=False)
    service_type = db.Column(db.String(100), nullable=False)  # e.g., "Regular Maintenance", "Oil Change", "Brake Service"
    mileage = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    cost = db.Column(db.Float, nullable=False)
    service_provider = db.Column(db.String(100), nullable=False)
    next_service_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    pdf_filename = db.Column(db.String(255), nullable=True)  # Path to uploaded PDF
    
    # Optional fields for additional documentation
    invoice_number = db.Column(db.String(50), nullable=True)
    warranty_info = db.Column(db.Text, nullable=True)
    parts_replaced = db.Column(db.Text, nullable=True)

def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all() 