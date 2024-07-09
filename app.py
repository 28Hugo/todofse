import json
from datetime import datetime
import time

from bson import ObjectId
from flask import Flask, request, jsonify, send_from_directory, redirect, render_template, url_for
from flask_bcrypt import Bcrypt
from pymongo import MongoClient, DESCENDING
from flask_cors import CORS
import requests

from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user


class User(UserMixin):
    def __init__(self, user_dict):
        self.id = str(user_dict["_id"])
        self.email = user_dict["email"]


# create a new Flask application
app = Flask(__name__)
CORS(app)
app.app_context()
app.secret_key = 'superSecretKey'
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.init_app(app)
bcrypt = Bcrypt(app)

db = MongoClient("mongodb://mongo:27017").get_database("mydatabase")
# collection instance
users = db['users']
tasks_collection = db["tasks"]
notes_collection = db["notes"]

# Updated categories
categories = ['uni', 'work', 'private']

# Your OpenWeatherMap API key
WEATHER_API_KEY = '2321d60237674c67b4595038241006'


def get_relevant_weather(data: dict) -> list[dict]:
    hours = data["forecast"]["forecastday"][0]["hour"]
    current_time = time.time()
    return_hours: list[dict] = []
    hour: dict[str, object]
    for hour in hours:
        if int(str(hour["time_epoch"])) > current_time:
            return_hours.append(hour)
    if len(return_hours) < 5:
        return return_hours
    else:
        return return_hours[:5]


def get_weather_icon_class(condition_text: str) -> str:
    if condition_text == "Sunny":
        return "fa-sun"
    elif "partly cloudy" in condition_text.lower():
        return "fa-cloud-sun"
    elif condition_text == "Cloudy":
        return "fa-cloud"
    elif "clear" in condition_text.lower():
        return "fa-moon"
    elif "light rain" in condition_text.lower():
        return "fa-cloud-rain"
    elif "moderate rain" in condition_text.lower():
        return "fa-cloud-rain"
    elif "snow" in condition_text.lower():
        return "fa-snowflake"
    elif "heavy rain" in condition_text.lower():
        return "fa-cloud-showers-heavy"
    elif "rain" in condition_text.lower():
        return "fa-cloud-rain"
    else:
        print(condition_text)
        return "fa-notdef"


app.jinja_env.globals.update(get_weather_icon_class=get_weather_icon_class)


@app.template_filter('formatdatetime')
def format_datetime(value):
    date = datetime.strptime(value, "%Y-%m-%d %H:%M")

    return date.strftime('%H Uhr')


@app.get('/test')
def style_test():
    return render_template('style-test.html')


@app.get('/tasks')
def tasks():
    _tasks = tasks_collection.find({"user_id": current_user.get_id()}, sort=[('status', DESCENDING)])

    return render_template('tasks.html', tasks=_tasks, categories=categories)


@app.route('/tasks/add', methods=['POST'])
def add_task():
    task_content = request.form.get('content')
    task_category = request.form.get('category')
    task_date = request.form.get('date')
    task_status = request.form.get('status')
    if task_content:
        tasks_collection.insert_one(
            {"user_id": current_user.get_id(), 'content': task_content, 'category': task_category, 'date': task_date,
             'status': task_status})
    return redirect(url_for('tasks'))


@app.route('/tasks/delete/<task_id>', methods=['POST'])
def delete_task(task_id):
    tasks_collection.delete_one({'_id': ObjectId(task_id)})
    return redirect(url_for('tasks'))


@app.route('/tasks/edit/<task_id>', methods=['POST'])
def edit_task(task_id):
    new_content = request.form.get('content')
    new_category = request.form.get('category')
    new_date = request.form.get('date')
    new_status = request.form.get('status')
    print({'content': new_content, 'category': new_category, 'date': new_date, 'status': new_status})
    tasks_collection.update_one({'_id': ObjectId(task_id)},
                                {"$set": {'content': new_content, 'category': new_category, 'date': new_date,
                                          'status': new_status}}, upsert=False)
    return redirect(url_for('tasks'))


def get_weather(city):
    url = f"https://api.weatherapi.com/v1/forecast.json?key={WEATHER_API_KEY}&q={city}&aqi=no&hour_fields=temp_c,will_it_rain,cloud,condition:text"
    response = requests.get(url)
    if response.status_code == 200:
        return jsonify(response.json()), response.status_code
    else:
        return jsonify({"error": "Unable to fetch weather data"}), response.status_code


# API default endpoint
@app.route('/', methods=['GET'])
@login_required
def default():
    city = "Berlin" if request.args.get('city') is None else request.args.get('city')
    _notes = notes_collection.find({'user_id': current_user.get_id()})
    _pending_tasks = tasks_collection.find({'user_id': current_user.get_id(), "status": {"$ne": "completed"}})
    _weather = get_weather(city)[0].json
    _hours: list = get_relevant_weather(_weather)
    return render_template("dashboard.html", notes=_notes, pending_tasks=_pending_tasks, weather=_weather, hours=_hours)


@login_manager.user_loader
def load_user(user_id) -> User:
    user_dict = users.find_one({'_id': ObjectId(user_id)})
    return User(user_dict)


@app.route('/register', methods=['GET'])
def register_form():
    return send_from_directory("frontend", 'register.html')


@app.route('/register', methods=['POST'])
def register():
    # Get data from request
    email = request.form.get('username')
    password = request.form.get('password')

    # Check if email already exists
    if users.find_one({'email': email}):
        return jsonify({'error': 'Email already exists'}), 400

    # Hash the password
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    # Create a new user
    user = {
        'email': email,
        'password': hashed_password,
    }

    # Insert the user in the database
    users.insert_one(user)

    return redirect(url_for("login_form"))


@app.route('/login', methods=['GET'])
def login_form():
    return send_from_directory("frontend", 'login.html')


@app.route('/login', methods=['POST'])
def login():
    # Get data from request
    email = request.form.get('username')
    password = request.form.get('password')
    # Find the user by email
    user = users.find_one({'email': email})

    # If user doesn't exist or password is wrong
    if not user or not bcrypt.check_password_hash(user['password'], password):
        return jsonify({"error": "Invalid credentials"}), 400

    # Log in the user and establish the session
    user_dict = {
        "_id": str(user["_id"]),
        "email": email
    }
    login_user(User(user_dict))

    return redirect(url_for('default'))


@app.route('/notes', methods=['GET'])
def get_notes():
    _notes = notes_collection.find({"user_id": current_user.get_id()}, sort=[('created_at', DESCENDING)])
    return render_template('notes.html', notes=_notes)


@app.route('/notes/add', methods=['POST'])
def add_note():
    title = request.form.get('title')
    content = request.form.get('content')
    notes_collection.insert_one({
        'title': title,
        'content': content,
        'user_id': current_user.get_id(),
        'created_at': datetime.now(),
        'updated_at': datetime.now(),
    })
    return redirect(url_for('get_notes'))


@app.route('/note/<note_id>')
def note_detail(note_id):
    note = notes_collection.find_one({'_id': ObjectId(note_id)})
    return render_template('note.html', note=note)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('default'))


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
