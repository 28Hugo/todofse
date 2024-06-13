from flask import Flask, render_template, request, redirect, url_for
import uuid

app = Flask(__name__)

# In-memory storage for tasks
tasks = []

# Updated categories
categories = ['Uni', 'Arbeit', 'Privat']

@app.route('/')
def index():
    # Separate tasks into pending and completed
    pending_tasks = [task for task in tasks if not task['completed']]
    completed_tasks = [task for task in tasks if task['completed']]
    return render_template('index.html', pending_tasks=pending_tasks, completed_tasks=completed_tasks, categories=categories)

@app.route('/add', methods=['POST'])
def add_task():
    task_content = request.form.get('content', '')
    task_category = request.form.get('category', '')  # Access 'category' field from form
    if task_content:
        task_id = str(uuid.uuid4())
        tasks.append({'id': task_id, 'content': task_content, 'category': task_category, 'completed': False})
    return redirect(url_for('index'))

@app.route('/update/<task_id>', methods=['POST'])
def update_task(task_id):
    for task in tasks:
        if task['id'] == task_id:
            task['completed'] = 'completed' in request.form
            break
    return redirect(url_for('index'))

@app.route('/delete/<task_id>', methods=['POST'])
def delete_task(task_id):
    global tasks
    tasks = [task for task in tasks if task['id'] != task_id]
    return redirect(url_for('index'))

@app.route('/edit/<task_id>', methods=['POST'])
def edit_task(task_id):
    new_content = request.form.get('content', '')
    new_category = request.form.get('category', '')
    for task in tasks:
        if task['id'] == task_id:
            task['content'] = new_content
            task['category'] = new_category
            break
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
