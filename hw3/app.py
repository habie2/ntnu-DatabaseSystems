import os
from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

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
    Obtiene todas las plantas de la colección y las renderiza en index.html.
    """
    all_plants = plants_collection.find()
    return render_template('index.html', plants=all_plants)

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

if __name__ == '__main__':
    # El modo debug permite ver los cambios sin reiniciar el servidor manualmente.
    app.run(debug=True)