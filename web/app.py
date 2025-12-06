"""
from flask import Flask, render_template, url_for
import os, time

app = Flask(__name__)
RADAR_PATH = os.path.join(app.static_folder, "radar")

@app.route("/")
def index():
    regions = []
    ts = int(time.time())  # timestamp for cache-busting
    for file in os.listdir(RADAR_PATH):
        if file.endswith(".gif"):
            region_name = file.split(".")[0]
            url = url_for("static", filename=f"radar/{file}") + f"?t={ts}"
            regions.append((region_name, url))
    return render_template("index.html", regions=regions)
"""
from flask import Flask, render_template, url_for
import os, time

app = Flask(__name__)
RADAR_PATH = os.path.join(app.static_folder, "radar")


@app.route("/")
def index():
    regions = []
    ts = int(time.time())  # timestamp for cache-busting
    order = ["Midwest", "Great Lakes", "East"]  # desired display order

    # build a dict mapping region_name -> url
    region_map = {}
    for file in os.listdir(RADAR_PATH):
        if file.endswith(".gif"):
            region_name = file.split(".")[0]
            url = url_for("static", filename=f"radar/{file}") + f"?t={ts}"
            region_map[region_name] = url

    # sort by your fixed order, skip missing
    for name in order:
        if name in region_map:
            regions.append((name, region_map[name]))

    return render_template("index.html", regions=regions)
