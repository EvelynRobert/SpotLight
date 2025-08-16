from flask import Blueprint, request, jsonify, current_app
from backend.db_connection import db
from mysql.connector import Error


customer = Blueprint("customer", __name__)


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


