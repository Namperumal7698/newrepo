# Horizon — App Health & Command Center

Two-tab web app: URL health dashboard + SSH chatbot.

## Setup (on your central Linux server only)

```bash
# 1. Install Python packages
pip3 install -r requirements.txt

# 2. Edit app.py — update APPS and SSH_SERVERS with your real values
vi app.py

# 3. Run Flask
python3 app.py
# Runs on port 5000

# 4. Access in browser
http://your-server:5000
```

## Configure your apps in app.py

### APPS (URL health check):
```python
APPS = [
    {"name": "Jenkins",  "url": "http://your-jenkins-server:8080"},
    {"name": "Flipkart", "url": "https://www.flipkart.com"},
]
```

### SSH_SERVERS (chatbot commands):
```python
SSH_SERVERS = {
    "jenkins": {
        "host": "192.168.1.10",
        "user": "nambi",
        "key":  "/home/nambi/.ssh/id_rsa",
        "start_cmd":  "cd /opt/jenkins/bin && ./start.sh",
        "stop_cmd":   "cd /opt/jenkins/bin && ./stop.sh",
        "status_cmd": "cd /opt/jenkins/bin && ./status.sh",
    },
}
```

## Chatbot usage examples
- "start jenkins"
- "jenkins is down, please bring it up"
- "status tomcat"
- "stop jenkins"
- "is tomcat running?"

## Serve via Apache (optional)
Use mod_proxy to forward Apache → Flask:
```
ProxyPass /horizon http://localhost:5000
ProxyPassReverse /horizon http://localhost:5000
```

## Files
- app.py          → Flask backend (URL check + SSH logic)
- templates/index.html → Two-tab UI
- requirements.txt → Python dependencies
