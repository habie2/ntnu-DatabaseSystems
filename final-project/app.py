import os
from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

app = Flask(__name__)

# --- Database Setup ---
client = MongoClient('mongodb://localhost:27017/')
db = client.plant_watering_db
plants_collection = db.plants

# --- Image Definitions ---
# This logic will be used when adding AND editing plants
SPECIES_IMAGES = {
    'Monstera': 'images/monstera.png',
    'Pothos': 'images/pothos.png',
    'Succulent': 'images/suculenta.png', # You can rename the image files too
    'Snake Plant': 'images/sansevieria.png', # Renamed for clarity
}
DEFAULT_IMAGE = 'images/default.png'

# --- Main Route (Show All Plants) ---
@app.route('/')
def index():
    all_plants = list(plants_collection.find())
    # Sort by creation date, newest first
    all_plants_sorted = sorted(all_plants, key=lambda p: p.get('created_at', datetime.min), reverse=True)
    return render_template('index.html', plants=all_plants_sorted)

# --- Add New Plant ---
@app.route('/add', methods=['GET', 'POST'])
def add_plant():
    available_species = list(SPECIES_IMAGES.keys())
    
    if request.method == 'POST':
        plant_name = request.form['plant_name']
        plant_species = request.form['plant_species']
        last_watered_str = request.form['last_watered']

        last_watered_date = datetime.strptime(last_watered_str, '%Y-%m-%d')
        
        # Get the correct image URL
        plant_image_url = SPECIES_IMAGES.get(plant_species, DEFAULT_IMAGE)

        plant_document = {
            'name': plant_name,
            'species': plant_species,
            'last_watered': last_watered_date,
            'image_url': plant_image_url,
            'created_at': datetime.now()
        }
        plants_collection.insert_one(plant_document)

        return redirect(url_for('index'))

    # If GET request, just show the form
    return render_template('add_plant.html', species_list=available_species)

# --- NEW: Edit Existing Plant ---
@app.route('/edit/<string:plant_id>', methods=['GET', 'POST'])
def edit_plant(plant_id):
    try:
        plant_id_obj = ObjectId(plant_id)
        plant_to_edit = plants_collection.find_one({'_id': plant_id_obj})

        if not plant_to_edit:
            # Handle case where plant is not found
            return redirect(url_for('index'))

        available_species = list(SPECIES_IMAGES.keys())

        if request.method == 'POST':
            # --- This is the POST logic (Save Changes) ---
            # Get updated data from the form
            updated_name = request.form['plant_name']
            updated_species = request.form['plant_species']
            updated_last_watered_str = request.form['last_watered']
            
            updated_last_watered = datetime.strptime(updated_last_watered_str, '%Y-%m-%d')
            
            # Re-check and update the image URL based on the new species
            updated_image_url = SPECIES_IMAGES.get(updated_species, DEFAULT_IMAGE)
            
            # Create the update operation
            update_data = {
                '$set': {
                    'name': updated_name,
                    'species': updated_species,
                    'last_watered': updated_last_watered,
                    'image_url': updated_image_url
                }
            }
            
            # Apply the update to the database
            plants_collection.update_one({'_id': plant_id_obj}, update_data)
            
            return redirect(url_for('index'))

        else:
            # --- This is the GET logic (Show Form) ---
            # Pass the existing plant data to the template
            return render_template('edit_plant.html', plant=plant_to_edit, species_list=available_species)

    except Exception as e:
        print(f"Error editing plant: {e}")
        return redirect(url_for('index'))


# --- Water Plant (No changes, just English comments) ---
@app.route('/water/<string:plant_id>', methods=['POST'])
def water_plant(plant_id):
    try:
        plant_id_obj = ObjectId(plant_id)
        filter_query = {'_id': plant_id_obj}
        update_operation = {
            '$set': {
                'last_watered': datetime.now()
            }
        }
        plants_collection.update_one(filter_query, update_operation)
    except Exception as e:
        print(f"Error watering plant: {e}")
    
    return redirect(url_for('index'))

# --- Delete Plant (No changes, just English comments) ---
@app.route('/delete/<string:plant_id>', methods=['POST'])
def delete_plant(plant_id):
    try:
        plant_id_obj = ObjectId(plant_id)
        plants_collection.delete_one({'_id': plant_id_obj})
    except Exception as e:
        print(f"Error deleting plant: {e}")

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)