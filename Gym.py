from flask import Flask, render_template, request, redirect, url_for, g
import sqlite3
import datetime

app = Flask(__name__)

# Configuration
app.config['DATABASE'] = 'gym_system.db'


def connect_db():
    return sqlite3.connect(app.config['DATABASE'])


# Create members table if not exists
with app.app_context():
    db = connect_db()
    cursor = db.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS members
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       nom TEXT,
                       prenom TEXT,
                       date_expiration DATETIME)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS attendance
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       member_id INTEGER,
                       entry_time DATETIME,
                       exit_time DATETIME,
                       FOREIGN KEY (member_id) REFERENCES members (id))''')
    db.commit()
    db.close()


def get_db():
    if 'db' not in g:
        g.db = connect_db()
    return g.db


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'db'):
        g.db.close()


@app.route('/')
def accueil():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM members")
    membres = cursor.fetchall()
    return render_template('accueil.html', membres=membres)


@app.route('/ajouter_membre', methods=['POST', 'GET'])
def ajouter_membre():
    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenom']
        date_expiration = datetime.datetime.now() + datetime.timedelta(days=30)

        db = get_db()
        cursor = db.cursor()

        # Insert data into the members table
        cursor.execute("INSERT INTO members (nom, prenom, date_expiration) VALUES (?, ?, ?)",
                       (nom, prenom, date_expiration))
        db.commit()

        return redirect('/')

    return render_template('ajouter_membre.html')


@app.route('/entrer_sortir', methods=['POST', 'GET'])
def entrer_sortir():
    db = get_db()
    cursor = db.cursor()

    if request.method == 'POST':
        member_id = request.form['member_id']
        action = request.form['action']
        current_time = datetime.datetime.now()

        if action == 'entrer':
            # Insert data into the attendance table for entry
            cursor.execute("INSERT INTO attendance (member_id, entry_time) VALUES (?, ?)",
                           (member_id, current_time))
        elif action == 'sortir':
            # Update the exit_time for the latest entry
            cursor.execute("UPDATE attendance SET exit_time = ? WHERE member_id = ? AND exit_time IS NULL",
                           (current_time, member_id))

        db.commit()

    cursor.execute("SELECT members.nom, members.prenom, attendance.entry_time, attendance.exit_time "
                   "FROM members LEFT JOIN attendance ON members.id = attendance.member_id")
    entries = cursor.fetchall()

    return render_template('entrer_sortir.html', entries=entries)


if __name__ == "__main__":
    app.run(debug=True)
