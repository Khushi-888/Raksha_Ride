# services/serpapi_routes.py
"""
Flask Blueprint defining SerpApi powered endpoints for RakshaRide:
- GET /api/geocode: Autocomplete & geocode addresses to lat/lng
- GET /api/nearby_safety: Pre-ride route safety & news context
- GET /api/route: Road distance, duration & transparent fare calculation
- GET /api/nearby_emergency: Nearest police and hospital emergency contacts
- GET /api/admin/driver_sanity_check: Soft background check for drivers
"""

import sqlite3
from flask import Blueprint, request, jsonify, session
from services.serpapi_service import (
    geocode_address,
    get_nearby_emergency_services,
    get_safety_news,
    get_route_directions,
    driver_vehicle_sanity_check,
    get_db_path
)

serpapi_bp = Blueprint("serpapi", __name__)

@serpapi_bp.route("/api/geocode", methods=["GET"])
def api_geocode():
    """
    Address autocomplete & geocoding.
    Params:
      q: text address or query (required)
      lat: optional user latitude for location biasing
      lng: optional user longitude for location biasing
    """
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"success": False, "message": "Query parameter 'q' is required", "results": []}), 400

    lat = request.args.get("lat", type=float)
    lng = request.args.get("lng", type=float)

    try:
        results = geocode_address(query, lat_bias=lat, lng_bias=lng)
        return jsonify({
            "success": True,
            "query": query,
            "count": len(results),
            "results": results
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e), "results": []}), 500


@serpapi_bp.route("/api/nearby_safety", methods=["GET"])
def api_nearby_safety():
    """
    Pre-ride safety news & road alerts.
    Params:
      city: City name or locality (default: Jaipur)
      lat: optional latitude (to deduce city)
      lng: optional longitude
    """
    city = request.args.get("city", "").strip()
    if not city:
        city = request.args.get("q", "").strip()

    lat = request.args.get("lat", type=float)
    lng = request.args.get("lng", type=float)

    if not city and lat and lng:
        city = "Jaipur"

    city = city or "Jaipur"

    try:
        data = get_safety_news(city)
        return jsonify({
            "success": True,
            **data
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e), "alerts": []}), 500


@serpapi_bp.route("/api/route", methods=["GET"])
def api_route():
    """
    Calculates driving distance, duration, and fair pricing.
    Params:
      lat1: pickup latitude (required)
      lng1: pickup longitude (required)
      lat2: dropoff latitude (required)
      lng2: dropoff longitude (required)
      pickup: optional pickup address text
      dropoff: optional dropoff address text
    """
    lat1 = request.args.get("lat1", type=float)
    lng1 = request.args.get("lng1", type=float)
    lat2 = request.args.get("lat2", type=float)
    lng2 = request.args.get("lng2", type=float)

    pickup_addr = request.args.get("pickup", "").strip() or None
    dropoff_addr = request.args.get("dropoff", "").strip() or None

    if None in [lat1, lng1, lat2, lng2]:
        return jsonify({"success": False, "message": "lat1, lng1, lat2, and lng2 are required"}), 400

    try:
        route_info = get_route_directions(lat1, lng1, lat2, lng2, start_addr=pickup_addr, end_addr=dropoff_addr)
        return jsonify(route_info)
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@serpapi_bp.route("/api/nearby_emergency", methods=["GET"])
def api_nearby_emergency():
    """
    Lookup nearest police stations and hospitals for SOS.
    Params:
      lat: current latitude
      lng: current longitude
    """
    lat = request.args.get("lat", type=float)
    lng = request.args.get("lng", type=float)

    if lat is None or lng is None:
        return jsonify({"success": False, "message": "lat and lng are required"}), 400

    try:
        services = get_nearby_emergency_services(lat, lng)
        return jsonify({
            "success": True,
            "lat": lat,
            "lng": lng,
            **services
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@serpapi_bp.route("/api/admin/driver_sanity_check", methods=["GET"])
def api_admin_driver_sanity_check():
    """
    Admin soft fraud/sanity check for drivers using Google Search via SerpApi.
    Params:
      driver_id: driver database ID (optional if name/vehicle provided)
      name: driver full name
      vehicle: vehicle registration number
    """
    if not session.get("is_admin"):
        return jsonify({"success": False, "message": "Admin authorization required"}), 401

    driver_id = request.args.get("driver_id", type=int)
    name = request.args.get("name", "").strip()
    vehicle = request.args.get("vehicle", "").strip()

    if driver_id and (not name or not vehicle):
        try:
            conn = sqlite3.connect(get_db_path(), timeout=10)
            c = conn.cursor()
            c.execute("SELECT name, vehicle_number FROM drivers WHERE id = ?", (driver_id,))
            row = c.fetchone()
            conn.close()
            if row:
                name = name or row[0]
                vehicle = vehicle or row[1]
        except Exception:
            pass

    if not name and not vehicle:
        return jsonify({"success": False, "message": "Driver name or vehicle number required"}), 400

    try:
        report = driver_vehicle_sanity_check(name, vehicle)
        return jsonify(report)
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
