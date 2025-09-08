from flask import Flask, request, render_template_string
import mysql.connector
import config

app = Flask(__name__)

# --- DB connection ---
def get_db_connection():
    conn = mysql.connector.connect(
        host=config.DB_HOST,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME
    )
    return conn

# --- Routes ---
@app.route("/")
def home():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template_string("""
        <h1>Users</h1>
        <ul>
        {% for u in users %}
          <li>{{ u['name'] }}</li>
        {% endfor %}
        </ul>
        <form method="post" action="/add">
          <input name="name" placeholder="New user">
          <button type="submit">Add</button>
        </form>
    """, users=users)

@app.route("/add", methods=["POST"])
def add():
    name = request.form["name"]
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (name) VALUES (%s)", (name,))
    conn.commit()
    cursor.close()
    conn.close()
    return ("<p>User added!</p><a href='/'>Back</a>")

if __name__ == "__main__":
    app.run(debug=True)
