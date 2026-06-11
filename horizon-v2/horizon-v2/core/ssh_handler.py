import paramiko
import yaml
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'apps.yaml')

def load_apps():
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)['apps']

def find_app(name: str) -> dict | None:
    """Find app config by name (case-insensitive, partial match)."""
    apps = load_apps()
    name_lower = name.lower()
    for app in apps:
        if name_lower in app['name'].lower():
            return app
    return None

def get_app_servers(app_name: str) -> list:
    """Return list of servers for an app — used by chatbot to ask which server."""
    app = find_app(app_name)
    if not app:
        return []
    return app.get('servers', [])

def ssh_exec(host: str, user: str, key_path: str, command: str) -> dict:
    """SSH into a server and run a command. Returns stdout, stderr, success flag."""
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=host,
            username=user,
            key_filename=key_path,
            timeout=15
        )
        stdin, stdout, stderr = client.exec_command(command, timeout=30)
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        exit_code = stdout.channel.recv_exit_status()
        client.close()

        return {
            "success": exit_code == 0,
            "output":  out or err or "(no output)",
            "exit_code": exit_code
        }
    except FileNotFoundError:
        return {"success": False, "output": f"SSH key not found: {key_path}", "exit_code": -1}
    except paramiko.AuthenticationException:
        return {"success": False, "output": "SSH authentication failed. Check key/user.", "exit_code": -1}
    except Exception as e:
        return {"success": False, "output": str(e), "exit_code": -1}

def run_action(app_name: str, action: str, server_host: str) -> dict:
    """
    Run start/stop/status on a specific server of an app.
    Returns result dict with success, output.
    """
    app = find_app(app_name)
    if not app:
        return {"success": False, "output": f"App '{app_name}' not found in config."}

    cmd = app['commands'].get(action)
    if not cmd:
        return {"success": False, "output": f"Action '{action}' not defined for {app_name}."}

    # Find the matching server label
    server_label = server_host
    for s in app.get('servers', []):
        if s['host'] == server_host or s['label'] == server_host:
            server_label = s['label']
            server_host  = s['host']
            break

    result = ssh_exec(
        host=server_host,
        user=app['ssh_user'],
        key_path=app['ssh_key'],
        command=cmd
    )
    result['server'] = server_label
    result['app']    = app['name']
    result['action'] = action
    result['command'] = cmd
    return result
