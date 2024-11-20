from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from bs4 import BeautifulSoup
import requests
from win10toast import ToastNotifier
import threading
from notifications import notification_manager  # Import the notification manager
import csv

app = Flask(__name__, template_folder='.')
app.config['SECRET_KEY'] = 'b674cd39e520181aca43fe4157e33763'  # Replace with your secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Initialize Flask-Admin
admin = Admin(app, name='Admin Panel', template_mode='bootstrap3')

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
	

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/registration', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created!', 'success')
        return redirect(url_for('login'))
    return render_template('registration.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user:
            if bcrypt.check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for('index'))
            else:
                flash('Invalid password. Please try again.', 'danger')
        else:
            flash('Invalid username. Please try again.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    notification_manager.stop()  # Stop notifications on logout
    logout_user()
    return redirect(url_for('login'))

def get_current_matches():
    try:
        page = requests.get('http://static.cricinfo.com/rss/livescores.xml', timeout=10)
        page.raise_for_status()  # Raise HTTPError for bad responses
        soup = BeautifulSoup(page.text, 'lxml')
        matches = soup.find_all('description')
        live_matches = [s.get_text() for s in matches if '*' in s.get_text()]
        return live_matches
    except requests.exceptions.RequestException as e:
        print(f"Error fetching live scores: {e}")
        return []

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        if 'match' in request.form:
            selected_match = int(request.form['match'])
            notification_manager.start(selected_match)
        elif 'stop_notifications' in request.form:
            notification_manager.stop()
    matches = get_current_matches()
    return render_template('index.html', matches=enumerate(matches))

@app.route('/player_search', methods=['GET', 'POST'])
@login_required
def player_search():
    players = []
    if request.method == 'POST':
        search_query = request.form['search_query'].lower()
        with open('playersdata.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if (search_query in row['firstname'].lower() or 
                    search_query in row['lastname'].lower() or
                    search_query in f"{row['firstname'].lower()} {row['lastname'].lower()}"):
                    players.append(row)
    return render_template('player_search.html', players=players)

# Add the User model to Flask-Admin
admin.add_view(ModelView(User, db.session))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
