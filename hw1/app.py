from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

mysql = MySQL(app)

# Home page
@app.route('/')
def home():
    return render_template('base.html')

# User registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm = request.form['confirm']

        if password != confirm:
            flash('Las contraseñas no coinciden', 'danger')
            return redirect(url_for('register'))

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                    (username, email, password))
        mysql.connection.commit()
        cur.close()

        flash('Registe was a success, youo can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password_candidate = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()

        if user and (password_candidate == user['password']):
            session['logged_in'] = True
            session['username'] = user['username']
            flash('Bienvenido ' + user['username'], 'success')
            return redirect(url_for('profile'))
        else:
            flash('Incorrect credentials', 'danger')

    return render_template('login.html')

# Profile view
@app.route('/profile')
def profile():
    if 'logged_in' in session:
        # We have to add username variable 0in order to display the username in the template.
        return render_template('profile.html', username=session['username'])
    else:
        flash('You must be logged in to view this page.', 'warning')
        return redirect(url_for('login'))

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
