import os
from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

app = Flask(__name__)

client = MongoClient('mongodb://localhost:27017/')
db = client.plant_watering_db  
plants_collection = db.plants

@app.route('/')
def index():
    all_plants = plants_collection.find()
    all_plants = list(all_plants)
    return render_template('index.html', plants=all_plants)

SPECIES_IMAGES = {
    'Monstera': 'images/monstera.png',
    'Pothos': 'images/pothos.png',
    'Suculenta': 'images/suculenta.png',
    'Sansevieria': 'images/sansevieria.png',
}
DEFAULT_IMAGE = 'images/default.png'

@app.route('/add', methods=['GET', 'POST'])
def add_plant():
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
            'created_at': datetime.now()
        }
        plants_collection.insert_one(plant_document)

        return redirect(url_for('index'))

    available_species = list(SPECIES_IMAGES.keys())
    return render_template('add_plant.html', species_list=available_species)

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
        print(f"Error when watering a plant: {e}")

    return redirect(url_for('index'))

@app.route('/delete/<string:plant_id>', methods=['POST'])
def delete_plant(plant_id):
    try:
        plant_id_obj = ObjectId(plant_id)
        
        plants_collection.delete_one({'_id': plant_id_obj})
        
    except Exception as e:
        print(f"Error deleting the plant: {e}")

    return redirect(url_for('index'))

@app.route('/delete_multiple', methods=['POST'])
def delete_multiple():
    try:
        # Obtener la lista de IDs seleccionados del formulario
        plant_ids = request.form.getlist('plant_ids')
        
        if plant_ids:
            # Convertir los strings de ID a objetos ObjectId
            object_ids = [ObjectId(pid) for pid in plant_ids]
            
            # Eliminar todos los documentos que coincidan con esos IDs
            plants_collection.delete_many({'_id': {'$in': object_ids}})
            
    except Exception as e:
        print(f"Error deleting multiple plants: {e}")

    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    
    # host='0.0.0.0' visible externally
    app.run(host='0.0.0.0', port=port)  