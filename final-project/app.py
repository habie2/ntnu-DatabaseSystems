import os
from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime, timedelta

app = Flask(__name__)

# --- Conexión a MongoDB ---
# Para que la aplicación funcione, asegúrate de que MongoDB se esté ejecutando en tu máquina.
# La cadena de conexión 'mongodb://localhost:27017/' asume que MongoDB
# está corriendo en el puerto por defecto.
client = MongoClient('mongodb://localhost:27017/')
db = client.plant_watering_db  # Nombre de la base de datos
plants_collection = db.plants   # Nombre de la colección

# --- Rutas de la Aplicación ---

@app.route('/')
def index():
    """
    Página principal que muestra todas las plantas.
    Obtiene las plantas, calcula los días desde el último riego y las
    ordena para mostrar primero las que necesitan agua con más urgencia.
    """
    all_plants_cursor = plants_collection.find()
    
    plants_list = []
    for plant in all_plants_cursor:
        # Calcula la diferencia de días desde el último riego
        days_since_watering = (datetime.utcnow() - plant['last_watered']).days
        plant['days_since_watering'] = days_since_watering
        plants_list.append(plant)

    # Ordena la lista: las plantas no regadas por más tiempo aparecen primero
    plants_list.sort(key=lambda x: x['days_since_watering'], reverse=True)

    return render_template('index.html', plants=plants_list, now=datetime.utcnow())

@app.route('/add', methods=['GET', 'POST'])
def add_plant():
    """
    Maneja la adición de nuevas plantas.
    Si es GET, muestra el formulario.
    Si es POST, procesa los datos del formulario y los guarda en MongoDB.
    """
    if request.method == 'POST':
        plant_name = request.form['plant_name']
        plant_species = request.form['plant_species']
        last_watered_str = request.form['last_watered']

        # Convierte la cadena de fecha a un objeto datetime
        last_watered_date = datetime.strptime(last_watered_str, '%Y-%m-%d')

        # Crea el documento para insertar en la colección
        plant_document = {
            'name': plant_name,
            'species': plant_species,
            'last_watered': last_watered_date,
            'created_at': datetime.utcnow()
        }
        plants_collection.insert_one(plant_document)

        # Redirige a la página principal después de añadir la planta
        return redirect(url_for('index'))

    # Si es un request GET, simplemente muestra el formulario
    return render_template('add_plant.html')

@app.route('/edit/<plant_id>', methods=['GET', 'POST'])
def edit_plant(plant_id):
    """
    Maneja la edición de una planta existente.
    Busca la planta por su ID. Si es GET, muestra el formulario de edición
    con los datos actuales. Si es POST, actualiza los datos en MongoDB.
    """
    plant_oid = ObjectId(plant_id)
    plant_to_edit = plants_collection.find_one({'_id': plant_oid})

    if request.method == 'POST':
        # Obtiene los datos actualizados del formulario
        updated_name = request.form['plant_name']
        updated_species = request.form['plant_species']
        updated_last_watered_str = request.form['last_watered']
        updated_last_watered_date = datetime.strptime(updated_last_watered_str, '%Y-%m-%d')

        # Actualiza el documento en la base de datos
        plants_collection.update_one(
            {'_id': plant_oid},
            {'$set': {
                'name': updated_name,
                'species': updated_species,
                'last_watered': updated_last_watered_date
            }}
        )
        return redirect(url_for('index'))

    # Para un request GET, renderiza el formulario con los datos existentes
    return render_template('edit_plant.html', plant=plant_to_edit)

@app.route('/delete/<plant_id>', methods=['POST'])
def delete_plant(plant_id):
    """
    Elimina una planta de la base de datos.
    Esta ruta solo acepta el método POST por seguridad, para evitar
    eliminaciones accidentales a través de un simple enlace.
    """
    plant_oid = ObjectId(plant_id)
    plants_collection.delete_one({'_id': plant_oid})
    return redirect(url_for('index'))


if __name__ == '__main__':
    # El modo debug permite ver los cambios sin reiniciar el servidor manualmente.
    app.run(debug=True)

