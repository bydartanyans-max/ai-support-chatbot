import os
import sqlite3
from datetime import datetime, timezone
from functools import wraps

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from services.ai_provider import generate_reply

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.getenv("CHATBOT_DB", os.path.join(BASE_DIR, "chatbot.db"))

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-change-me")


def db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = db_connection()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'agent',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visitor_name TEXT NOT NULL DEFAULT 'Visitor',
            status TEXT NOT NULL DEFAULT 'open',
            source TEXT NOT NULL DEFAULT 'web',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            sender TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
        );
        """
    )

    columns = {row[1] for row in conn.execute("PRAGMA table_info(conversations)").fetchall()}
    if "source" not in columns:
        conn.execute("ALTER TABLE conversations ADD COLUMN source TEXT NOT NULL DEFAULT 'web'")

    existing = conn.execute("SELECT id FROM users WHERE email = ?", ("admin@demo.local",)).fetchone()
    if not existing:
        conn.execute(
            "INSERT INTO users (email, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
            (
                "admin@demo.local",
                generate_password_hash("demo1234"),
                "admin",
                now_iso(),
            ),
        )
    conn.commit()
    conn.close()


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def create_conversation_record(visitor_name="Visitor", source="web"):
    visitor_name = (visitor_name or "Visitor").strip()[:80] or "Visitor"
    source = (source or "web").strip()[:40] or "web"
    now = now_iso()
    conn = db_connection()
    cur = conn.execute(
        "INSERT INTO conversations (visitor_name, status, source, created_at, updated_at) VALUES (?, 'open', ?, ?, ?)",
        (visitor_name, source, now, now),
    )
    conversation_id = cur.lastrowid
    conn.commit()
    conn.close()
    return conversation_id, visitor_name, source


def process_message(conversation_id, message):
    conn = db_connection()
    conversation = conn.execute(
        "SELECT * FROM conversations WHERE id = ?", (conversation_id,)
    ).fetchone()
    if not conversation:
        conn.close()
        return None

    history = conn.execute(
        "SELECT sender, content FROM messages WHERE conversation_id = ? ORDER BY id DESC LIMIT 8",
        (conversation_id,),
    ).fetchall()
    history = [dict(row) for row in reversed(history)]

    created_at = now_iso()
    conn.execute(
        "INSERT INTO messages (conversation_id, sender, content, created_at) VALUES (?, 'user', ?, ?)",
        (conversation_id, message, created_at),
    )

    reply, provider = generate_reply(message, history)
    bot_created_at = now_iso()
    conn.execute(
        "INSERT INTO messages (conversation_id, sender, content, created_at) VALUES (?, 'assistant', ?, ?)",
        (conversation_id, reply, bot_created_at),
    )

    status = "needs_human" if any(
        phrase in reply.lower() for phrase in ["operator uman", "human agent", "prelua conversația"]
    ) else conversation["status"]

    conn.execute(
        "UPDATE conversations SET updated_at = ?, status = ? WHERE id = ?",
        (bot_created_at, status, conversation_id),
    )
    conn.commit()
    conn.close()

    return {
        "reply": reply,
        "provider": provider,
        "conversation_id": conversation_id,
        "timestamp": bot_created_at,
        "status": status,
    }


@app.get("/")
def home():
    return render_template("chat.html")


@app.post("/api/conversations")
def create_conversation():
    payload = request.get_json(silent=True) or {}
    conversation_id, visitor_name, source = create_conversation_record(
        payload.get("visitor_name"), payload.get("source", "web")
    )
    return jsonify(
        {
            "conversation_id": conversation_id,
            "visitor_name": visitor_name,
            "source": source,
        }
    ), 201


@app.get("/api/conversations/<int:conversation_id>/messages")
def conversation_messages(conversation_id):
    conn = db_connection()
    conversation = conn.execute(
        "SELECT * FROM conversations WHERE id = ?", (conversation_id,)
    ).fetchone()
    if not conversation:
        conn.close()
        return jsonify({"error": "conversation not found"}), 404

    messages = conn.execute(
        "SELECT sender, content, created_at FROM messages WHERE conversation_id = ? ORDER BY id",
        (conversation_id,),
    ).fetchall()
    conn.close()
    return jsonify(
        {
            "conversation": dict(conversation),
            "messages": [dict(row) for row in messages],
        }
    )


@app.post("/api/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    message = (payload.get("message") or "").strip()
    conversation_id = payload.get("conversation_id")

    if not message:
        return jsonify({"error": "message is required"}), 400
    if not isinstance(conversation_id, int):
        return jsonify({"error": "conversation_id is required"}), 400

    result = process_message(conversation_id, message)
    if result is None:
        return jsonify({"error": "conversation not found"}), 404
    return jsonify(result)


@app.post("/api/webhooks/incoming")
def incoming_webhook():
    expected_secret = os.getenv("WEBHOOK_SECRET")
    if expected_secret:
        provided_secret = request.headers.get("X-Webhook-Secret", "")
        if provided_secret != expected_secret:
            return jsonify({"error": "unauthorized webhook"}), 401

    payload = request.get_json(silent=True) or {}
    message = str(payload.get("message") or "").strip()
    visitor_name = str(payload.get("visitor_name") or payload.get("customer") or "Webhook Visitor")
    source = str(payload.get("source") or "webhook")
    conversation_id = payload.get("conversation_id")

    if not message:
        return jsonify({"error": "message is required"}), 400

    if conversation_id is None:
        conversation_id, _, _ = create_conversation_record(visitor_name, source)
    elif not isinstance(conversation_id, int):
        return jsonify({"error": "conversation_id must be an integer"}), 400

    result = process_message(conversation_id, message)
    if result is None:
        return jsonify({"error": "conversation not found"}), 404

    result["source"] = source
    return jsonify(result), 200


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        conn = db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["user_email"] = user["email"]
            session["role"] = user["role"]
            return redirect(url_for("dashboard"))
        flash("Email sau parolă incorectă.", "error")
    return render_template("login.html")


@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.get("/dashboard")
@login_required
def dashboard():
    conn = db_connection()
    conversations = conn.execute(
        """
        SELECT c.*,
               COUNT(m.id) AS message_count,
               MAX(m.created_at) AS last_message_at
        FROM conversations c
        LEFT JOIN messages m ON m.conversation_id = c.id
        GROUP BY c.id
        ORDER BY c.updated_at DESC
        """
    ).fetchall()
    total_messages = conn.execute("SELECT COUNT(*) AS c FROM messages").fetchone()["c"]
    open_conversations = conn.execute(
        "SELECT COUNT(*) AS c FROM conversations WHERE status = 'open'"
    ).fetchone()["c"]
    conn.close()
    return render_template(
        "dashboard.html",
        conversations=conversations,
        total_messages=total_messages,
        open_conversations=open_conversations,
    )


@app.get("/dashboard/conversations/<int:conversation_id>")
@login_required
def dashboard_conversation(conversation_id):
    conn = db_connection()
    conversation = conn.execute(
        "SELECT * FROM conversations WHERE id = ?", (conversation_id,)
    ).fetchone()
    messages = conn.execute(
        "SELECT * FROM messages WHERE conversation_id = ? ORDER BY id",
        (conversation_id,),
    ).fetchall()
    conn.close()
    if not conversation:
        return "Conversation not found", 404
    return render_template(
        "conversation.html", conversation=conversation, messages=messages
    )


@app.post("/dashboard/conversations/<int:conversation_id>/status")
@login_required
def set_status(conversation_id):
    status = request.form.get("status", "open")
    if status not in {"open", "closed", "needs_human"}:
        return "Invalid status", 400
    conn = db_connection()
    conn.execute(
        "UPDATE conversations SET status = ?, updated_at = ? WHERE id = ?",
        (status, now_iso(), conversation_id),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard_conversation", conversation_id=conversation_id))


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "ai-support-chatbot"})


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG") == "1")
