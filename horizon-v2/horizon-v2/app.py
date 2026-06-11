from flask import Flask, render_template, request, jsonify
from core.health_checker import get_all_health, load_apps
from core.ssh_handler import find_app, get_app_servers, run_action
import re

app = Flask(__name__)

# ── In-memory session state for chatbot multi-turn (per conversation) ─────────
# Stores pending action when bot is waiting for user to pick a server
pending = {}   # key: session_id → {app_name, action, servers}

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/health")
def health():
    try:
        results = get_all_health()
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/apps")
def apps_list():
    """Return app names for chatbot hint chips."""
    try:
        apps = load_apps()
        return jsonify([{"name": a["name"]} for a in apps])
    except Exception as e:
        return jsonify([])

@app.route("/api/chat", methods=["POST"])
def chat():
    data       = request.json
    msg        = data.get("message", "").strip()
    session_id = data.get("session_id", "default")
    msg_lower  = msg.lower()

    # ── Check if we're in a pending server-selection flow ──────────────────
    if session_id in pending:
        p = pending[session_id]

        # User picked a server by number or label
        # Check for number like "1", "2", "3"
        num_match = re.search(r'\b([1-9])\b', msg)
        chosen_server = None

        if num_match:
            idx = int(num_match.group(1)) - 1
            if 0 <= idx < len(p['servers']):
                chosen_server = p['servers'][idx]

        # Or user typed the server label/host directly
        if not chosen_server:
            for s in p['servers']:
                if s['label'].lower() in msg_lower or s['host'] in msg_lower:
                    chosen_server = s
                    break

        if not chosen_server:
            return jsonify({"reply": "Please pick a server by number (e.g. reply '1' or '2')."})

        # Clear pending and execute
        del pending[session_id]
        result = run_action(p['app_name'], p['action'], chosen_server['host'])
        return jsonify({"reply": format_result(result)})

    # ── Fresh message: identify app ────────────────────────────────────────
    target_app = None
    apps = load_apps()
    for a in apps:
        if a['name'].lower() in msg_lower:
            target_app = a['name']
            break

    if not target_app:
        return jsonify({"reply": (
            "I didn't catch which application you mean.\n"
            "Try: 'start Jenkins', 'status Tomcat', 'stop SonarQube'\n\n"
            "Available apps:\n" +
            "\n".join(f"• {a['name']}" for a in apps)
        )})

    # ── Identify action ────────────────────────────────────────────────────
    if any(w in msg_lower for w in ["start", "bring up", "restart", "launch"]):
        action = "start"
    elif any(w in msg_lower for w in ["stop", "shut", "kill", "down"]):
        action = "stop"
    elif any(w in msg_lower for w in ["status", "check", "running", "health", "up", "alive"]):
        action = "status"
    else:
        return jsonify({"reply": f"I found '{target_app}' but didn't understand the action.\nTry: start, stop, or status."})

    # ── Get servers for this app ───────────────────────────────────────────
    servers = get_app_servers(target_app)

    if not servers:
        return jsonify({"reply": f"No servers configured for {target_app}."})

    if len(servers) == 1:
        # Only one server — execute directly
        result = run_action(target_app, action, servers[0]['host'])
        return jsonify({"reply": format_result(result)})

    # Multiple servers — ask which one
    pending[session_id] = {
        "app_name": target_app,
        "action":   action,
        "servers":  servers
    }

    server_list = "\n".join(
        f"{i+1}. {s['label']}  ({s['host']})"
        for i, s in enumerate(servers)
    )
    return jsonify({
        "reply": (
            f"'{target_app}' has {len(servers)} servers. Which one should I run '{action}' on?\n\n"
            f"{server_list}\n\n"
            "Click a server below or reply with the number."
        ),
        "servers": servers   # sent to UI for clickable buttons
    })


def format_result(result: dict) -> str:
    icon = "✅" if result['success'] else "❌"
    lines = [
        f"{icon} {result['action'].upper()} on {result['app']} — {result['server']}",
        f"Command: {result.get('command', '')}",
        "---",
        result['output']
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
