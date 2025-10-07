from flask import Flask, render_template, request, redirect, url_for, session, Response, flash
import os, requests

app = Flask(__name__)
app.secret_key = "dev-secret-change-me"

AUTH = os.environ.get("AUTH_URL", "http://auth-service:5000")
FILE = os.environ.get("FILE_URL", "http://file-service:5000")
VIDEO = os.environ.get("VIDEO_URL", "http://video-service:5000")

# ---------- Web UI -----------

@app.route("/")
def index():
    if "username" in session:
        return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    u = request.form.get("username"); p = request.form.get("password")
    if not u or not p:
        flash("Missing credentials"); return redirect(url_for("index"))
    r = requests.post(f"{AUTH}/auth", json={"username":u,"password":p})
    if r.status_code == 200:
        session['username'] = u
        session['password'] = p  # kept to let gateway call video-service for listing/deletes (demo only)
        session['is_admin'] = r.json().get("is_admin", False)
        return redirect(url_for("dashboard"))
    flash("Login failed"); return redirect(url_for("index"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("index"))
    # request list from video-service
    try:
        resp = requests.post(f"{VIDEO}/videos", json={"username": session['username'], "password": session['password']})
        if resp.status_code != 200:
            flash("Failed to fetch videos"); videos=[]
        else:
            videos = resp.json()
    except Exception:
        videos = []
    return render_template("dashboard.html", username=session['username'], is_admin=session.get('is_admin',False), videos=videos)

@app.route("/upload", methods=["POST"])
def upload():
    if "username" not in session:
        return redirect(url_for("index"))
    f = request.files.get("file")
    if not f or f.filename == "":
        flash("No file selected"); return redirect(url_for("dashboard"))

    # POST to file-service
    files = {"file": (f.filename, f.read())}
    data = {"username": session['username']}
    resp = requests.post(f"{FILE}/upload", files=files, data=data)
    if resp.status_code not in (200,201):
        flash("File upload failed: " + resp.text); return redirect(url_for("dashboard"))
    info = resp.json()
    path = info.get("path")
    name = info.get("filename")

    # Register in video-service
    add = requests.post(f"{VIDEO}/add-video", json={"name": name, "path": path, "owner": session['username']})
    if add.status_code not in (200,201):
        flash("Failed to register video"); return redirect(url_for("dashboard"))

    flash("Uploaded")
    return redirect(url_for("dashboard"))

@app.route("/delete/<int:video_id>", methods=["POST"])
def delete(video_id):
    if "username" not in session:
        return redirect(url_for("index"))

    # 1️⃣ First, ask video-service for file path & delete DB record
    payload = {"video_id": video_id, "username": session['username'], "password": session['password']}
    vr = requests.post(f"{VIDEO}/delete-video", json=payload)
    if vr.status_code != 200:
        flash("Delete failed: " + vr.text)
        return redirect(url_for("dashboard"))

    # video-service should return JSON with path info
    try:
        info = vr.json()
        video_path = info.get("path")
    except Exception:
        video_path = None

    # 2️⃣ If we got a file path, tell file-service to delete it
    if video_path:
        fr = requests.post(f"{FILE}/delete", json={"path": video_path})
        if fr.status_code != 200:
            flash("DB entry deleted but file delete failed: " + fr.text)
            return redirect(url_for("dashboard"))

    flash("Deleted")
    return redirect(url_for("dashboard"))


@app.route("/create-user", methods=["POST"])
def create_user():
    if "username" not in session or not session.get('is_admin'):
        flash("Admin only"); return redirect(url_for("dashboard"))
    new_user = request.form.get("new_user"); new_pass = request.form.get("new_pass"); admin_pass_confirm = request.form.get("admin_pass_confirm")
    if not all([new_user, new_pass, admin_pass_confirm]):
        flash("Missing fields"); return redirect(url_for("dashboard"))
    r = requests.post(f"{AUTH}/create-user", json={
        "admin_user": session['username'],
        "admin_pass": admin_pass_confirm,
        "username": new_user,
        "password": new_pass
    })
    if r.status_code == 201:
        flash("User created")
    else:
        flash("Failed to create user: " + r.text)
    return redirect(url_for("dashboard"))


@app.route("/delete-user", methods=["POST"])
def delete_user():
    if "username" not in session or not session.get('is_admin'):
        flash("Admin only"); return redirect(url_for("dashboard"))

    delete_user = request.form.get("delete_user")
    admin_pass_confirm = request.form.get("admin_pass_confirm")

    if not all([delete_user, admin_pass_confirm]):
        flash("Missing fields"); return redirect(url_for("dashboard"))

    r = requests.post(f"{AUTH}/delete-user", json={
        "admin_user": session['username'],
        "admin_pass": admin_pass_confirm,
        "username": delete_user
    })

    if r.status_code == 200:
        flash(f"User '{delete_user}' deleted")
    else:
        flash("Failed to delete user: " + r.text)
    return redirect(url_for("dashboard"))


@app.route("/stream/<path:subpath>")
def stream(subpath):
    # subpath like username/filename
    # proxy to video-service which proxies file-service
    downstream = f"{VIDEO}/stream/{subpath}"
    r = requests.get(downstream, stream=True)
    if r.status_code != 200:
        return ("not found", 404)
    headers = {"Content-Type": r.headers.get("Content-Type","application/octet-stream")}
    return Response(r.iter_content(chunk_size=1024*64), headers=headers)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
