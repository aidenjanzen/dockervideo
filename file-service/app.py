from flask import Flask, request, jsonify, send_from_directory
import os

app = Flask(__name__)
BASE = "/data/videos"
os.makedirs(BASE, exist_ok=True)

VIDEO_FOLDER = os.environ.get("VIDEO_FOLDER", "/data/videos")

@app.route("/upload", methods=["POST"])
def upload():
    # requires form-data: file + username
    if "file" not in request.files or "username" not in request.form:
        return jsonify({"error":"missing file or username"}), 400
    f = request.files["file"]
    username = request.form["username"]
    userdir = os.path.join(BASE, username)
    os.makedirs(userdir, exist_ok=True)
    path = os.path.join(userdir, f.filename)
    f.save(path)
    # return relative path used in DB (username/filename)
    return jsonify({"path": f"{username}/{f.filename}", "filename": f.filename}), 201

@app.route("/delete", methods=["POST"])
def delete_file():
    data = request.json or {}
    path = data.get("path")
    if not path:
        return jsonify({"error": "Missing path"}), 400

    file_path = os.path.join(VIDEO_FOLDER, path)
    print(f"[DELETE DEBUG] Path received: {path}")
    print(f"[DELETE DEBUG] Full file_path: {file_path}", flush=True)

    if not os.path.exists(file_path):
        print(f"[DELETE DEBUG] File not found on disk: {file_path}", flush=True)
        return jsonify({"error": "File not found"}), 404

    try:
        os.remove(file_path)
        print(f"[DELETE DEBUG] File deleted: {file_path}", flush=True)
        return jsonify({"deleted": True}), 200
    except Exception as e:
        print(f"[DELETE DEBUG] Error deleting file: {e}", flush=True)
        return jsonify({"error": str(e)}), 500

@app.route("/videos/<path:subpath>", methods=["GET"])
def serve_video(subpath):
    # subpath = username/filename
    file_path = os.path.join(BASE, subpath)
    if not os.path.exists(file_path):
        print(f"[STREAM DEBUG] File not found at {file_path}", flush=True)
        return "File not found", 404

    directory = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    return send_from_directory(directory, filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
