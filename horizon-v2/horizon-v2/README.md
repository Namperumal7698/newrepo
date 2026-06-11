# Horizon v2 — App Health & Command Center

## Folder Structure
```
horizon-v2/
├── app.py                  ← Flask entry point
├── requirements.txt        ← pip dependencies
├── config/
│   └── apps.yaml           ← ALL your apps go here (20+ supported)
├── core/
│   ├── health_checker.py   ← URL health check logic
│   └── ssh_handler.py      ← SSH command execution via Paramiko
└── templates/
    └── index.html          ← Two-tab UI (health + chatbot)
```

## Setup (on your central Linux server only)

```bash
# 1. Install dependencies
pip3 install -r requirements.txt

# 2. Edit config/apps.yaml with your real apps
vi config/apps.yaml

# 3. Run
python3 app.py
# Access at http://yourserver:5000
```

## Adding apps to config/apps.yaml

```yaml
- name: MyApp
  url: http://myapp.internal:8080
  ssh_user: svc_myapp          # service account
  ssh_key: /home/nambi/.ssh/id_rsa
  servers:
    - host: 192.168.10.5
      label: MyApp-Server1
    - host: 192.168.10.6
      label: MyApp-Server2
  commands:
    start:  "cd /opt/myapp/bin && ./start.sh"
    stop:   "cd /opt/myapp/bin && ./stop.sh"
    status: "cd /opt/myapp/bin && ./status.sh"
```

## Chatbot usage
- "start jenkins"        → if 1 server: runs directly. if multiple: asks which one
- "status tomcat"        → checks status on selected server
- "stop sonarqube"       → stops on selected server
- Server selection: click the button shown, or type the number (1, 2, 3...)

## Destination servers
No packages needed on destination servers.
Only requirement: SSH key-based access from central server to destination servers.

## Apache proxy (optional)
```apache
ProxyPass /horizon http://localhost:5000
ProxyPassReverse /horizon http://localhost:5000
```
