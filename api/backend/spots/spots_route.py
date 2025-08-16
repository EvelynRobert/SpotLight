from flask import Blueprint, request, jsonify, current_app
from backend.db_connection import db
from mysql.connector import Error


spots = Blueprint("spots", __name__)


def _valid_spot_status(value: str) -> bool:
    return value in ("free", "inuse", "w.issue", "planned")


@spots.route("/", methods=["GET"])
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


@spots.route("/", methods=["POST"])
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


@spots.route("/<int:spot_id>", methods=["GET"])
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


@spots.route("/<int:spot_id>", methods=["POST"])
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


@spots.route("/<int:spot_id>", methods=["PUT"])
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


@spots.route("/<int:spot_id>", methods=["DELETE"])
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


@spots.route("/near", methods=["GET"])
def find_spots_near():
    try:
        lat_str = request.args.get("lat")
        lng_str = request.args.get("lng")
        radius_str = request.args.get("radius_km")
        status = request.args.get("status")

        if not lat_str or not lng_str or not radius_str:
            return jsonify({"error": "Missing required query params: lat, lng, radius_km"}), 400
        try:
            lat = float(lat_str)
            lng = float(lng_str)
            radius_km = float(radius_str)
        except ValueError:
            return jsonify({"error": "lat, lng, and radius_km must be numeric"}), 400

        if status and not _valid_spot_status(status):
            return jsonify({"error": "Invalid status"}), 400

        cursor = db.get_db().cursor()
        params = [lat, lng, lat]
        query = (
            "SELECT spotID, price, contactTel, estViewPerMonth, monthlyRentCost, "
            "endTimeOfCurrentOrder, status, address, longitude, latitude, "
            "(6371 * acos( cos(radians(%s)) * cos(radians(latitude)) * "
            "cos(radians(longitude) - radians(%s)) + sin(radians(%s)) * sin(radians(latitude)) )) AS distance_km "
            "FROM Spot WHERE latitude IS NOT NULL AND longitude IS NOT NULL "
        )
        if status:
            query += "AND status = %s "
            params.append(status)
        query += "HAVING distance_km <= %s ORDER BY distance_km ASC LIMIT 100"
        params.append(radius_km)

        cursor.execute(query, tuple(params))
        data = cursor.fetchall()
        cursor.close()
        return jsonify(data), 200
    except Error as e:
        current_app.logger.error(f"find_spots_near error: {e}")
        return jsonify({"error": str(e)}), 500


@spots.route("/<int:spot_id>/status/<status>", methods=["POST"])
def change_spot_status(spot_id: int, status: str):
    try:
        if not _valid_spot_status(status):
            return jsonify({"error": "Invalid status"}), 400
        cursor = db.get_db().cursor()
        cursor.execute("UPDATE Spot SET status = %s WHERE spotID = %s", (status, spot_id))
        db.get_db().commit()
        cursor.close()
        return jsonify({"message": "updated", "spotID": spot_id, "status": status}), 200
    except Error as e:
        current_app.logger.error(f"change_spot_status error: {e}")
        return jsonify({"error": str(e)}), 500


@spots.route("/search", methods=["GET"])
def search_spots():
    try:
        key_word = (request.args.get("key_word") or "").strip()
        top_n_raw = (request.args.get("top_n") or "10").strip()
        if not key_word:
            return jsonify({"error": "Missing key_word"}), 400
        try:
            top_n = int(top_n_raw)
        except Exception:
            return jsonify({"error": "top_n must be an integer"}), 400
        # Clamp to a sane range
        top_n = max(1, min(top_n, 200))

        cursor = db.get_db().cursor()
        query = (
            "SELECT spotID, price, contactTel, estViewPerMonth, monthlyRentCost, "
            "endTimeOfCurrentOrder, status, address, longitude, latitude "
            "FROM Spot WHERE MATCH(address) AGAINST (%s IN NATURAL LANGUAGE MODE) "
            "LIMIT %s"
        )
        cursor.execute(query, (key_word, top_n))
        data = cursor.fetchall()  # if no rows, this will be []
        cursor.close()
        return jsonify(data), 200
    except Error as e:
        current_app.logger.error(f"search_spots error: {e}")
        return jsonify({"error": str(e)}), 500
