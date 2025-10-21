from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime
import os
from database import init_db, get_db
##########
# app.py 頂部修改（確保 redirect 和 url_for 在這裡）
from flask import Flask, render_template, request, jsonify, redirect, url_for
# ... 其他導入
##########

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SESSION_SECRET", "your-secret-key-here")
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

init_db()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/waiter")
def waiter():
    return render_template("waiter.html")


@app.route("/kitchen")
def kitchen():
    return render_template("kitchen.html")


# @app.route("/api/menu", methods=["GET"])
# def get_menu():
#     conn = get_db()
#     cursor = conn.cursor()
#     cursor.execute(
#         "SELECT * FROM menu_items WHERE available = 1 ORDER BY category, name"
#     )
#     items = cursor.fetchall()
#     conn.close()

#     menu = []
#     for item in items:
#         menu.append(
#             {
#                 "id": item["id"],
#                 "name": item["name"],
#                 "price": item["price"],
#                 "description": item["description"],
#                 "category": item["category"],
#             }
#         )

#     return jsonify(menu)


@app.route("/api/orders", methods=["GET"])
def get_orders():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders ORDER BY created_at DESC")
    orders = cursor.fetchall()
    conn.close()

    order_list = []
    for order in orders:
        order_list.append(
            {
                "id": order["id"],
                "order_number": order["order_number"],
                "items": json.loads(order["items"]),
                "total_amount": order["total_amount"],
                "status": order["status"],
                "notes": order["notes"],
                "created_at": order["created_at"],
                "updated_at": order["updated_at"],
            }
        )

    return jsonify(order_list)


@app.route("/api/orders/pending", methods=["GET"])
def get_pending_orders():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM orders WHERE status != 'completed' ORDER BY created_at ASC"
    )
    orders = cursor.fetchall()
    conn.close()

    order_list = []
    for order in orders:
        order_list.append(
            {
                "id": order["id"],
                "order_number": order["order_number"],
                "items": json.loads(order["items"]),
                "total_amount": order["total_amount"],
                "status": order["status"],
                "notes": order["notes"],
                "created_at": order["created_at"],
                "updated_at": order["updated_at"],
            }
        )

    return jsonify(order_list)


@app.route("/api/orders", methods=["POST"])
def create_order():
    data = request.json
    items = data.get("items", [])
    total_amount = data.get("total_amount", 0)
    notes = data.get("notes", "")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as count FROM orders")
    count = cursor.fetchone()["count"]
    order_number = f"ORD{datetime.now().strftime('%Y%m%d')}{count + 1:04d}"

    cursor.execute(
        "INSERT INTO orders (order_number, items, total_amount, status, notes) VALUES (?, ?, ?, ?, ?)",
        (order_number, json.dumps(items), total_amount, "pending", notes),
    )

    order_id = cursor.lastrowid
    conn.commit()
    conn.close()

    order_data = {
        "id": order_id,
        "order_number": order_number,
        "items": items,
        "total_amount": total_amount,
        "status": "pending",
        "notes": notes,
        "created_at": datetime.now().isoformat(),
    }

    socketio.emit("new_order", order_data)

    return jsonify(order_data), 201


@app.route("/api/orders/<int:order_id>/status", methods=["PUT"])
def update_order_status(order_id):
    data = request.json
    new_status = data.get("status")

    if new_status not in ["pending", "received", "cooking", "ready", "completed"]:
        return jsonify({"error": "Invalid status"}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE orders SET status = ?, updated_at = ? WHERE id = ?",
        (new_status, datetime.now().isoformat(), order_id),
    )

    conn.commit()

    cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    order = cursor.fetchone()
    conn.close()

    if order:
        order_data = {
            "id": order["id"],
            "order_number": order["order_number"],
            "items": json.loads(order["items"]),
            "total_amount": order["total_amount"],
            "status": order["status"],
            "notes": order["notes"],
            "created_at": order["created_at"],
            "updated_at": order["updated_at"],
        }

        socketio.emit("order_updated", order_data)

        return jsonify(order_data)

    return jsonify({"error": "Order not found"}), 404
    
##################
# --- 菜單管理路由 ---
@app.route("/admin", methods=["GET", "POST"])
def admin_menu():
    conn = get_db()
    
    if request.method == "POST":
        action = request.form.get("action")
        
        if action == "add_or_update":
            # 從表單獲取數據
            category = request.form["category"]
            name = request.form["name"]
            price = float(request.form["price"])
            description = request.form["description"]
            item_id = request.form.get("item_id")
            
            # 處理可用性（預設為 1，即可用）
            available = 1 
            
            if item_id:
                # 修改現有項目
                conn.execute(
                    "UPDATE menu_items SET category=?, name=?, price=?, description=?, available=? WHERE id=?",
                    (category, name, price, description, available, item_id)
                )
            else:
                # 新增項目
                conn.execute(
                    "INSERT INTO menu_items (category, name, price, description, available) VALUES (?, ?, ?, ?, ?)",
                    (category, name, price, description, available)
                )
            
        elif action == "delete":
            # 刪除項目
            item_id = request.form["item_id"]
            conn.execute("DELETE FROM menu_items WHERE id=?", (item_id,))

        conn.commit()
        conn.close()
        
        # 處理完畢後，重導向回管理頁面
        return redirect(url_for("admin_menu"))
    
    # GET 請求：顯示所有菜單
    cursor = conn.cursor()
    cursor.execute("SELECT id, category, name, price, description, available FROM menu_items ORDER BY category, id")
    menu_items = cursor.fetchall()
    conn.close()
    
    return render_template("admin.html", menu_items=menu_items)

# --- 修正 API 路由，以包含新的 category 和 description ---
@app.route("/api/menu", methods=["GET"])
def get_menu():
    conn = get_db()
    cursor = conn.cursor()
    # 確保這裡的欄位順序和 SELECT 語句一致
    cursor.execute(
        "SELECT id, name, price, description, category FROM menu_items WHERE available = 1 ORDER BY category, name"
    )
    items = cursor.fetchall()
    conn.close()

    menu = []
    for item in items:
        # 使用 dict 語法來匹配您的資料庫行
        menu.append(
            {
                "id": item["id"],
                "name": item["name"],
                "price": item["price"],
                "description": item["description"],
                "category": item["category"],
            }
        )
    return jsonify(menu)
#############



@socketio.on("connect")
def handle_connect():
    print("Client connected")
    emit("connected", {"data": "Connected to server"})


@socketio.on("disconnect")
def handle_disconnect():
    print("Client disconnected")


# if __name__ == '__main__':
#     socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
import os

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    # 先讀 PORT 環境變數；沒有就用 5000
    port = int(os.getenv("PORT", "5000"))

    # 如果你有裝 eventlet，Socket.IO 會更穩
    try:
        import eventlet  # noqa: F401

        use_eventlet = True
    except Exception:
        use_eventlet = False

    # 讓開發階段不被 Werkzeug 安全警告卡住
    socketio.run(app, host=host, port=port, debug=True, allow_unsafe_werkzeug=True)
