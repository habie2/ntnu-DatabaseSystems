from pymongo import MongoClient
from datetime import datetime, timedelta

def seed_database():
    """
    Este script se conecta a la base de datos de MongoDB y, si la colección
    'plants' está vacía, inserta una lista de plantas de ejemplo.
    """
    # --- 1. Conexión a MongoDB (misma configuración que en app.py) ---
    try:
        client = MongoClient('mongodb://localhost:27017/')
        db = client.plant_watering_db
        plants_collection = db.plants
        # Comprobar si la conexión fue exitosa
        client.admin.command('ping') 
        print("✅ Conexión a MongoDB exitosa.")
    except Exception as e:
        print(f"❌ Error al conectar con MongoDB: {e}")
        return

    # --- 2. Comprobar si la colección ya tiene datos ---
    if plants_collection.count_documents({}) > 0:
        print("ℹ️ La colección 'plants' ya contiene datos. No se realizará ninguna acción.")
        client.close()
        return

    # --- 3. Definir los datos de ejemplo ---
    # Usamos datetime y timedelta para que las fechas sean relativas al día de hoy.
    print("🌱 La colección está vacía. Preparando datos de ejemplo...")
    plants_data = [
        {
            'name': 'Monstera Deliciosa',
            'species': 'Costilla de Adán',
            'last_watered': datetime.utcnow() - timedelta(days=2),
            'created_at': datetime.utcnow()
        },
        {
            'name': 'Ficus Lyrata',
            'species': 'Higuera de hoja de violín',
            'last_watered': datetime.utcnow() - timedelta(days=5),
            'created_at': datetime.utcnow()
        },
        {
            'name': 'Sansevieria Zeylanica',
            'species': 'Lengua de suegra',
            'last_watered': datetime.utcnow() - timedelta(days=15),
            'created_at': datetime.utcnow()
        },
        {
            'name': 'Pilea Peperomioides',
            'species': 'Planta del dinero china',
            'last_watered': datetime.utcnow(), # Regada hoy
            'created_at': datetime.utcnow()
        },
        {
            'name': 'Orquídea',
            'species': 'Phalaenopsis',
            'last_watered': datetime.utcnow() - timedelta(days=8),
            'created_at': datetime.utcnow()
        }
    ]

    # --- 4. Insertar los datos en la colección ---
    try:
        result = plants_collection.insert_many(plants_data)
        print(f"🚀 ¡Éxito! Se han insertado {len(result.inserted_ids)} plantas de ejemplo.")
    except Exception as e:
        print(f"❌ Error al insertar los datos: {e}")
    finally:
        # --- 5. Cerrar la conexión ---
        client.close()
        print("🔌 Conexión a MongoDB cerrada.")

if __name__ == '__main__':
    seed_database()
'''

### Cómo Usarlo

1.  **Guarda el Código:** Guarda este código en un archivo llamado `seed_database.py` en la misma carpeta principal de tu proyecto (junto a `app.py`).

2.  **Asegúrate de que MongoDB esté Corriendo:** El servidor de MongoDB debe estar activo para que el script pueda conectarse.

3.  **Ejecuta el Script desde la Terminal:**
    Abre tu terminal, asegúrate de estar en la carpeta del proyecto y ejecuta el siguiente comando:
    ```bash
    python seed_database.py
    ```

# ### Qué Verás en la Terminal

# **Si la base de datos está vacía, verás algo como esto:**
# ```
# ✅ Conexión a MongoDB exitosa.
# 🌱 La colección está vacía. Preparando datos de ejemplo...
# 🚀 ¡Éxito! Se han insertado 5 plantas de ejemplo.
# 🔌 Conexión a MongoDB cerrada.
# ```

# **Si vuelves a ejecutar el script (o si ya tenías datos), verás esto:**
# ```
# ✅ Conexión a MongoDB exitosa.
# ℹ️ La colección 'plants' ya contiene datos. No se realizará ninguna acción.
'''