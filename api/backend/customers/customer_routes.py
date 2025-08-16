import mysql.connector as mysql
from flask import Blueprint, request, jsonify, current_app
from backend.db_connection import db
from mysql.connector import Error


# Blueprint setup
customer = Blueprint("customer", __name__, url_prefix="/customer")
customer.strict_slashes = False

def _get_conn():
    cfg = current_app.config
    return mysql.connect(
        host=cfg.get("MYSQL_DATABASE_HOST", "127.0.0.1"),
        port=int(cfg.get("MYSQL_DATABASE_PORT", 3306)),
        user=cfg.get("MYSQL_DATABASE_USER", "root"),
        password=cfg.get("MYSQL_DATABASE_PASSWORD", "changeme"),
        database=cfg.get("MYSQL_DATABASE_DB", "SpotLight"),
    )

@customer.route("/<int:c_id>", methods=["GET"])
def get_customer(c_id: int):
    try:
        cursor = db.get_db().cursor()
        cursor.execute(
            (
                "SELECT cID, fName, lName, email, position, companyName, totalOrderTimes, VIP, avatarURL, balance, TEL "
                "FROM Customers WHERE cID = %s"
            ),
            (c_id,),
        )
        row = cursor.fetchone()
        cursor.close()
        if not row:
            return jsonify({"error": "Customer not found"}), 404
        return jsonify(row), 200
    except Error as e:
        current_app.logger.error(f"get_customer error: {e}")
        return jsonify({"error": str(e)}), 500


@customer.route("/<int:c_id>", methods=["POST"])
def update_customer(c_id: int):
    try:
        payload = request.get_json(silent=True) or {}
        # Require all fields except id, as requested
        required_fields = [
            "fName",
            "lName",
            "email",
            "position",
            "companyName",
            "totalOrderTimes",
            "VIP",
            "avatarURL",
            "balance",
            "TEL",
        ]
        missing = [f for f in required_fields if f not in payload]
        if missing:
            return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

        cursor = db.get_db().cursor()
        query = (
            "UPDATE Customers SET fName=%s, lName=%s, email=%s, position=%s, companyName=%s, "
            "totalOrderTimes=%s, VIP=%s, avatarURL=%s, balance=%s, TEL=%s WHERE cID=%s"
        )
        data = (
            payload["fName"],
            payload["lName"],
            payload["email"],
            payload["position"],
            payload["companyName"],
            int(payload["totalOrderTimes"]),
            1 if bool(payload["VIP"]) else 0,
            payload["avatarURL"],
            int(payload["balance"]),
            payload["TEL"],
            c_id,
        )
        cursor.execute(query, data)
        db.get_db().commit()
        cursor.close()
        return jsonify({"message": "updated", "cID": c_id}), 200
    except Error as e:
        current_app.logger.error(f"update_customer error: {e}")
        return jsonify({"error": str(e)}), 500

@customer.delete("/<int:c_id>")
def delete_customer(c_id: int):
    """
    Delete a customer by cID.
    Returns: {"deleted": c_id, "rows_affected": N}
    """
    try:
        conn = _get_conn(); cur = conn.cursor()
        cur.execute("DELETE FROM Customers WHERE cID=%s", (c_id,))
        rows = cur.rowcount
        conn.commit()
        cur.close(); conn.close()
        return {"deleted": c_id, "rows_affected": rows}, 200
    except Exception as e:
        return {"error": str(e)}, 500

@customer.get("/")
def list_customers():
    """
    List customers (supports simple search with ?q=).
    """
    q = (request.args.get("q") or "").strip()
    try:
        conn = _get_conn(); cur = conn.cursor(dictionary=True)
        if q:
            like = f"%{q}%"
            cur.execute(
                """
                SELECT cID, fName, lName, email, TEL
                FROM Customers
                WHERE fName LIKE %s OR lName LIKE %s OR email LIKE %s
                ORDER BY cID DESC
                LIMIT 200
                """,
                (like, like, like),
            )
        else:
            cur.execute(
                "SELECT cID, fName, lName, email, TEL FROM Customers ORDER BY cID DESC LIMIT 200"
            )
        rows = cur.fetchall()
        cur.close(); conn.close()
        return rows, 200
    except Exception as e:
        return {"error": str(e)}, 500

@customer.get("/<int:c_id>/orders")
def list_customer_orders(c_id: int):
    """
    List recent orders for a specific customer.
    """
    try:
        conn = _get_conn(); cur = conn.cursor(dictionary=True)
        # Minimal, schema-safe selection
        cur.execute(
            """
            SELECT o.*
            FROM Orders o
            WHERE o.cID = %s
            ORDER BY o.orderID DESC
            LIMIT 100
            """,
            (c_id,),
        )
        rows = cur.fetchall()
        cur.close(); conn.close()
        return rows, 200
    except Exception as e:
        return {"error": str(e)}, 500
