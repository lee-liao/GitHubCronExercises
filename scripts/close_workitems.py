#!/usr/bin/env python3
"""
Close ADO work items for today from README.md table.

Reads Active rows for today's date, closes them in Azure DevOps,
then updates README.md with Closed status.

Required env vars: ADO_PAT
Optional env vars: ADO_ORG, ADO_PROJECT, ADO_API_VER (have defaults)
"""

import os, sys, json, base64, datetime
import urllib.request, urllib.error

ORG     = os.environ.get("ADO_ORG", "cubeforest3003")
PROJECT = os.environ.get("ADO_PROJECT", "powerBI-demo")
API_VER = os.environ.get("ADO_API_VER", "7.1")

COLS = ['date', 'type', 'title', 'description', 'assigned_to', 'status', 'id', 'parent_id']


# ── ADO helpers ───────────────────────────────────────────────────────────────

def _auth(pat):
    return "Basic " + base64.b64encode(f":{pat}".encode()).decode()

def _call(method, url, pat, body=None):
    data = json.dumps(body).encode() if body else None
    req  = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": _auth(pat),
        "Content-Type":  "application/json-patch+json",
    })
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read())

def _base():
    return f"https://dev.azure.com/{ORG}/{PROJECT}/_apis/wit/workitems"

def close_item(item_id, pat):
    url = f"{_base()}/{item_id}?api-version={API_VER}"
    resp = _call("PATCH", url, pat,
                 [{"op": "add", "path": "/fields/System.State", "value": "Closed"}])
    return resp.get("fields", {}).get("System.State", "unknown")


# ── README table helpers ──────────────────────────────────────────────────────

def parse_table(content):
    rows, seen_header, seen_sep = [], False, False
    for line in content.split('\n'):
        s = line.strip()
        if not (s.startswith('|') and s.endswith('|')):
            if rows:
                break
            continue
        cells = [c.strip() for c in s.split('|')[1:-1]]
        if not seen_header:
            seen_header = True
            continue
        if not seen_sep:
            seen_sep = True
            continue
        if len(cells) >= len(COLS):
            rows.append(dict(zip(COLS, cells)))
    return rows

def update_row_status(content, item_id, new_status):
    out = []
    for line in content.split('\n'):
        if line.startswith('|') and line.endswith('|'):
            parts = line.split('|')
            if len(parts) >= 9 and parts[-3].strip() == str(item_id):
                parts[-4] = f' {new_status} '
                line = '|'.join(parts)
        out.append(line)
    return '\n'.join(out)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    pat = os.environ.get("ADO_PAT")
    if not pat:
        sys.exit("ERROR: ADO_PAT environment variable is required.")

    today = datetime.date.today().isoformat()
    print(f"Closing active work items for {today}...")

    with open("README.md") as f:
        content = f.read()

    active = [r for r in parse_table(content)
              if r['date'] == today and r['status'].lower() == 'active']

    if not active:
        print(f"No active items for {today}. Nothing to do.")
        return

    print(f"Found {len(active)} active item(s) for {today}.")

    for item in active:
        item_id = item['id']
        if not item_id:
            print(f"  Skipping {item['type']} '{item['title']}' — no ID.")
            continue
        print(f"  Closing {item['type']} ID {item_id}: {item['title']}...")
        final_state = close_item(item_id, pat)
        print(f"  → {final_state}")
        content = update_row_status(content, item_id, final_state)

    with open("README.md", 'w') as f:
        f.write(content)
    print("\nREADME.md updated.")


if __name__ == '__main__':
    main()
