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


# ------------------------------------------------------------
# Spot-related routes under the same blueprint (prefixed with /customer)


def _valid_spot_status(value: str) -> bool:
    return value in ("free", "inuse", "w.issue", "planned")


@customer.route("/spots", methods=["GET"])
def list_spots():
    try:
        cursor = db.get_db().cursor()
        cursor.execute(
            (
                "SELECT spotID, price, contactTel, estViewPerMonth, monthlyRentCost, "
                "endTimeOfCurrentOrder, status, address, longitude, latitude "
                "FROM Spot ORDER BY spotID DESC"
            )
        )
        data = cursor.fetchall()
        cursor.close()
        return jsonify(data), 200
    except Error as e:
        current_app.logger.error(f"list_spots error: {e}")
        return jsonify({"error": str(e)}), 500


@customer.route("/spots", methods=["POST"])
def create_spot():
    try:
        payload = request.get_json(silent=True) or {}
        required = [
            "price",
            "contactTel",
            "estViewPerMonth",
            "monthlyRentCost",
            "endTimeOfCurrentOrder",
            "status",
            "address",
            "longitude",
            "latitude",
        ]
        missing = [f for f in required if f not in payload]
        if missing:
            return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
        if not _valid_spot_status(payload["status"]):
            return jsonify({"error": "Invalid status"}), 400

        cursor = db.get_db().cursor()
        cursor.execute(
            (
                "INSERT INTO Spot (price, contactTel, estViewPerMonth, monthlyRentCost, endTimeOfCurrentOrder, "
                "status, address, longitude, latitude) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
            ),
            (
                payload["price"],
                payload["contactTel"],
                payload["estViewPerMonth"],
                payload["monthlyRentCost"],
                payload["endTimeOfCurrentOrder"],
                payload["status"],
                payload["address"],
                payload["longitude"],
                payload["latitude"],
            ),
        )
        db.get_db().commit()
        new_id = cursor.lastrowid
        cursor.close()
        return jsonify({"message": "created", "spotID": new_id}), 201
    except Error as e:
        current_app.logger.error(f"create_spot error: {e}")
        return jsonify({"error": str(e)}), 500


@customer.route("/spots/<int:spot_id>", methods=["GET"])
def get_spot(spot_id: int):
    try:
        cursor = db.get_db().cursor()
        cursor.execute(
            (
                "SELECT spotID, price, contactTel, estViewPerMonth, monthlyRentCost, "
                "endTimeOfCurrentOrder, status, address, longitude, latitude "
                "FROM Spot WHERE spotID = %s"
            ),
            (spot_id,),
        )
        row = cursor.fetchone()
        cursor.close()
        if not row:
            return jsonify({"error": "Spot not found"}), 404
        return jsonify(row), 200
    except Error as e:
        current_app.logger.error(f"get_spot error: {e}")
        return jsonify({"error": str(e)}), 500


@customer.route("/spots/<int:spot_id>", methods=["POST"])
def create_spot_with_id(spot_id: int):
    try:
        payload = request.get_json(silent=True) or {}
        required = [
            "price",
            "contactTel",
            "estViewPerMonth",
            "monthlyRentCost",
            "endTimeOfCurrentOrder",
            "status",
            "address",
            "longitude",
            "latitude",
        ]
        missing = [f for f in required if f not in payload]
        if missing:
            return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
        if not _valid_spot_status(payload["status"]):
            return jsonify({"error": "Invalid status"}), 400

        cursor = db.get_db().cursor()
        cursor.execute(
            (
                "INSERT INTO Spot (spotID, price, contactTel, estViewPerMonth, monthlyRentCost, endTimeOfCurrentOrder, "
                "status, address, longitude, latitude) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            ),
            (
                spot_id,
                payload["price"],
                payload["contactTel"],
                payload["estViewPerMonth"],
                payload["monthlyRentCost"],
                payload["endTimeOfCurrentOrder"],
                payload["status"],
                payload["address"],
                payload["longitude"],
                payload["latitude"],
            ),
        )
        db.get_db().commit()
        cursor.close()
        return jsonify({"message": "created", "spotID": spot_id}), 201
    except Error as e:
        current_app.logger.error(f"create_spot_with_id error: {e}")
        return jsonify({"error": str(e)}), 500


@customer.route("/spots/<int:spot_id>", methods=["PUT"])
def update_spot(spot_id: int):
    try:
        payload = request.get_json(silent=True) or {}
        required = [
            "price",
            "contactTel",
            "estViewPerMonth",
            "monthlyRentCost",
            "endTimeOfCurrentOrder",
            "status",
            "address",
            "longitude",
            "latitude",
        ]
        missing = [f for f in required if f not in payload]
        if missing:
            return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
        if not _valid_spot_status(payload["status"]):
            return jsonify({"error": "Invalid status"}), 400

        cursor = db.get_db().cursor()
        cursor.execute(
            (
                "UPDATE Spot SET price=%s, contactTel=%s, estViewPerMonth=%s, monthlyRentCost=%s, "
                "endTimeOfCurrentOrder=%s, status=%s, address=%s, longitude=%s, latitude=%s WHERE spotID=%s"
            ),
            (
                payload["price"],
                payload["contactTel"],
                payload["estViewPerMonth"],
                payload["monthlyRentCost"],
                payload["endTimeOfCurrentOrder"],
                payload["status"],
                payload["address"],
                payload["longitude"],
                payload["latitude"],
                spot_id,
            ),
        )
        db.get_db().commit()
        cursor.close()
        return jsonify({"message": "updated", "spotID": spot_id}), 200
    except Error as e:
        current_app.logger.error(f"update_spot error: {e}")
        return jsonify({"error": str(e)}), 500


@customer.route("/spots/<int:spot_id>", methods=["DELETE"])
def delete_spot(spot_id: int):
    try:
        cursor = db.get_db().cursor()
        cursor.execute("DELETE FROM Spot WHERE spotID = %s", (spot_id,))
        db.get_db().commit()
        cursor.close()
        return jsonify({"message": "deleted", "spotID": spot_id}), 200
    except Error as e:
        current_app.logger.error(f"delete_spot error: {e}")
        return jsonify({"error": str(e)}), 500
