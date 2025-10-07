from flask import Flask, request, jsonify, Response
import os, requests, mysql.connector

app = Flask(__name__)

AUTH_URL = os.environ.get("AUTH_URL", "http://auth-service:5000")
FILE_URL = os.environ.get("FILE_URL", "http://file-service:5000")

DB_CONF = {
    "host": os.environ.get("MYSQL_HOST", "db"),
    "user": os.environ.get("MYSQL_USER", "root"),
    "password": os.environ.get("MYSQL_PASSWORD", "root"),
    "database": os.environ.get("MYSQL_DB", "videos")
}

def db():
    return mysql.connector.connect(**DB_CONF)

@app.route("/videos", methods=["POST"])
def list_videos():
    # Expects JSON: {username, password}
    data = request.json or {}
    username = data.get("username"); password = data.get("password")
    if not username or not password:
        return jsonify({"error":"missing"}), 400

    auth = requests.post(f"{AUTH_URL}/auth", json={"username":username,"password":password})
    if auth.status_code != 200:
        return jsonify({"error":"auth failed"}), 401
    is_admin = auth.json().get("is_admin", False)

    conn = db()
    cur = conn.cursor()
    if is_admin:
        cur.execute("SELECT id,name,path,owner FROM videos")
    else:
        cur.execute("SELECT id,name,path,owner FROM videos WHERE owner=%s", (username,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    videos = [{"id":r[0],"name":r[1],"path":r[2],"owner":r[3]} for r in rows]
    return jsonify(videos)

@app.route("/add-video", methods=["POST"])
def add_video():
    # Expects JSON: {name, path, owner}
    data = request.json or {}
    name = data.get("name"); path = data.get("path"); owner = data.get("owner")
    if not all([name, path, owner]):
        return jsonify({"error":"missing"}), 400
    conn = db()
    cur = conn.cursor()
    cur.execute("INSERT INTO videos (name,path,owner) VALUES (%s,%s,%s)", (name, path, owner))
    conn.commit()
    cur.close(); conn.close()
    return jsonify({"added": True}), 201

@app.route("/delete-video", methods=["POST"])
def delete_video():
    # Expects JSON: {video_id, username, password}
    data = request.json or {}
    video_id = data.get("video_id")
    username = data.get("username")
    password = data.get("password")

    if not all([video_id, username, password]):
        return jsonify({"error": "missing"}), 400

    # 🔐 Authenticate user
    auth = requests.post(f"{AUTH_URL}/auth", json={"username": username, "password": password})
    if auth.status_code != 200:
        return jsonify({"error": "auth failed"}), 401
    is_admin = auth.json().get("is_admin", False)

    conn = db()
    cur = conn.cursor()
    # Get video path + owner
    cur.execute("SELECT path, owner FROM videos WHERE id=%s", (video_id,))
    row = cur.fetchone()
    if not row:
        cur.close(); conn.close()
        return jsonify({"error": "not found"}), 404

    path, owner = row
    # Check ownership or admin
    if owner != username and not is_admin:
        cur.close(); conn.close()
        return jsonify({"error": "forbidden"}), 403

    # Delete from DB
    cur.execute("DELETE FROM videos WHERE id=%s", (video_id,))
    conn.commit()
    cur.close(); conn.close()

    # ✅ Return file path so gateway can tell file-service to delete it too
    return jsonify({"deleted": True, "path": path}), 200


@app.route("/stream/<path:subpath>", methods=["GET"])
def stream(subpath):
    # subpath = username/filename
    downstream = f"{FILE_URL}/videos/{subpath}"
    r = requests.get(downstream, stream=True)
    if r.status_code != 200:
        return ("not found", 404)
    # Stream response back with same content-type
    headers = {"Content-Type": r.headers.get("Content-Type","application/octet-stream")}
    return Response(r.iter_content(chunk_size=1024*64), headers=headers)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
