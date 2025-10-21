from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
# Asumo que tu config.py tiene SECRET_KEY y las credenciales de MySQL
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

mysql = MySQL(app)


@app.route('/')
def home():
    return render_template('base.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm = request.form['confirm']

        if password != confirm:
            flash('The passwords do not match.', 'danger')
            return redirect(url_for('register'))

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
        if cur.fetchone():
            flash('The username or email already exists.', 'danger')
            return redirect(url_for('register'))

        cur.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                      (username, email, password))
        mysql.connection.commit()
        cur.close()

        flash('Registration successful. You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

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
            session['user_id'] = user['id']  

            flash('Welcome ' + user['username'], 'success')
            return redirect(url_for('profile'))
        else:
            flash('Invalid credentials', 'danger')

    return render_template('login.html')

@app.route('/profile')
def profile():
    if 'logged_in' in session:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
        user = cur.fetchone()
        cur.close()
        return render_template('profile.html', user=user)
    else:
        flash('You must be logged in to view this page.', 'warning')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))


@app.route('/update_profile', methods=['GET', 'POST'])
def update_profile():
    # only for logged in users
    if 'logged_in' not in session:
        flash('You should be logged in to do this.', 'warning')
        return redirect(url_for('login'))
    
    # Obtenemos el ID del usuario desde la sesión
    user_id = session['user_id']
    cur = mysql.connection.cursor()
    
    if request.method == 'POST':
        new_username = request.form['username']
        new_email = request.form['email']

        cur.execute(
            "UPDATE users SET username = %s, email = %s WHERE id = %s",
            (new_username, new_email, user_id)
        )
        mysql.connection.commit()
        
        session['username'] = new_username

        flash('Your profile has been updated successfully.', 'success')
        return redirect(url_for('profile'))

    # If the method is GET, show the form with the current data
    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()
    return render_template('update_profile.html', user=user)

@app.route('/delete_profile', methods=['POST'])
def delete_profile():
    if 'logged_in' not in session:
        flash('You should be logged in to do this.', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']
    cur = mysql.connection.cursor()
    
    cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
    mysql.connection.commit()
    cur.close()
    
    session.clear()

    flash('Your account has been permanently deleted.', 'info')
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)