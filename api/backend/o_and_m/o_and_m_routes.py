from flask import Blueprint, request, jsonify, current_app
from backend.db_connection import db
from mysql.connector import Error
from datetime import datetime, timedelta


o_and_m = Blueprint("o_and_m", __name__)


def _parse_period_days(period_param: str, default_days: int = 90) -> int:
    if not period_param:
        return default_days
    try:
        # supports formats like "90d"
        if period_param.endswith("d"):
            return int(period_param[:-1])
        return int(period_param)
    except Exception:
        return default_days


@o_and_m.route("/search", methods=["GET"])
def full_db_search():
    try:
        q = request.args.get("query", "").strip()
        if not q:
            return jsonify({"spots": [], "customers": [], "orders": []}), 200

        cursor = db.get_db().cursor()

        # Spots: use FULLTEXT on address when possible, also fallback to LIKE
        spots = []
        try:
            cursor.execute(
                (
                    "SELECT spotID, address, status, price, estViewPerMonth, monthlyRentCost "
                    "FROM Spot WHERE MATCH(address) AGAINST (%s IN NATURAL LANGUAGE MODE) "
                    "OR address LIKE %s LIMIT 20"
                ),
                (q, f"%{q}%"),
            )
            spots = cursor.fetchall()
        except Error:
            # In case MATCH is unsupported in current mode
            cursor.execute(
                (
                    "SELECT spotID, address, status, price, estViewPerMonth, monthlyRentCost "
                    "FROM Spot WHERE address LIKE %s LIMIT 20"
                ),
                (f"%{q}%",),
            )
            spots = cursor.fetchall()

        # Customers: search by name/email/company
        cursor.execute(
            (
                "SELECT cID, fName, lName, email, companyName, VIP "
                "FROM Customers "
                "WHERE fName LIKE %s OR lName LIKE %s OR email LIKE %s OR companyName LIKE %s "
                "LIMIT 20"
            ),
            (f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%"),
        )
        customers = cursor.fetchall()

        # Orders: if numeric, try exact match on orderID or cID; else search by date string
        orders = []
        if q.isdigit():
            cursor.execute(
                (
                    "SELECT orderID, date, total, cID "
                    "FROM Orders WHERE orderID = %s OR cID = %s LIMIT 20"
                ),
                (int(q), int(q)),
            )
            orders = cursor.fetchall()
        else:
            cursor.execute(
                (
                    "SELECT orderID, date, total, cID "
                    "FROM Orders WHERE DATE_FORMAT(date, '%Y-%m-%d') LIKE %s LIMIT 20"
                ),
                (f"%{q}%",),
            )
            orders = cursor.fetchall()

        cursor.close()
        return jsonify({"spots": spots, "customers": customers, "orders": orders}), 200
    except Error as e:
        current_app.logger.error(f"full_db_search error: {e}")
        return jsonify({"error": str(e)}), 500


@o_and_m.route("/insert", methods=["POST"])
def insert_data():
    try:
        payload = request.get_json(silent=True) or {}
        entity = (payload.get("entity") or "").strip().lower()
        if not entity:
            return jsonify({"error": "Missing entity"}), 400

        cursor = db.get_db().cursor()

        if entity == "spot":
            required = ["price", "contactTel", "address"]
            for f in required:
                if f not in payload:
                    return jsonify({"error": f"Missing field: {f}"}), 400
            status = payload.get("status", "free")
            if status not in ("free", "inuse", "w.issue", "planned"):
                return jsonify({"error": "Invalid status"}), 400
            cursor.execute(
                (
                    "INSERT INTO Spot (price, contactTel, imageURL, estViewPerMonth, monthlyRentCost, "
                    "endTimeOfCurrentOrder, status, address, latitude, longitude) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                ),
                (
                    payload["price"],
                    payload["contactTel"],
                    payload.get("imageURL"),
                    payload.get("estViewPerMonth"),
                    payload.get("monthlyRentCost"),
                    payload.get("endTimeOfCurrentOrder"),
                    status,
                    payload["address"],
                    payload.get("latitude"),
                    payload.get("longitude"),
                ),
            )
            db.get_db().commit()
            new_id = cursor.lastrowid
            cursor.close()
            return jsonify({"message": "created", "spotID": new_id}), 201

        if entity == "customer":
            required = ["fName", "lName", "email"]
            for f in required:
                if f not in payload:
                    return jsonify({"error": f"Missing field: {f}"}), 400
            cursor.execute(
                (
                    "INSERT INTO Customers (fName, lName, email, position, companyName, totalOrderTimes, VIP, avatarURL, balance, TEL) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                ),
                (
                    payload["fName"],
                    payload["lName"],
                    payload["email"],
                    payload.get("position"),
                    payload.get("companyName"),
                    payload.get("totalOrderTimes", 0),
                    bool(payload.get("VIP", False)),
                    payload.get("avatarURL"),
                    payload.get("balance", 0),
                    payload.get("TEL"),
                ),
            )
            db.get_db().commit()
            new_id = cursor.lastrowid
            cursor.close()
            return jsonify({"message": "created", "cID": new_id}), 201

        if entity == "order":
            required = ["date", "total", "cID"]
            for f in required:
                if f not in payload:
                    return jsonify({"error": f"Missing field: {f}"}), 400
            cursor.execute(
                "INSERT INTO Orders (date, total, cID) VALUES (%s, %s, %s)",
                (payload["date"], payload["total"], payload["cID"]),
            )
            db.get_db().commit()
            new_id = cursor.lastrowid
            cursor.close()
            return jsonify({"message": "created", "orderID": new_id}), 201

        cursor.close()
        return jsonify({"error": "Unsupported entity. Use one of: spot, customer, order"}), 400
    except Error as e:
        current_app.logger.error(f"insert_data error: {e}")
        return jsonify({"error": str(e)}), 500


@o_and_m.route("/spot/<int:spot_id>", methods=["DELETE"])
def delete_spot(spot_id: int):
    try:
        cursor = db.get_db().cursor()
        cursor.execute("DELETE FROM Spot WHERE spotID = %s", (spot_id,))
        db.get_db().commit()
        cursor.close()
        return jsonify({"message": "deleted", "spotID": spot_id}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@o_and_m.route("/customer/<int:c_id>", methods=["DELETE"])
def delete_customer(c_id: int):
    try:
        cursor = db.get_db().cursor()
        cursor.execute("DELETE FROM Customers WHERE cID = %s", (c_id,))
        db.get_db().commit()
        cursor.close()
        return jsonify({"message": "deleted", "cID": c_id}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@o_and_m.route("/order/<int:order_id>", methods=["DELETE"])
def delete_order(order_id: int):
    try:
        cursor = db.get_db().cursor()
        cursor.execute("DELETE FROM Orders WHERE orderID = %s", (order_id,))
        db.get_db().commit()
        cursor.close()
        return jsonify({"message": "deleted", "orderID": order_id}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@o_and_m.route("/spots/metrics", methods=["GET"])
def get_spots_metrics():
    try:
        cursor = db.get_db().cursor()
        cursor.execute("SELECT COUNT(*) AS total FROM Spot")
        total = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS cnt FROM Spot WHERE status = 'inuse'")
        in_use = cursor.fetchone()["cnt"]

        cursor.execute("SELECT COUNT(*) AS cnt FROM Spot WHERE status = 'free'")
        free = cursor.fetchone()["cnt"]

        cursor.execute("SELECT COUNT(*) AS cnt FROM Spot WHERE status = 'w.issue'")
        with_issue = cursor.fetchone()["cnt"]

        cursor.close()
        return jsonify({
            "total": total,
            "in_use": in_use,
            "free": free,
            "with_issue": with_issue,
        }), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@o_and_m.route("/customers/metrics", methods=["GET"])
def get_customers_metrics():
    try:
        cursor = db.get_db().cursor()
        cursor.execute("SELECT COUNT(*) AS total FROM Customers")
        total = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS vip FROM Customers WHERE VIP = 1")
        vip = cursor.fetchone()["vip"]

        cursor.execute(
            (
                "SELECT COUNT(*) AS never_ordered FROM Customers c "
                "LEFT JOIN Orders o ON o.cID = c.cID WHERE o.orderID IS NULL"
            )
        )
        never_ordered = cursor.fetchone()["never_ordered"]

        # Average days since last order across customers having at least 1 order
        cursor.execute(
            (
                "SELECT AVG(days_since) AS avg_days FROM ("
                "  SELECT DATEDIFF(CURDATE(), MAX(o.date)) AS days_since"
                "  FROM Orders o GROUP BY o.cID"
                ") t"
            )
        )
        row = cursor.fetchone()
        avg_order_time = row["avg_days"] if row and row["avg_days"] is not None else 0

        cursor.close()
        return jsonify({
            "total": total,
            "vip": vip,
            "never_ordered": never_ordered,
            "avg_order_time": avg_order_time,
        }), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@o_and_m.route("/orders/metrics", methods=["GET"])
def get_orders_metrics():
    try:
        period_param = request.args.get("period", "90d")
        days = _parse_period_days(period_param, 90)

        cursor = db.get_db().cursor()

        cursor.execute("SELECT COUNT(*) AS total FROM Orders")
        total = cursor.fetchone()["total"]

        cursor.execute("SELECT AVG(total) AS avg_price FROM Orders")
        avg_price = cursor.fetchone()["avg_price"]

        cursor.execute(
            "SELECT COUNT(*) AS last_period FROM Orders WHERE date >= (CURDATE() - INTERVAL %s DAY)",
            (days,),
        )
        last_period = cursor.fetchone()["last_period"]

        cursor.close()
        return jsonify({
            "total": total,
            "avg_price": avg_price,
            "last_period": last_period,
        }), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@o_and_m.route("/spots/summary", methods=["GET"])
def spots_summary():
    try:
        limit = int(request.args.get("limit", 10))
        cursor = db.get_db().cursor()
        cursor.execute(
            (
                "SELECT spotID, address, status, price, estViewPerMonth, monthlyRentCost "
                "FROM Spot ORDER BY spotID DESC LIMIT %s"
            ),
            (limit,),
        )
        data = cursor.fetchall()
        cursor.close()
        return jsonify(data), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@o_and_m.route("/customers/summary", methods=["GET"])
def customers_summary():
    try:
        limit = int(request.args.get("limit", 10))
        cursor = db.get_db().cursor()
        cursor.execute(
            (
                "SELECT cID, fName, lName, email, companyName, VIP, totalOrderTimes "
                "FROM Customers ORDER BY cID DESC LIMIT %s"
            ),
            (limit,),
        )
        data = cursor.fetchall()
        cursor.close()
        return jsonify(data), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@o_and_m.route("/orders/summary", methods=["GET"])
def orders_summary():
    try:
        period_param = request.args.get("period", "90d")
        days = _parse_period_days(period_param, 90)
        limit = int(request.args.get("limit", 10))

        cursor = db.get_db().cursor()
        cursor.execute(
            (
                "SELECT orderID, date, total, cID "
                "FROM Orders WHERE date >= (CURDATE() - INTERVAL %s DAY) "
                "ORDER BY date DESC, orderID DESC LIMIT %s"
            ),
            (days, limit),
        )
        data = cursor.fetchall()
        cursor.close()
        return jsonify(data), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@o_and_m.route("/spots/<int:spot_id>/status", methods=["PUT"])
def update_spot_status(spot_id: int):
    try:
        payload = request.get_json(silent=True) or {}
        status = payload.get("status")
        if status not in ("free", "inuse", "w.issue", "planned"):
            return jsonify({"error": "Invalid status"}), 400
        cursor = db.get_db().cursor()
        cursor.execute("UPDATE Spot SET status = %s WHERE spotID = %s", (status, spot_id))
        db.get_db().commit()
        cursor.close()
        return jsonify({"message": "updated", "spotID": spot_id, "status": status}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@o_and_m.route("/reports/<int:r_id>", methods=["DELETE"])
def delete_report(r_id: int):
    try:
        cursor = db.get_db().cursor()
        cursor.execute("DELETE FROM Report WHERE rID = %s", (r_id,))
        db.get_db().commit()
        cursor.close()
        return jsonify({"message": "deleted", "rID": r_id}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@o_and_m.route("/reports/<int:r_id>/status", methods=["PUT"])
def update_report_status(r_id: int):
    try:
        payload = request.get_json(silent=True) or {}
        status = payload.get("status")
        # According to schema, valid values: 'unexamined', 'examined'
        if status not in ("unexamined", "examined"):
            return jsonify({"error": "Invalid status. Allowed: unexamined, examined"}), 400
        cursor = db.get_db().cursor()
        cursor.execute("UPDATE Report SET status = %s WHERE rID = %s", (status, r_id))
        db.get_db().commit()
        cursor.close()
        return jsonify({"message": "updated", "rID": r_id, "status": status}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
