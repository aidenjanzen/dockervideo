from flask import Flask, request, jsonify
import os
import mysql.connector

app = Flask(__name__)

def db():
    return mysql.connector.connect(
        host=os.environ.get("MYSQL_HOST", "db"),
        user=os.environ.get("MYSQL_USER", "root"),
        password=os.environ.get("MYSQL_PASSWORD", "root"),
        database=os.environ.get("MYSQL_DB", "videos"),
        autocommit=True
    )

@app.route("/auth", methods=["POST"])
def auth():
    data = request.json or {}
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"error":"missing"}), 400
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT password, is_admin FROM users WHERE username=%s", (username,))
    row = cur.fetchone()
    cur.close(); conn.close()
    if row and row[0] == password:
        return jsonify({"authenticated": True, "is_admin": bool(row[1])})
    return jsonify({"authenticated": False}), 401

@app.route("/create-user", methods=["POST"])
def create_user():
    data = request.json or {}
    admin_user = data.get("admin_user")
    admin_pass = data.get("admin_pass")
    new_user = data.get("username")
    new_pass = data.get("password")
    if not all([admin_user, admin_pass, new_user, new_pass]):
        return jsonify({"error":"missing"}), 400

    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT password, is_admin FROM users WHERE username=%s", (admin_user,))
    row = cur.fetchone()
    if not (row and row[0] == admin_pass and row[1] == 1):
        cur.close(); conn.close()
        return jsonify({"error":"admin auth failed"}), 401
    try:
        cur.execute("INSERT INTO users (username,password,is_admin) VALUES (%s,%s,0)", (new_user, new_pass))
    except Exception as e:
        cur.close(); conn.close()
        return jsonify({"error": str(e)}), 400
    cur.close(); conn.close()
    return jsonify({"created": True}), 201

@app.route("/delete-user", methods=["POST"])
def delete_user():
    data = request.json or {}
    admin_user = data.get("admin_user")
    admin_pass = data.get("admin_pass")
    username = data.get("username")

    if not all([admin_user, admin_pass, username]):
        return jsonify({"error": "Missing fields"}), 400

    # ✅ Verify admin credentials
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT password, is_admin FROM users WHERE username=%s", (admin_user,))
    row = cur.fetchone()
    if not row:
        cur.close(); conn.close()
        return jsonify({"error": "Admin user not found"}), 404
    stored_pass, is_admin = row
    if stored_pass != admin_pass or not is_admin:
        cur.close(); conn.close()
        return jsonify({"error": "Unauthorized"}), 403

    # 🚨 Don't let admin delete themselves
    if username == admin_user:
        cur.close(); conn.close()
        return jsonify({"error": "Cannot delete yourself"}), 400

    # 🗑️ Delete target user
    cur.execute("DELETE FROM users WHERE username=%s", (username,))
    conn.commit()
    cur.close(); conn.close()

    return jsonify({"deleted": True}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
