import json, pathlib
from flask import Flask, render_template
from datetime import datetime

DATA = pathlib.Path("data_log.jsonl")
app  = Flask(__name__)

def last_n(n=10):
    if not DATA.exists():
        return [], [], [], [], [], [], []

    lines = DATA.read_text().splitlines()
    recs = [json.loads(l) for l in lines]

    system_recs = [r for r in recs if r.get("type") == "system"][-n:]
    service_recs = [r for r in recs if r.get("type") == "service"]

    timestamps = [r["ts"] for r in system_recs]
    req_counts = [r["req"] for r in system_recs]
    uptimes = [r["upt"] for r in system_recs]
    mem_values = [r["memGB"] for r in system_recs]
    crashes = [r["crashes"] for r in system_recs]

    # latest status per service (use a dict to keep only latest IP/status)
    service_status = {}
    for r in service_recs:
        label = f'{r["service"]} ({r["ip"]})'
        service_status[label] = 1 if r["status"].lower() == "in service" else 0

    service_labels = list(service_status.keys())
    service_values = list(service_status.values())

    return timestamps, req_counts, uptimes, mem_values, crashes, service_labels, service_values

@app.route("/")
def home():
    timestamps, reqs, upts, mems, crashes, service_labels, service_values = last_n(10)

    formatted_timestamps = [
        datetime.fromisoformat(ts).strftime("%d %b %H:%M")
        for ts in timestamps
    ]

    return render_template("dashboard.html",
                           timestamps=formatted_timestamps,
                           request_counts=reqs,
                           uptime_seconds_list=upts,
                           memory_values=mems,
                           crash_counts=crashes,
                           service_labels=service_labels,
                           service_status_values=service_values)

if __name__ == "__main__":
    app.run(debug=True)