import json
import os

# Persistent storage for To-Do items using local JSON file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TODO_FILE = os.path.join(BASE_DIR, "todo.json")


def load_todos():
    """
    Load all tasks from persistent storage.
    Returns empty list if file does not exist or is unreadable.
    """
    if not os.path.exists(TODO_FILE):
        return []
    try:
        with open(TODO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        # Fail-safe to avoid agent crash due to malformed file
        return []


def save_todos(todos):
    """
    Persist task list to disk.
    """
    try:
        with open(TODO_FILE, "w", encoding="utf-8") as f:
            json.dump(todos, f, indent=2)
    except PermissionError:
        print("Permission denied when writing todo.json")


def add_task(task):
    """
    Append new task to list.
    """
    todos = load_todos()
    todos.append({"task": task, "done": False})
    save_todos(todos)
    return f"Task '{task}' added."


def mark_done(index):
    """
    Mark task as completed by index.
    """
    todos = load_todos()
    if 0 <= index < len(todos):
        todos[index]["done"] = True
        save_todos(todos)
        return f"Task '{todos[index]['task']}' marked as done."
    return "Invalid task index."