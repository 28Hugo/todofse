from flask import Flask, render_template, request, redirect, url_for
import uuid

app = Flask(__name__)

# In-memory storage for tasks
tasks = []

@app.route('/')
def index():
    # Separate tasks into pending and completed
    pending_tasks = [task for task in tasks if not task['completed']]
    completed_tasks = [task for task in tasks if task['completed']]
    return render_template('index.html', pending_tasks=pending_tasks, completed_tasks=completed_tasks)

@app.route('/add', methods=['POST'])
def add_task():
    task_content = request.form['content']
    if task_content:
        task_id = str(uuid.uuid4())
        tasks.append({'id': task_id, 'content': task_content, 'completed': False})
    return redirect(url_for('index'))

@app.route('/complete/<task_id>')
def complete_task(task_id):
    for task in tasks:
        if task['id'] == task_id:
            task['completed'] = True
            break
    return redirect(url_for('index'))

@app.route('/delete/<task_id>')
def delete_task(task_id):
    global tasks
    tasks = [task for task in tasks if task['id'] != task_id]
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
