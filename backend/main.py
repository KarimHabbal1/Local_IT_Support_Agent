from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import sqlite3

app = FastAPI()

# Database setup
conn = sqlite3.connect('support_agent.db', check_same_thread=False)
cursor = conn.cursor()

# Models
class User(BaseModel):
    id: Optional[int]
    username: str

class Task(BaseModel):
    id: Optional[int]
    issue: str
    status: str
    assigned_to: Optional[int]
    logs: Optional[str]

# Routes
@app.post('/tasks', response_model=Task)
def create_task(task: Task):
    cursor.execute('INSERT INTO tasks (issue, status, assigned_to, logs) VALUES (?, ?, ?, ?)',
                   (task.issue, task.status, task.assigned_to, task.logs))
    conn.commit()
    task_id = cursor.lastrowid
    return {"id": task_id, **task.dict()}

@app.put('/tasks/{task_id}', response_model=Task)
def update_task(task_id: int, task: Task):
    cursor.execute('SELECT * FROM tasks WHERE id=?', (task_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail='Task not found')
    cursor.execute('UPDATE tasks SET issue=?, status=?, assigned_to=?, logs=? WHERE id=?',
                   (task.issue, task.status, task.assigned_to, task.logs, task_id))
    conn.commit()
    return {"id": task_id, **task.dict()}

@app.put('/tasks/{task_id}/close', response_model=Task)
def close_task(task_id: int):
    cursor.execute('SELECT * FROM tasks WHERE id=?', (task_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail='Task not found')
    cursor.execute('UPDATE tasks SET status=? WHERE id=?', ('closed', task_id))
    conn.commit()
    return {
        "id": row[0],
        "issue": row[1],
        "status": "closed",
        "assigned_to": row[3],
        "logs": row[4]
    }
