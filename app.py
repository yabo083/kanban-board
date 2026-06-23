#!/usr/bin/env python3
"""看板系统 — Flask backend + JSON file storage"""

import json
import os
import uuid
from datetime import datetime, timezone, timedelta
from functools import wraps

from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder="static")

# ─── Config (可通过环境变量覆盖) ───────────────────────
DATA_FILE = os.environ.get("KANBAN_DATA_FILE", os.path.join(os.path.dirname(__file__), "data", "tasks.json"))
ARCHIVE_DIR = os.path.join(os.path.dirname(DATA_FILE), "archive")
TZ = timezone(timedelta(hours=8))

os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
os.makedirs(ARCHIVE_DIR, exist_ok=True)


def load_tasks():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        tasks = json.load(f)
    # Migrate: ensure every task has 'archived' field
    changed = False
    for t in tasks:
        if "archived" not in t:
            t["archived"] = False
            changed = True
    if changed:
        save_tasks(tasks)
    return tasks


def save_tasks(tasks):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)


def now_str():
    return datetime.now(TZ).strftime("%Y-%m-%d %H:%M")


# ─── API ───────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/tasks", methods=["GET"])
def get_tasks():
    tasks = load_tasks()
    # By default return non-archived; ?archived=true returns only archived
    show_archived = request.args.get("archived", "false").lower() == "true"
    return jsonify([t for t in tasks if t.get("archived", False) == show_archived])


@app.route("/api/tasks", methods=["POST"])
def create_task():
    data = request.json
    task = {
        "id": uuid.uuid4().hex[:8],
        "title": data.get("title", "").strip(),
        "description": data.get("description", "").strip(),
        "status": data.get("status", "todo"),
        "priority": data.get("priority", "normal"),
        "created_at": now_str(),
        "updated_at": now_str(),
        "completed_at": None,
        "archived": False,
        "notes": [],
    }
    if not task["title"]:
        return jsonify({"error": "title required"}), 400
    tasks = load_tasks()
    tasks.insert(0, task)
    save_tasks(tasks)
    return jsonify(task), 201


@app.route("/api/tasks/<task_id>", methods=["PATCH"])
def update_task(task_id):
    data = request.json
    tasks = load_tasks()
    for t in tasks:
        if t["id"] == task_id:
            for key in ("title", "description", "status", "priority"):
                if key in data:
                    t[key] = data[key]
            if data.get("status") == "done" and not t.get("completed_at"):
                t["completed_at"] = now_str()
            if data.get("status") in ("todo", "doing"):
                t["completed_at"] = None
            if "note" in data and data["note"]:
                t["notes"].append({"text": data["note"], "time": now_str()})
            t["updated_at"] = now_str()
            save_tasks(tasks)
            return jsonify(t)
    return jsonify({"error": "not found"}), 404


@app.route("/api/tasks/<task_id>", methods=["DELETE"])
def delete_task(task_id):
    tasks = load_tasks()
    tasks = [t for t in tasks if t["id"] != task_id]
    save_tasks(tasks)
    return jsonify({"ok": True})


@app.route("/api/tasks/<task_id>/archive", methods=["POST"])
def archive_task(task_id):
    tasks = load_tasks()
    for t in tasks:
        if t["id"] == task_id:
            t["archived"] = True
            t["updated_at"] = now_str()
            save_tasks(tasks)
            return jsonify(t)
    return jsonify({"error": "not found"}), 404


@app.route("/api/tasks/<task_id>/unarchive", methods=["POST"])
def unarchive_task(task_id):
    tasks = load_tasks()
    for t in tasks:
        if t["id"] == task_id:
            t["archived"] = False
            t["updated_at"] = now_str()
            save_tasks(tasks)
            return jsonify(t)
    return jsonify({"error": "not found"}), 404


@app.route("/api/archive/batch", methods=["POST"])
def batch_archive_done():
    """Archive all done tasks. Called by weekly cron."""
    tasks = load_tasks()
    count = 0
    for t in tasks:
        if t.get("status") == "done" and not t.get("archived", False):
            t["archived"] = True
            t["updated_at"] = now_str()
            count += 1
    save_tasks(tasks)
    return jsonify({"archived": count})


@app.route("/api/stats", methods=["GET"])
def stats():
    tasks = load_tasks()
    active = [t for t in tasks if not t.get("archived", False)]
    total = len(active)
    by_status = {}
    for t in active:
        s = t.get("status", "todo")
        by_status[s] = by_status.get(s, 0) + 1
    archived = len([t for t in tasks if t.get("archived", False)])
    return jsonify({"total": total, "by_status": by_status, "archived": archived})


if __name__ == "__main__":
    port = int(os.environ.get("KANBAN_PORT", "8888"))
    app.run(host="0.0.0.0", port=port)
