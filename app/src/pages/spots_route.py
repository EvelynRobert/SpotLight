# spots_route

from flask import Blueprint, request, jsonify, current_app
from backend.db_connection import db
from mysql.connector import Error


spots = Blueprint("spots", __name__)

VALID_STATUSES = {"free", "inuse", "planned", "w.issue"}

# ------------------------- helpers -------------------------

def _valid_status(s: str) -> bool:
    return s in VALID_STATUSES

def _add_where(sql_parts, params, clause, *vals):
    sql_parts.append(clause)
    params.extend(vals)

# ------------------------- routes --------------------------

@spots.route("/", methods=["GET"])
def list_spots():
    """
    Optional query params:
      status=free,inuse,planned,w.issue
      bbox=minLon,minLat,maxLon,maxLat
      q=<address contains>
      sort=spotID|price|views|status  order=asc|desc
      limit=<1..1000>  offset=<0..>
    """
    try:
        params = []
        where = ["1=1"]

        # status filter
        status_str = request.args.get("status", "").strip()
        if status_str:
            statuses = [s.strip() for s in status_str.split(",") if s.strip()]
            where.append("status IN (" + ",".join(["%s"] * len(statuses)) + ")")
            params += statuses

        # bbox filter: minLon,minLat,maxLon,maxLat
        bbox = request.args.get("bbox", "").strip()
        if bbox:
            try:
                min_lon, min_lat, max_lon, max_lat = map(float, bbox.split(","))
            except Exception:
                return jsonify(
                    {"error": "bbox must be 'minLon,minLat,maxLon,maxLat'"}), 
            400
            where.append
            ("longitude BETWEEN %s AND %s AND latitude BETWEEN %s AND %s")
            params += [min_lon, max_lon, min_lat, max_lat]

        # address contains
        q = request.args.get("q", "").strip() or request.args.get
        ("key_word", "").strip()
        if q:
            where.append("address LIKE %s")
            params.append(f"%{q}%")

        sort_map = {"spotID": "spotID", "price": "price", "views": 
                    "estViewPerMonth", "status": "status"}
        sort = sort_map.get(request.args.get("sort", "spotID"), "spotID")
        order = "DESC" if request.args.get("order", "asc").lower() == "desc" else "ASC"

        try:
            limit = max(1, min(1000, int(request.args.get("limit", "300"))))
            offset = max(0, int(request.args.get("offset", "0")))
        except ValueError:
            return jsonify({"error": "limit/offset must be integers"}), 400

        sql = (
            "SELECT spotID, price, contactTel, estViewPerMonth, monthlyRentCost, "
            "endTimeOfCurrentOrder, status, address, longitude, latitude, imageURL "
            "FROM Spot WHERE " + " AND ".join(where) + 
            f" ORDER BY {sort} {order} LIMIT %s OFFSET %s"
        )
        params += [limit, offset]

        cursor = db.get_db().cursor()
        cursor.execute(sql, tuple(params))
        data = cursor.fetchall()
        cursor.close()
        return jsonify(data), 200

    except Error as e:
        current_app.logger.error(f"list_spots error: {e}")
        return jsonify({"error": str(e)}), 500


@spots.route("/<int:spot_id>", methods=["GET"])
def get_spot(spot_id: int):
    try:
        cursor = db.get_db().cursor()
        cursor.execute(
            (
                "SELECT spotID, price, contactTel, estViewPerMonth, monthlyRentCost, "
                "endTimeOfCurrentOrder, status, address, longitude, latitude, imageURL "
                "FROM Spot WHERE spotID = %s"
            ),
            (spot_id,),
        )
        row = cursor.fetchone()
        cursor.close()
        if not row:
            return jsonify({"error": "not found"}), 404
        return jsonify(row), 200
    except Error as e:
        current_app.logger.error(f"get_spot error: {e}")
        return jsonify({"error": str(e)}), 500


@spots.route("/<int:spot_id>/status/<status>", methods=["POST"])
def change_status_path(spot_id: int, status: str):
    """Alternative style used by some pages: POST /spots/{id}/status/{status}"""
    try:
        if not _valid_status(status):
            return jsonify({"error": "Invalid status"}), 400
        cursor = db.get_db().cursor()
        cursor.execute("UPDATE Spot SET status=%s WHERE spotID=%s", 
                       (status, spot_id))
        db.get_db().commit()
        cursor.close()
        return jsonify({"ok": True, "spotID": spot_id, "status": status}), 200
    except Error as e:
        current_app.logger.error(f"change_status_path error: {e}")
        return jsonify({"error": str(e)}), 500


@spots.route("/<int:spot_id>/status", methods=["PUT"])
def change_status_body(spot_id: int):
    """PUT /spots/{id}/status with JSON: {"status": "..."}"""
    try:
        payload = request.get_json(silent=True) or {}
        status = payload.get("status")
        if not _valid_status(status):
            return jsonify({"error": "Invalid status"}), 400
        cursor = db.get_db().cursor()
        cursor.execute("UPDATE Spot SET status=%s WHERE spotID=%s", 
                       (status, spot_id))
        db.get_db().commit()
        cursor.close()
        return jsonify({"ok": True, "spotID": spot_id, "status": status}), 200
    except Error as e:
        current_app.logger.error(f"change_status_body error: {e}")
        return jsonify({"error": str(e)}), 500


@spots.route("/<int:spot_id>", methods=["PUT"])
def update_spot(spot_id: int):
    """
    Updatable fields:
      price, contactTel, estViewPerMonth, monthlyRentCost, 
      endTimeOfCurrentOrder,
      status, address, longitude, latitude, imageURL
    """
    try:
        payload = request.get_json(silent=True) or {}
        if not payload:
            return jsonify({"error": "empty body"}), 400

        # Build dynamic SET
        allowed = {
            "price","contactTel","estViewPerMonth","monthlyRentCost",
            "endTimeOfCurrentOrder",
            "status","address","longitude","latitude","imageURL"
        }
        keys = [k for k in payload.keys() if k in allowed]
        if not keys:
            return jsonify({"error": "no editable fields provided"}), 400
        if "status" in keys and not _valid_status(payload.get("status")):
            return jsonify({"error": "Invalid status"}), 400

        sets = ", ".join(f"{k}=%s" for k in keys)
        values = [payload[k] for k in keys] + [spot_id]

        cursor = db.get_db().cursor()
        cursor.execute(f"UPDATE Spot SET {sets} WHERE spotID=%s", 
                       tuple(values))
        db.get_db().commit()
        cursor.close()

        return jsonify({"ok": True, "spotID": spot_id}), 200

    except Error as e:
        current_app.logger.error(f"update_spot error: {e}")
        return jsonify({"error": str(e)}), 500


@spots.route("/", methods=["POST"])
def create_spot():
    """
    Required fields:
      price, contactTel, estViewPerMonth, monthlyRentCost, 
      endTimeOfCurrentOrder,
      status, address, longitude, latitude
    """
    try:
        payload = request.get_json(silent=True) or {}
        required = [
            "price","contactTel","estViewPerMonth","monthlyRentCost",
            "endTimeOfCurrentOrder",
            "status","address","longitude","latitude"
        ]
        missing = [f for f in required if f not in payload]
        if missing:
            return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
        if not _valid_status(payload["status"]):
            return jsonify({"error": "Invalid status"}), 400

        cursor = db.get_db().cursor()
        cursor.execute(
            (
                "INSERT INTO Spot (price, contactTel, estViewPerMonth, monthlyRentCost," 
                "endTimeOfCurrentOrder, status, address, longitude,  "
                "latitude, imageURL) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            ),
            (
                payload["price"], payload["contactTel"], 
                payload["estViewPerMonth"], payload["monthlyRentCost"],
                payload["endTimeOfCurrentOrder"], payload["status"], 
                payload["address"],
                payload["longitude"], payload["latitude"], 
                payload.get("imageURL"),
            ),
        )
        db.get_db().commit()
        new_id = cursor.lastrowid
        cursor.close()
        return jsonify({"message": "created", "spotID": new_id}), 201

    except Error as e:
        current_app.logger.error(f"create_spot error: {e}")
        return jsonify({"error": str(e)}), 500


@spots.route("/<int:spot_id>", methods=["DELETE"])
def delete_spot(spot_id: int):
    try:
        cursor = db.get_db().cursor()
        cursor.execute("DELETE FROM Spot WHERE spotID=%s", (spot_id,))
        db.get_db().commit()
        cursor.close()
        return jsonify({"ok": True, "spotID": spot_id}), 200
    except Error as e:
        current_app.logger.error(f"delete_spot error: {e}")
        return jsonify({"error": str(e)}), 500


@spots.route("/near", methods=["GET"])
def near():
    """
    GET /spots/near?lat=29.6516&lng=-82.3248&radius_km=5&status=free
    Uses haversine formula in SQL; returns up to 100 rows ordered by distance.
    """
    try:
        lat_str = request.args.get("lat")
        lng_str = request.args.get("lng")
        radius_str = request.args.get("radius_km", "5")
        status = request.args.get("status")

        if not lat_str or not lng_str:
            return jsonify
        ({"error": "Missing required query params: lat, lng"}), 400
        try:
            lat = float(lat_str)
            lng = float(lng_str)
            radius_km = float(radius_str)
        except ValueError:
            return jsonify
        ({"error": "lat, lng, and radius_km must be numeric"}), 400
        if status and not _valid_status(status):
            return jsonify({"error": "Invalid status"}), 400

        params = [lat, lng, lat]
        query = (
            "SELECT spotID, price, contactTel, estViewPerMonth, monthlyRentCost,"
            " endTimeOfCurrentOrder, status, address, longitude, latitude, "
            "(6371 * acos( cos(radians(%s)) * cos(radians(latitude)) * "
            "cos(radians(longitude) - radians(%s)) + sin(radians(%s)) * sin(radians(latitude)) )) AS distance_km "
            "FROM Spot WHERE latitude IS NOT NULL AND longitude IS NOT NULL "
        )
        if status:
            query += "AND status = %s "
            params.append(status)
        query += "HAVING distance_km <= %s ORDER BY distance_km ASC LIMIT 100"
        params.append(radius_km)

        cursor = db.get_db().cursor()
        cursor.execute(query, tuple(params))
        data = cursor.fetchall()
        cursor.close()
        return jsonify(data), 200

    except Error as e:
        current_app.logger.error(f"near error: {e}")
        return jsonify({"error": str(e)}), 500


@spots.route("/search", methods=["GET"])
def search():
    """
    GET /spots/search?q=Main&top_n=20
    Tries FULLTEXT on address; falls back to LIKE if unavailable.
    """
    try:
        q = (request.args.get("q") or request.args.get
             ("key_word") or "").strip()
        top_n = int(request.args.get("top_n", "20"))
        if not q:
            return jsonify([]), 200

        cursor = db.get_db().cursor()
        try:
            cursor.execute(
                (
                    "SELECT spotID, price, contactTel, estViewPerMonth, "
                    "monthlyRentCost, endTimeOfCurrentOrder, "
                    "status, address, longitude, latitude "
                    "FROM Spot WHERE MATCH(address) AGAINST ("
                    "%s IN NATURAL LANGUAGE MODE) "
                    "LIMIT %s"
                ),
                (q, top_n),
            )
        except Error:
            cursor.execute(
                (
                    "SELECT spotID, price, contactTel, estViewPerMonth, "
                    "monthlyRentCost, endTimeOfCurrentOrder, "
                    "status, address, longitude, latitude "
                    "FROM Spot WHERE address LIKE %s LIMIT %s"
                ),
                (f"%{q}%", top_n),
            )

        data = cursor.fetchall()
        cursor.close()
        return jsonify(data), 200

    except Error as e:
        current_app.logger.error(f"search error: {e}")
        return jsonify({"error": str(e)}), 500
