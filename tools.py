from duckduckgo_search import DDGS
from todo import add_task, mark_done, load_todos
from datetime import datetime
import difflib

# Supported tool actions (used for model instruction)
VALID_ACTIONS = ["search", "add_todo", "complete_todo", "date", "none"]


def internet_search(query):
    """
    Lightweight internet search wrapper using DuckDuckGo.
    Appends contextual keywords to improve relevance for smaller models.
    """
    try:
        query = query + " explanation meaning context"

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=6))

        if not results:
            return "No relevant results found."

        formatted = []
        for r in results:
            if len(r.get("body", "")) > 40:
                formatted.append(f"{r.get('title')}\n{r.get('body')}")

        return "\n\n---\n\n".join(formatted[:3])
    except Exception as e:
        return f"Search failed: {str(e)}"


def add_todo(task):
    """
    Prevent duplicate tasks via case-insensitive comparison.
    """
    todos = load_todos()
    cleaned = task.strip().lower()

    for t in todos:
        if cleaned == t["task"].strip().lower():
            return "Task already exists."

    return add_task(task)


def complete_todo(task_text):
    """
    Fuzzy match task text and mark best candidate as done.
    """
    todos = load_todos()

    if not todos:
        return "There are no tasks to complete."

    best_match = None
    best_score = 0

    for i, t in enumerate(todos):
        if not t["done"]:
            score = difflib.SequenceMatcher(
                None, task_text.lower(), t["task"].lower()
            ).ratio()
            if score > best_score:
                best_score = score
                best_match = i

    if best_match is not None and best_score > 0.45:
        return mark_done(best_match)

    return "No matching task found."


def get_current_date():
    """
    Return formatted current system date.
    """
    return datetime.now().strftime("%A, %B %d, %Y")