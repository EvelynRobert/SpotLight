# salesman_route.py
from flask import Blueprint, request, jsonify, current_app
import mysql.connector as mysql

salesman_bp = Blueprint("salesman", __name__, url_prefix="/salesman")
salesman_bp.strict_slashes = False

def _get_conn():
    cfg = current_app.config
    return mysql.connect(
        host=cfg.get("MYSQL_DATABASE_HOST", "127.0.0.1"),
        port=int(cfg.get("MYSQL_DATABASE_PORT", 3306)),
        user=cfg.get("MYSQL_DATABASE_USER", "root"),
        password=cfg.get("MYSQL_DATABASE_PASSWORD", "changeme"),
        database=cfg.get("MYSQL_DATABASE_DB", "SpotLight"),
    )

def _table_exists(cur, name):
    cur.execute("SHOW TABLES LIKE %s", (name,))
    return cur.fetchone() is not None

def _column_exists(cur, table, column):
    cur.execute(f"SHOW COLUMNS FROM `{table}` LIKE %s", (column,))
    return cur.fetchone() is not None

@salesman_bp.get("/orders/pending")
def pending_orders():
    """List 'to-be-processed' orders for a salesman."""
    try:
        conn = _get_conn(); cur = conn.cursor(dictionary=True)
        if not _table_exists(cur, "ToBeProcessedOrder"):
            return jsonify({"data": [], "note": "table ToBeProcessedOrder not found"}), 200
        cur.execute("SELECT * FROM ToBeProcessedOrder ORDER BY orderID DESC LIMIT 100")
        rows = cur.fetchall()
        cur.close(); conn.close()
        return jsonify(rows), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@salesman_bp.put("/spots/<int:spot_id>/status")
def update_spot_status(spot_id: int):
    """Update a spot's status (e.g., free, inuse, planned, w.issue)."""
    body = request.get_json(silent=True) or {}
    new_status = (body.get("status") or "").strip()
    if not new_status:
        return jsonify({"error": "Missing 'status' in JSON body"}), 400
    try:
        conn = _get_conn(); cur = conn.cursor(dictionary=True)
        if not _table_exists(cur, "Spot"):
            return jsonify({"error": "table Spot not found"}), 400
        if not _column_exists(cur, "Spot", "status"):
            return jsonify({"error": "column 'status' not found on Spot"}), 400
        cur.execute("UPDATE Spot SET status=%s WHERE spotID=%s", (new_status, spot_id))
        conn.commit()
        cur.execute("SELECT * FROM Spot WHERE spotID=%s", (spot_id,))
        row = cur.fetchone()
        cur.close(); conn.close()
        if not row:
            return jsonify({"error": f"spotID {spot_id} not found"}), 404
        return jsonify(row), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@salesman_bp.get("/spots")
def salesman_spots():
    """
    Search/list spots for a salesman.
    - /salesman/spots?status=inuse
    - /salesman/spots?lat=29.65&lng=-82.32&radius_km=8
    """
    status = request.args.get("status")
    lat = request.args.get("lat", type=float)
    lng = request.args.get("lng", type=float)
    radius_km = request.args.get("radius_km", type=float)

    try:
        conn = _get_conn(); cur = conn.cursor(dictionary=True)
        if not _table_exists(cur, "Spot"):
            return jsonify({"data": [], "note": "table Spot not found"}), 200

        if lat is not None and lng is not None and radius_km is not None:
            # Haversine (km)
            q = """
                SELECT
                  spotID, address, latitude, longitude,
                  IFNULL(status,'') AS status,
                  (6371 * 2 * ASIN(SQRT(
                      POWER(SIN(RADIANS(%s - latitude)/2), 2) +
                      COS(RADIANS(latitude)) * COS(RADIANS(%s)) *
                      POWER(SIN(RADIANS(%s - longitude)/2), 2)
                  ))) AS distance_km
                FROM Spot
                {where}
                HAVING distance_km <= %s
                ORDER BY distance_km
                LIMIT 200
            """
            where = ""
            params = [lat, lat, lng]
            if status:
                where = "WHERE status = %s"
                params.append(status)
            q = q.format(where=where)
            params.append(radius_km)
            cur.execute(q, tuple(params))
        else:
            if status:
                cur.execute(
                    "SELECT spotID, address, latitude, longitude, IFNULL(status,'') AS status "
                    "FROM Spot WHERE status=%s ORDER BY spotID DESC LIMIT 200",
                    (status,),
                )
            else:
                cur.execute(
                    "SELECT spotID, address, latitude, longitude, IFNULL(status,'') AS status "
                    "FROM Spot ORDER BY spotID DESC LIMIT 200"
                )

        rows = cur.fetchall()
        cur.close(); conn.close()
        return jsonify(rows), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
