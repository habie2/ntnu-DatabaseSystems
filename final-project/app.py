import os
from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from dotenv import load_dotenv

# --- Load Environment Variables ---
load_dotenv()

# --- App Setup ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_fallback_key_for_dev')

# --- Database Setup ---
mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri)
db = client.plant_watering_db

# Collections
plants_collection = db.plants
users_collection = db.users
care_events_collection = db.care_events
forum_posts_collection = db.forum_posts  # <--- Collection for Forum

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
login_manager.login_view = 'login'

class User(UserMixin):
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
    return User.get(user_id)

# --- Auth Routes ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        existing_user = users_collection.find_one({'email': email})
        if existing_user:
            flash('Email already registered. Please log in.', 'error')
            return redirect(url_for('login'))

        password_hash = generate_password_hash(password)
        new_user_id = users_collection.insert_one({
            'username': username,
            'email': email,
            'password_hash': password_hash
        }).inserted_id

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

# --- Main App Routes ---

@app.route('/')
def index():
    plants = []
    if current_user.is_authenticated:
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
            'user_id': ObjectId(current_user.id)
        }
        new_plant_id = plants_collection.insert_one(plant_document).inserted_id

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
        return redirect(url_for('index'))
    else:
        return render_template('edit_plant.html', plant=plant_to_edit, species_list=available_species)

@app.route('/plant/<string:plant_id>')
@login_required
def plant_detail(plant_id):
    plant_id_obj = ObjectId(plant_id)
    plant = plants_collection.find_one({
        '_id': plant_id_obj,
        'user_id': ObjectId(current_user.id)
    })

    if not plant:
        flash('Plant not found or you do not have permission.', 'error')
        return redirect(url_for('index'))

    events_cursor = care_events_collection.find({
        'plant_id': plant_id_obj,
        'user_id': ObjectId(current_user.id)
    })
    
    events = sorted(events_cursor, key=lambda e: e.get('event_date', datetime.min), reverse=True)
    return render_template('plant_detail.html', plant=plant, events=events)

@app.route('/water/<string:plant_id>', methods=['POST'])
@login_required
def water_plant(plant_id):
    plant_id_obj = ObjectId(plant_id)
    now = datetime.now()

    plant_to_update = plants_collection.find_one({
        '_id': plant_id_obj,
        'user_id': ObjectId(current_user.id)
    })

    if plant_to_update:
        plants_collection.update_one(
            {'_id': plant_id_obj},
            {'$set': {'last_watered': now}}
        )
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
    plant_to_delete = plants_collection.find_one({
        '_id': plant_id_obj,
        'user_id': ObjectId(current_user.id)
    })
    
    if plant_to_delete:
        plants_collection.delete_one({'_id': plant_id_obj})
        care_events_collection.delete_many({'plant_id': plant_id_obj})
    else:
        flash('Plant not found or you do not have permission.', 'error')

    return redirect(url_for('index'))

@app.route('/delete_selected_plants', methods=['POST'])
@login_required
def delete_selected_plants():
    # Get list of selected plant IDs from the checkboxes
    plant_ids = request.form.getlist('plant_ids')
    
    if not plant_ids:
        flash('No plants selected for deletion.', 'warning')
        return redirect(url_for('index'))

    deleted_count = 0
    for plant_id in plant_ids:
        try:
            plant_id_obj = ObjectId(plant_id)
            
            # Security check: Ensure the plant belongs to the current user before deleting
            result = plants_collection.delete_one({
                '_id': plant_id_obj,
                'user_id': ObjectId(current_user.id)
            })
            
            if result.deleted_count > 0:
                # Also delete associated care events
                care_events_collection.delete_many({'plant_id': plant_id_obj})
                deleted_count += 1
                
        except Exception as e:
            print(f"Error deleting plant {plant_id}: {e}")
            continue
    
    flash(f'Successfully deleted {deleted_count} selected plants.', 'info')
    return redirect(url_for('index'))


# --- Forum Routes (RESTORED) ---
@app.route('/forum')
def forum():
    # Get all posts, sorted newest first
    posts_cursor = forum_posts_collection.find()
    posts = sorted(posts_cursor, key=lambda p: p.get('created_at', datetime.min), reverse=True)
    return render_template('forum.html', posts=posts)

@app.route('/forum/new', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        
        post_document = {
            'user_id': ObjectId(current_user.id),
            'username': current_user.username,
            'title': title,
            'content': content,
            'created_at': datetime.now()
        }
        forum_posts_collection.insert_one(post_document)
        return redirect(url_for('forum'))
        
    return render_template('create_post.html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5002))
    
    # host='0.0.0.0' visible externally
    app.run(host='0.0.0.0', port=port)  
