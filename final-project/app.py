import os
from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

# --- App Setup ---
app = Flask(__name__)
# YOU MUST set a secret key for sessions to work
app.config['SECRET_KEY'] = 'a_very_secret_key_change_this'

# --- Database Setup ---
client = MongoClient('mongodb://localhost:27017/')
db = client.plant_watering_db
plants_collection = db.plants
users_collection = db.users
care_events_collection = db.care_events

# --- Image Definitions ---
SPECIES_IMAGES = {
    'Monstera': 'images/monstera.png',
    'Pothos': 'images/pothos.png',
    'Succulent': 'images/suculenta.png',
    'Snake Plant': 'images/sansevieria.png',
}
DEFAULT_IMAGE = 'images/default.png'

# --- Flask-Login Setup ---
login_manager = LoginManager()
login_manager.init_app(app)
# Redirect user to login page if they try to access a protected page
login_manager.login_view = 'login'

class User(UserMixin):
    """
    User class for Flask-Login to wrap the MongoDB user document.
    """
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']
        self.email = user_data['email']
        self.password_hash = user_data['password_hash']

    @staticmethod
    def get(user_id):
        user_data = users_collection.find_one({'_id': ObjectId(user_id)})
        if user_data:
            return User(user_data)
        return None

@login_manager.user_loader
def load_user(user_id):
    """Required callback for Flask-Login to load a user from session."""
    return User.get(user_id)

# --- Auth Routes (Register, Login, Logout) ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Check if user already exists
        existing_user = users_collection.find_one({'email': email})
        if existing_user:
            flash('Email already registered. Please log in.', 'error')
            return redirect(url_for('login'))

        # Hash password and create new user
        password_hash = generate_password_hash(password)
        new_user_id = users_collection.insert_one({
            'username': username,
            'email': email,
            'password_hash': password_hash
        }).inserted_id

        # Log the new user in
        user_data = users_collection.find_one({'_id': new_user_id})
        new_user = User(user_data)
        login_user(new_user)
        
        return redirect(url_for('index'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user_data = users_collection.find_one({'email': email})

        if user_data and check_password_hash(user_data['password_hash'], password):
            user = User(user_data)
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# --- Main App Routes (Protected) ---

@app.route('/')
def index():
    plants = []
    if current_user.is_authenticated:
        # Only find plants that belong to the current user
        user_plants = plants_collection.find({'user_id': ObjectId(current_user.id)})
        plants = sorted(user_plants, key=lambda p: p.get('created_at', datetime.min), reverse=True)
        
    return render_template('index.html', plants=plants)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_plant():
    available_species = list(SPECIES_IMAGES.keys())
    
    if request.method == 'POST':
        plant_name = request.form['plant_name']
        plant_species = request.form['plant_species']
        last_watered_str = request.form['last_watered']
        last_watered_date = datetime.strptime(last_watered_str, '%Y-%m-%d')
        
        plant_image_url = SPECIES_IMAGES.get(plant_species, DEFAULT_IMAGE)

        plant_document = {
            'name': plant_name,
            'species': plant_species,
            'last_watered': last_watered_date,
            'image_url': plant_image_url,
            'created_at': datetime.now(),
            'user_id': ObjectId(current_user.id) # Link plant to user
        }
        new_plant_id = plants_collection.insert_one(plant_document).inserted_id

        # Create the first care event
        care_events_collection.insert_one({
            'plant_id': new_plant_id,
            'user_id': ObjectId(current_user.id),
            'event_type': 'water',
            'event_date': last_watered_date,
            'notes': 'Initial watering specified on creation.'
        })

        return redirect(url_for('index'))

    return render_template('add_plant.html', species_list=available_species)

@app.route('/edit/<string:plant_id>', methods=['GET', 'POST'])
@login_required
def edit_plant(plant_id):
    plant_id_obj = ObjectId(plant_id)
    # Find plant matching ID AND user
    plant_to_edit = plants_collection.find_one({
        '_id': plant_id_obj,
        'user_id': ObjectId(current_user.id)
    })

    if not plant_to_edit:
        flash('Plant not found or you do not have permission.', 'error')
        return redirect(url_for('index'))

    available_species = list(SPECIES_IMAGES.keys())

    if request.method == 'POST':
        updated_name = request.form['plant_name']
        updated_species = request.form['plant_species']
        updated_last_watered_str = request.form['last_watered']
        updated_last_watered = datetime.strptime(updated_last_watered_str, '%Y-%m-%d')
        updated_image_url = SPECIES_IMAGES.get(updated_species, DEFAULT_IMAGE)
        
        update_data = {
            '$set': {
                'name': updated_name,
                'species': updated_species,
                'last_watered': updated_last_watered,
                'image_url': updated_image_url
            }
        }
        plants_collection.update_one({'_id': plant_id_obj}, update_data)
        
        # Optional: You could create a 'care_event' for "edit" here
        
        return redirect(url_for('index'))
    else:
        return render_template('edit_plant.html', plant=plant_to_edit, species_list=available_species)

@app.route('/plant/<string:plant_id>')
@login_required
def plant_detail(plant_id):
    plant_id_obj = ObjectId(plant_id)
    
    # 1. Find the plant
    plant = plants_collection.find_one({
        '_id': plant_id_obj,
        'user_id': ObjectId(current_user.id)
    })

    if not plant:
        flash('Plant not found or you do not have permission.', 'error')
        return redirect(url_for('index'))

    # 2. Find all care events for this plant
    events_cursor = care_events_collection.find({
        'plant_id': plant_id_obj,
        'user_id': ObjectId(current_user.id)
    })
    
    # 3. Sort events, newest first
    events = sorted(events_cursor, key=lambda e: e.get('event_date', datetime.min), reverse=True)

    # 4. Render the new template
    return render_template('plant_detail.html', plant=plant, events=events)

@app.route('/water/<string:plant_id>', methods=['POST'])
@login_required
def water_plant(plant_id):
    plant_id_obj = ObjectId(plant_id)
    now = datetime.now()

    # Find plant matching ID AND user
    plant_to_update = plants_collection.find_one({
        '_id': plant_id_obj,
        'user_id': ObjectId(current_user.id)
    })

    if plant_to_update:
        # 1. Update the 'last_watered' status on the plant document
        plants_collection.update_one(
            {'_id': plant_id_obj},
            {'$set': {'last_watered': now}}
        )
        
        # 2. Create a new historical event in the 'care_events' collection
        care_events_collection.insert_one({
            'plant_id': plant_id_obj,
            'user_id': ObjectId(current_user.id),
            'event_type': 'water',
            'event_date': now
        })
    else:
        flash('Plant not found or you do not have permission.', 'error')
    
    return redirect(url_for('index'))

@app.route('/delete/<string:plant_id>', methods=['POST'])
@login_required
def delete_plant(plant_id):
    plant_id_obj = ObjectId(plant_id)

    # Find plant matching ID AND user
    plant_to_delete = plants_collection.find_one({
        '_id': plant_id_obj,
        'user_id': ObjectId(current_user.id)
    })
    
    if plant_to_delete:
        # 1. Delete the plant
        plants_collection.delete_one({'_id': plant_id_obj})
        
        # 2. Delete all associated care events (good hygiene)
        care_events_collection.delete_many({'plant_id': plant_id_obj})
    else:
        flash('Plant not found or you do not have permission.', 'error')

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)