from flask import Flask, render_template, request, jsonify
import requests
import paramiko
import re
import os

app = Flask(__name__)

# ─── App Config ───────────────────────────────────────────────────────────────
APPS = [
    {"name": "Flipkart",  "url": "https://www.flipkart.com"},
    {"name": "Jenkins",   "url": "http://nambi@yourserver:8080"},
    {"name": "Tomcat",    "url": "http://nambi@yourserver:8080/manager"},
]

# ─── SSH Config ───────────────────────────────────────────────────────────────
SSH_SERVERS = {
    "jenkins": {
        "host": "yourserver",
        "user": "nambi",
        "key":  "/home/nambi/.ssh/id_rsa",
        "start_cmd":  "cd /opt/jenkins/bin && ./start.sh",
        "stop_cmd":   "cd /opt/jenkins/bin && ./stop.sh",
        "status_cmd": "cd /opt/jenkins/bin && ./status.sh",
    },
    "tomcat": {
        "host": "yourserver",
        "user": "nambi",
        "key":  "/home/nambi/.ssh/id_rsa",
        "start_cmd":  "cd /opt/tomcat/bin && ./startup.sh",
        "stop_cmd":   "cd /opt/tomcat/bin && ./shutdown.sh",
        "status_cmd": "cd /opt/tomcat/bin && ./status.sh",
    },
}

# ─── Routes ───────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/health")
def health():
    results = []
    for app_info in APPS:
        try:
            r = requests.get(app_info["url"], timeout=5)
            status = "UP" if r.status_code < 400 else "DOWN"
            code   = r.status_code
        except Exception as e:
            status = "DOWN"
            code   = str(e)[:60]
        results.append({"name": app_info["name"], "url": app_info["url"], "status": status, "code": code})
    return jsonify(results)

@app.route("/api/chat", methods=["POST"])
def chat():
    msg = request.json.get("message", "").lower().strip()

    # ── Identify app ──────────────────────────────────────────────────────────
    target = None
    for key in SSH_SERVERS:
        if key in msg:
            target = key
            break

    if not target:
        return jsonify({"reply": "I didn't catch which application you mean. Try: 'start jenkins' or 'status tomcat'."})

    # ── Identify action ───────────────────────────────────────────────────────
    if any(w in msg for w in ["start", "bring up", "restart"]):
        action = "start"
    elif any(w in msg for w in ["stop", "shut", "kill"]):
        action = "stop"
    elif any(w in msg for w in ["status", "check", "running", "up", "down", "health"]):
        action = "status"
    else:
        return jsonify({"reply": f"I found '{target}' but didn't understand the action. Try: start, stop, or status."})

    # ── SSH Execute ───────────────────────────────────────────────────────────
    server = SSH_SERVERS[target]
    cmd    = server[f"{action}_cmd"]

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=server["host"],
            username=server["user"],
            key_filename=server["key"],
            timeout=10
        )
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        client.close()

        output = out or err or "Command executed with no output."
        reply  = f"✅ Ran `{action}` on **{target}**:\n```\n{output}\n```"
    except Exception as e:
        reply = f"❌ SSH failed for {target}: {str(e)}"

    return jsonify({"reply": reply})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
