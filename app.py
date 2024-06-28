from datetime import datetime

from bson import ObjectId
from flask import Flask, request, jsonify, send_from_directory, g, redirect, render_template, url_for
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
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
todos = db["Todos"]
notes_collection = db["Notes"]

# Your OpenWeatherMap API key
WEATHER_API_KEY = '2321d60237674c67b4595038241006'


# API endpoint to get todos data
@app.route('/todos', methods=['GET'])
def get_todos():
    all_todos = todos.find()

    result = []
    for todo in all_todos:
        item = {
            "id": str(todo['_id']),
            "user_id": todo['user_id'],
            "title": todo['title'],
            "description": todo['description'],
            "created_at": todo['created_at'].strftime('%Y-%m-%d %H:%M:%S') if todo.get('created_at') else None,
            "updated_at": todo['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if todo.get('updated_at') else None,
            "due_date": todo['due_date'].strftime('%Y-%m-%d %H:%M:%S') if todo.get('due_date') else None,
            "completed": todo['completed'],
            "priority": todo['priority'],
        }
        result.append(item)
    return jsonify(result), 200


@app.route('/todos/<id>', methods=['GET'])
def get_todo(_id):
    todo = todos.find_one({'_id': ObjectId(_id)})
    if todo:
        # Do data processing here and return the data
        return_data = {
            "id": str(todo.get('_id')),
            "user_id": todo.get('user_id'),
            "title": todo.get('title'),
            "description": todo.get('description'),
            "created_at": todo.get('created_at').strftime('%Y-%m-%d %H:%M:%S') if todo.get('created_at') else None,
            "updated_at": todo.get('updated_at').strftime('%Y-%m-%d %H:%M:%S') if todo.get('updated_at') else None,
            "due_date": todo.get('due_date').strftime('%Y-%m-%d %H:%M:%S') if todo.get('due_date') else None,
            "completed": todo.get('completed'),
            "priority": todo.get('priority'),
        }
        return jsonify(return_data), 200
    else:
        # Return not found if no Todo_element with that ID is found
        return jsonify({'error': 'Todo not found'}), 404


# API endpoint to add customer data
@app.route('/todos', methods=['POST'])
def add_todo():
    data = request.get_json()
    new_todo = {
        'user_id': data.get('user_id'),  # Get user_id from the request data
        'title': data.get('title'),
        'description': data.get('description', ''),  # Default to empty string if no description provided
        'created_at': datetime.now(),
        'updated_at': datetime.now(),
        'due_date': datetime.strptime(data.get('due_date'), '%Y-%m-%d') if data.get('due_date') else None,
        # Convert string date to datetime
        'completed': data.get('completed', False),  # Default to False if no completion status provided
        'priority': data.get('priority', 'Medium'),  # Default to Medium if no priority level provided
    }
    x = todos.insert_one(new_todo)
    return jsonify({"id": str(x.inserted_id)}), 201


# API endpoint to get weather data
@app.route('/weather', methods=['GET'])
def get_weather():
    city = request.args.get('city', default='London')
    url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={city}&aqi=no"
    response = requests.get(url)
    if response.status_code == 200:
        return jsonify(response.json()), response.status_code
    else:
        return jsonify({"error": "Unable to fetch weather data"}), response.status_code


# API default endpoint
@app.route('/', methods=['GET'])
@login_required
def default():
    _notes = notes_collection.find({'user_id': current_user.get_id()})
    return render_template("dashboard.html", notes=_notes)


@login_manager.user_loader
def load_user(user_id) -> User:
    users = db['users']
    user_dict = users.find_one({'_id': ObjectId(user_id)})
    return User(user_dict)


@app.route('/register', methods=['GET'])
def register_form():
    return send_from_directory("frontend", 'register.html')


@app.route('/register', methods=['POST'])
def register():
    users = db['users']
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
    users = db['users']
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


@app.route('/notes', methods=['GET', 'POST'])
def notes():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        notes_collection.insert_one({
            'title': title,
            'content': content,
            'user_id': current_user.get_id(),
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            })
        return redirect(url_for('notes'))
    else:
        _notes = notes_collection.find({"user_id": current_user.get_id()})
        return render_template('notes.html', notes=_notes)


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
