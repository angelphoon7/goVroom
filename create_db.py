from app import app, db
from models import User, CarModel, BookingModel, PaymentModel

# Create database and tables
with app.app_context():
    # Drop all existing tables and recreate them
    db.drop_all()
    db.create_all()
    print("Database tables created successfully!") 