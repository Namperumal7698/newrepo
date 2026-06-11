import requests
import yaml
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'apps.yaml')

def load_apps():
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)['apps']

def check_url(url: str, timeout: int = 5) -> dict:
    try:
        r = requests.get(url, timeout=timeout, verify=False)
        status = "UP" if r.status_code < 400 else "DOWN"
        return {"status": status, "code": r.status_code}
    except requests.exceptions.ConnectionError:
        return {"status": "DOWN", "code": "Connection refused"}
    except requests.exceptions.Timeout:
        return {"status": "DOWN", "code": "Timeout"}
    except Exception as e:
        return {"status": "DOWN", "code": str(e)[:60]}

def get_all_health() -> list:
    apps = load_apps()
    results = []
    for app in apps:
        health = check_url(app['url'])
        results.append({
            "name":       app['name'],
            "url":        app['url'],
            "status":     health['status'],
            "code":       health['code'],
            "servers":    [s['label'] for s in app.get('servers', [])],
            "server_count": len(app.get('servers', []))
        })
    return results
