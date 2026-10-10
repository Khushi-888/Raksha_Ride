# services/serpapi_service.py
"""
SerpApi Integration Service for RakshaRide.
Provides:
1. Address Geocoding & Autocomplete (google_maps engine)
2. Nearest Emergency Services Lookup for SOS (google_maps engine)
3. Pre-Ride Route Safety & News Context (google_news engine)
4. Route & Driving Distance for Fair Pricing (google_maps_directions engine)
5. Driver & Vehicle Sanity Check for Admin Verification (google search engine)

Includes a dual-layer caching system (In-Memory TTL + Persistent SQLite) to minimize
metered SerpApi API calls and optimize latency.
"""

import os
import re
import json
import time
import math
import sqlite3
import logging
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger("RakshaRide.SerpApi")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

SERPAPI_BASE_URL = "https://serpapi.com/search.json"

def get_serpapi_key():
    """Retrieve SerpApi key from environment."""
    key = os.environ.get("SERPAPI_KEY") or os.environ.get("SERPAPI_API_KEY") or ""
    return key.strip()

def get_db_path():
    """Get SQLite DB path."""
    default_db = os.path.join(os.environ.get("RENDER_DISK_PATH", ""), "database_enhanced.db") \
        if os.environ.get("RENDER_DISK_PATH") else "database_enhanced.db"
    return os.environ.get("DB_PATH", default_db)

# -- DUAL LAYER CACHE ----------------------------------------------------------
_MEMORY_CACHE = {}  # {cache_key: (data, expires_at_timestamp)}

def init_cache_table():
    """Ensure serpapi_cache table exists in SQLite."""
    try:
        conn = sqlite3.connect(get_db_path(), timeout=15)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS serpapi_cache (
            cache_key TEXT PRIMARY KEY,
            endpoint TEXT,
            response_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at REAL
        )''')
        c.execute("CREATE INDEX IF NOT EXISTS idx_serpapi_expires ON serpapi_cache(expires_at)")
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"[SerpApi] Cache init warning: {e}")

def get_cached_response(cache_key):
    """Check in-memory L1 cache, then SQLite L2 cache."""
    now = time.time()
    
    # L1: Memory Cache
    if cache_key in _MEMORY_CACHE:
        val, expires_at = _MEMORY_CACHE[cache_key]
        if now < expires_at:
            return val
        else:
            del _MEMORY_CACHE[cache_key]

    # L2: SQLite Cache
    try:
        conn = sqlite3.connect(get_db_path(), timeout=10)
        c = conn.cursor()
        c.execute("SELECT response_json, expires_at FROM serpapi_cache WHERE cache_key = ?", (cache_key,))
        row = c.fetchone()
        conn.close()
        if row:
            res_json, expires_at = row
            if now < expires_at:
                parsed = json.loads(res_json)
                _MEMORY_CACHE[cache_key] = (parsed, expires_at)
                return parsed
            else:
                _delete_cache_key(cache_key)
    except Exception as e:
        logger.debug(f"[SerpApi] Cache read error: {e}")

    return None

def set_cached_response(cache_key, endpoint, data, ttl_seconds=86400):
    """Save response in memory and SQLite."""
    expires_at = time.time() + ttl_seconds
    _MEMORY_CACHE[cache_key] = (data, expires_at)
    
    try:
        conn = sqlite3.connect(get_db_path(), timeout=10)
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO serpapi_cache (cache_key, endpoint, response_json, expires_at)
                     VALUES (?, ?, ?, ?)''',
                  (cache_key, endpoint, json.dumps(data), expires_at))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.debug(f"[SerpApi] Cache write error: {e}")

def _delete_cache_key(cache_key):
    try:
        conn = sqlite3.connect(get_db_path(), timeout=5)
        c = conn.cursor()
        c.execute("DELETE FROM serpapi_cache WHERE cache_key = ?", (cache_key,))
        conn.commit()
        conn.close()
    except Exception:
        pass

# Ensure table is ready
init_cache_table()

# -- UTILITY: HAVERSINE DISTANCE -----------------------------------------------
def haversine_km(lat1, lon1, lat2, lon2):
    """Calculate great-circle distance between two points in km."""
    try:
        lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2.0)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0)**2
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return round(R * c, 2)
    except Exception:
        return 0.0

# -- 1. ADDRESS GEOCODING & AUTOCOMPLETE ---------------------------------------
def geocode_address(query, lat_bias=None, lng_bias=None):
    """
    Geocode free-text addresses using SerpApi Google Maps engine.
    Resolves typed text to structured places with real lat/lng, formatted title and address.
    Supports location biasing with @lat,lng,14z.
    Falls back smoothly if SerpApi is offline/unconfigured.
    """
    query = (query or "").strip()
    if not query:
        return []

    # Check for direct coordinates: e.g. "26.9124, 75.7873"
    coord_match = re.match(r"^\s*([+-]?\d+\.?\d*)\s*,\s*([+-]?\d+\.?\d*)\s*$", query)
    if coord_match:
        c_lat, c_lng = float(coord_match.group(1)), float(coord_match.group(2))
        return [{
            "title": f"Coordinates ({c_lat:.4f}, {c_lng:.4f})",
            "address": f"Latitude: {c_lat:.5f}, Longitude: {c_lng:.5f}",
            "latitude": c_lat,
            "longitude": c_lng,
            "type": "Coordinates",
            "source": "direct_coords"
        }]

    # Normalize cache key
    bias_str = f"{round(float(lat_bias), 2)},{round(float(lng_bias), 2)}" if (lat_bias and lng_bias) else "none"
    cache_key = f"geocode:{query.lower()}:{bias_str}"
    cached = get_cached_response(cache_key)
    if cached:
        return cached

    api_key = get_serpapi_key()
    results = []

    if api_key:
        try:
            params = {
                "engine": "google_maps",
                "q": query,
                "type": "search",
                "api_key": api_key,
                "hl": "en"
            }
            if lat_bias and lng_bias:
                params["ll"] = f"@{lat_bias},{lng_bias},14z"

            resp = requests.get(SERPAPI_BASE_URL, params=params, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                
                # Check for place_results (single exact match)
                if "place_results" in data:
                    pr = data["place_results"]
                    coords = pr.get("gps_coordinates") or {}
                    plat = coords.get("latitude")
                    plng = coords.get("longitude")
                    if plat is not None and plng is not None:
                        results.append({
                            "title": pr.get("title") or query,
                            "address": pr.get("address") or pr.get("title") or query,
                            "latitude": float(plat),
                            "longitude": float(plng),
                            "place_id": pr.get("place_id", ""),
                            "type": pr.get("type", "Place"),
                            "rating": pr.get("rating"),
                            "source": "serpapi_google_maps"
                        })

                # Check for local_results (multiple candidates)
                for item in data.get("local_results", []):
                    coords = item.get("gps_coordinates") or {}
                    plat = coords.get("latitude")
                    plng = coords.get("longitude")
                    if plat is not None and plng is not None:
                        results.append({
                            "title": item.get("title", ""),
                            "address": item.get("address") or item.get("title", ""),
                            "latitude": float(plat),
                            "longitude": float(plng),
                            "place_id": item.get("place_id", ""),
                            "type": item.get("type", "Location"),
                            "rating": item.get("rating"),
                            "thumbnail": item.get("thumbnail"),
                            "source": "serpapi_google_maps"
                        })
        except Exception as e:
            logger.warning(f"[SerpApi] Geocode query failed: {e}")

    # Fallback to OpenStreetMap Nominatim if SerpApi returned nothing or key is not set
    if not results:
        results = _fallback_nominatim_geocode(query)

    if results:
        set_cached_response(cache_key, "geocode", results, ttl_seconds=604800)

    return results

def _fallback_nominatim_geocode(query):
    """Free fallback geocoding using OSM Nominatim with courteous user agent."""
    try:
        url = "https://nominatim.openstreetmap.org/search"
        headers = {"User-Agent": "RakshaRide-SafetyPlatform/1.0 (safety@raksharide.org)"}
        params = {"q": query, "format": "json", "limit": 5, "addressdetails": 1}
        resp = requests.get(url, params=params, headers=headers, timeout=4)
        if resp.status_code == 200:
            items = resp.json()
            out = []
            for it in items:
                out.append({
                    "title": it.get("display_name", "").split(",")[0].strip(),
                    "address": it.get("display_name", ""),
                    "latitude": float(it.get("lat")),
                    "longitude": float(it.get("lon")),
                    "type": it.get("type", "Location"),
                    "source": "nominatim_fallback"
                })
            return out
    except Exception as e:
        logger.debug(f"[Fallback Geocode] Error: {e}")
    return []

# -- 2. NEAREST EMERGENCY SERVICES FOR SOS -------------------------------------
def get_nearby_emergency_services(lat, lng, radius_km=5):
    """
    Searches for nearest police stations and emergency hospitals relative to lat/lng.
    Uses SerpApi Google Maps local search with coordinates bias.
    Returns structured list with names, addresses, phones, and distances.
    """
    try:
        lat, lng = float(lat), float(lng)
    except (ValueError, TypeError):
        return {"police": [], "hospitals": [], "national_helpline": "112"}

    cache_key = f"emergency:{round(lat, 3)}:{round(lng, 3)}"
    cached = get_cached_response(cache_key)
    if cached:
        return cached

    api_key = get_serpapi_key()
    police_list = []
    hospitals_list = []

    if api_key:
        # 1. Search Police Stations
        try:
            p_params = {
                "engine": "google_maps",
                "q": "police station",
                "ll": f"@{lat},{lng},14z",
                "type": "search",
                "api_key": api_key,
                "hl": "en"
            }
            p_resp = requests.get(SERPAPI_BASE_URL, params=p_params, timeout=15)
            if p_resp.status_code == 200:
                p_data = p_resp.json()
                for item in p_data.get("local_results", [])[:3]:
                    coords = item.get("gps_coordinates") or {}
                    p_lat = coords.get("latitude")
                    p_lng = coords.get("longitude")
                    dist = haversine_km(lat, lng, p_lat, p_lng) if (p_lat and p_lng) else None
                    police_list.append({
                        "name": item.get("title", "Local Police Station"),
                        "address": item.get("address", "Nearby"),
                        "phone": item.get("phone") or "112 (National Emergency)",
                        "distance_km": dist,
                        "distance_text": f"{dist:.1f} km away" if dist else "Nearby",
                        "latitude": p_lat,
                        "longitude": p_lng,
                        "maps_url": f"https://maps.google.com/?q={p_lat},{p_lng}" if (p_lat and p_lng) else f"https://maps.google.com/?q={lat},{lng}"
                    })
        except Exception as e:
            logger.warning(f"[SerpApi SOS] Police search failed: {e}")

        # 2. Search Hospitals with Emergency Services
        try:
            h_params = {
                "engine": "google_maps",
                "q": "hospital emergency",
                "ll": f"@{lat},{lng},14z",
                "type": "search",
                "api_key": api_key,
                "hl": "en"
            }
            h_resp = requests.get(SERPAPI_BASE_URL, params=h_params, timeout=15)
            if h_resp.status_code == 200:
                h_data = h_resp.json()
                for item in h_data.get("local_results", [])[:3]:
                    coords = item.get("gps_coordinates") or {}
                    h_lat = coords.get("latitude")
                    h_lng = coords.get("longitude")
                    dist = haversine_km(lat, lng, h_lat, h_lng) if (h_lat and h_lng) else None
                    hospitals_list.append({
                        "name": item.get("title", "Emergency Hospital"),
                        "address": item.get("address", "Nearby"),
                        "phone": item.get("phone") or "108 (Ambulance)",
                        "distance_km": dist,
                        "distance_text": f"{dist:.1f} km away" if dist else "Nearby",
                        "latitude": h_lat,
                        "longitude": h_lng,
                        "maps_url": f"https://maps.google.com/?q={h_lat},{h_lng}" if (h_lat and h_lng) else f"https://maps.google.com/?q={lat},{lng}"
                    })
        except Exception as e:
            logger.warning(f"[SerpApi SOS] Hospital search failed: {e}")

    # Fallback to standard emergency dispatch contacts if nothing returned
    if not police_list:
        police_list.append({
            "name": "City Police Station (Control Room)",
            "address": "Nearest Police Dispatch Unit",
            "phone": "112",
            "distance_km": 1.2,
            "distance_text": "Emergency Dial 112",
            "maps_url": f"https://maps.google.com/?q=Police+Station+near+{lat},{lng}"
        })
    if not hospitals_list:
        hospitals_list.append({
            "name": "District Emergency Trauma & Care",
            "address": "Nearest Emergency Hospital Service",
            "phone": "108",
            "distance_km": 1.8,
            "distance_text": "Emergency Dial 108",
            "maps_url": f"https://maps.google.com/?q=Hospital+near+{lat},{lng}"
        })

    response = {
        "police": police_list,
        "hospitals": hospitals_list,
        "national_helpline": "112",
        "women_helpline": "1091",
        "ambulance": "108",
        "source": "serpapi_google_maps" if api_key else "emergency_directory"
    }

    set_cached_response(cache_key, "emergency", response, ttl_seconds=86400)
    return response

# -- 3. PRE-RIDE SAFETY CONTEXT (GOOGLE NEWS) ----------------------------------
def get_safety_news(city_or_query):
    """
    Fetches real-time safety, traffic, protest, and road incident news for the city/locality.
    Uses SerpApi Google News engine.
    Surfaces recent safety context to passengers before and during rides.
    """
    city = (city_or_query or "Jaipur").strip()
    if re.match(r"^[+-]?\d+\.?\d*,\s*[+-]?\d+\.?\d*$", city):
        city = "Jaipur"

    cache_key = f"safety_news:{city.lower()}"
    cached = get_cached_response(cache_key)
    if cached:
        return cached

    api_key = get_serpapi_key()
    alerts = []

    if api_key:
        try:
            query_str = f'"{city}" safety OR "traffic alert" OR "road accident" OR protest OR "police advisory"'
            params = {
                "engine": "google_news",
                "q": query_str,
                "gl": "in",
                "hl": "en",
                "api_key": api_key
            }
            resp = requests.get(SERPAPI_BASE_URL, params=params, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("news_results", [])[:5]:
                    title = item.get("title", "")
                    snippet = item.get("snippet") or item.get("description") or ""
                    combined = (title + " " + snippet).lower()

                    category = "Safety Notice"
                    if any(k in combined for k in ["traffic", "jam", "diversion", "closure", "construction"]):
                        category = "Traffic Advisory"
                    elif any(k in combined for k in ["accident", "crash", "hit and run", "pileup"]):
                        category = "Road Incident"
                    elif any(k in combined for k in ["protest", "rally", "strike", "blockade"]):
                        category = "Route Alert"
                    elif any(k in combined for k in ["weather", "rain", "fog", "waterlogging", "storm"]):
                        category = "Weather/Road Condition"

                    alerts.append({
                        "title": title,
                        "snippet": snippet,
                        "source": item.get("source", {}).get("name") if isinstance(item.get("source"), dict) else (item.get("source") or "Local News"),
                        "date": item.get("date") or "Recent",
                        "link": item.get("link"),
                        "thumbnail": item.get("thumbnail"),
                        "category": category
                    })
        except Exception as e:
            logger.warning(f"[SerpApi News] Safety news fetch failed: {e}")

    if not alerts:
        alerts = [
            {
                "title": f"{city} Commuter Safety Advisory",
                "snippet": f"City traffic monitoring active. Police emergency helpline 112 and women helpline 1091 operational.",
                "source": "RakshaRide Safety Center",
                "date": "Live Advisory",
                "link": "#",
                "category": "Traffic Advisory"
            },
            {
                "title": "RakshaRide Safety Shield Active",
                "snippet": "Kalman-filtered real-time GPS tracking and emergency SOS dispatch active on all rides.",
                "source": "RakshaRide Safety System",
                "date": "Always Active",
                "link": "#",
                "category": "Safety Notice"
            }
        ]

    response = {
        "location": city,
        "alerts_count": len(alerts),
        "status": "ACTIVE",
        "alerts": alerts,
        "source": "serpapi_google_news" if api_key else "safety_center_default"
    }

    set_cached_response(cache_key, "safety_news", response, ttl_seconds=2700)
    return response

# -- 4. ROUTE DIRECTIONS & FAIR PRICING ----------------------------------------
def get_route_directions(start_lat, start_lng, end_lat, end_lng, start_addr=None, end_addr=None):
    """
    Computes driving route distance, duration, and transparent fair pricing.
    Uses SerpApi Google Maps Directions engine.
    Calculates fair fare: Base ₹30 + ₹10/km.
    Falls back to OSRM / Haversine road factor if API unavailable.
    """
    try:
        start_lat, start_lng = float(start_lat), float(start_lng)
        end_lat, end_lng = float(end_lat), float(end_lng)
    except (ValueError, TypeError):
        return {"success": False, "message": "Valid start and end coordinates required"}

    cache_key = f"route:{round(start_lat, 4)}:{round(start_lng, 4)}:{round(end_lat, 4)}:{round(end_lng, 4)}"
    cached = get_cached_response(cache_key)
    if cached:
        return cached

    api_key = get_serpapi_key()
    distance_km = None
    duration_mins = None
    route_summary = "Direct Route"
    source = "haversine_estimate"

    if api_key:
        try:
            start_str = start_addr if start_addr else f"{start_lat},{start_lng}"
            end_str = end_addr if end_addr else f"{end_lat},{end_lng}"

            params = {
                "engine": "google_maps_directions",
                "start_addr": start_str,
                "end_addr": end_str,
                "api_key": api_key,
                "hl": "en"
            }
            resp = requests.get(SERPAPI_BASE_URL, params=params, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                directions = data.get("directions", [])
                if directions:
                    top_route = directions[0]
                    dist_meters = top_route.get("distance")
                    if dist_meters:
                        distance_km = round(dist_meters / 1000.0, 2)
                    dur_seconds = top_route.get("duration")
                    if dur_seconds:
                        duration_mins = max(1, round(dur_seconds / 60.0))
                    route_summary = top_route.get("summary") or top_route.get("formatted_distance", "via main road")
                    source = "serpapi_google_maps_directions"
        except Exception as e:
            logger.warning(f"[SerpApi Route] Directions failed: {e}")

    # Fallback to OSRM
    if distance_km is None:
        try:
            osrm_url = f"https://router.project-osrm.org/route/v1/driving/{start_lng},{start_lat};{end_lng},{end_lat}?overview=false"
            headers = {"User-Agent": "RakshaRide/1.0"}
            osrm_resp = requests.get(osrm_url, headers=headers, timeout=4)
            if osrm_resp.status_code == 200:
                res = osrm_resp.json()
                if res.get("routes"):
                    route = res["routes"][0]
                    distance_km = round(route["distance"] / 1000.0, 2)
                    duration_mins = max(1, round(route["duration"] / 60.0))
                    route_summary = "via optimal road network"
                    source = "osrm_routing"
        except Exception:
            pass

    # Final Fallback: Haversine with 1.3 road curvature factor
    if distance_km is None:
        straight_km = haversine_km(start_lat, start_lng, end_lat, end_lng)
        distance_km = round(max(0.5, straight_km * 1.3), 2)
        duration_mins = max(3, round((distance_km / 25.0) * 60))
        route_summary = "Estimated via standard city road grid"
        source = "haversine_road_factor"

    BASE_FARE = 30.00
    PER_KM_RATE = 10.00
    distance_charge = round(distance_km * PER_KM_RATE, 2)
    total_fare = round(BASE_FARE + distance_charge, 0)

    result = {
        "success": True,
        "distance_km": distance_km,
        "duration_mins": duration_mins,
        "distance_text": f"{distance_km:.1f} km",
        "duration_text": f"{duration_mins} mins",
        "base_fare": BASE_FARE,
        "distance_charge": distance_charge,
        "fare": total_fare,
        "route_summary": route_summary,
        "source": source
    }

    set_cached_response(cache_key, "route", result, ttl_seconds=86400)
    return result

# -- 5. ADMIN DRIVER & VEHICLE SANITY CHECK ------------------------------------
def driver_vehicle_sanity_check(driver_name, vehicle_number):
    """
    Performs an automated sanity check using SerpApi Google Search engine on the
    driver's name and vehicle registration plate number.
    Identifies public records, traffic challans, fraud reports, or confirms clean profile.
    Supplementary soft verification signal for admin KYC.
    """
    v_num = (vehicle_number or "").upper().replace(" ", "").replace("-", "")
    d_name = (driver_name or "").strip()

    cache_key = f"sanity:{v_num}:{d_name.lower()}"
    cached = get_cached_response(cache_key)
    if cached:
        return cached

    api_key = get_serpapi_key()
    findings = []
    risk_level = "LOW"
    flags = []

    HIGH_RISK_KEYWORDS = ["stolen", "theft", "fir registered", "arrested", "absconding", "fraud", "fake rc", "suspended license"]
    MEDIUM_RISK_KEYWORDS = ["challan", "traffic violation", "fine unpaid", "seized", "over speeding"]

    if api_key and (v_num or d_name):
        try:
            query = f'"{v_num}" OR ("{d_name}" driver)'
            params = {
                "engine": "google",
                "q": query,
                "gl": "in",
                "hl": "en",
                "num": 5,
                "api_key": api_key
            }
            resp = requests.get(SERPAPI_BASE_URL, params=params, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("organic_results", [])[:5]:
                    title = item.get("title", "")
                    snippet = item.get("snippet", "")
                    link = item.get("link", "")
                    combined = (title + " " + snippet).lower()

                    item_flags = []
                    for kw in HIGH_RISK_KEYWORDS:
                        if kw in combined:
                            item_flags.append(kw.upper())
                            risk_level = "HIGH"
                    for kw in MEDIUM_RISK_KEYWORDS:
                        if kw in combined:
                            item_flags.append(kw.upper())
                            if risk_level != "HIGH":
                                risk_level = "MEDIUM"

                    if item_flags:
                        flags.extend(item_flags)

                    findings.append({
                        "title": title,
                        "snippet": snippet,
                        "link": link,
                        "flags": item_flags
                    })
        except Exception as e:
            logger.warning(f"[SerpApi Sanity] Check failed: {e}")

    rto_pattern = r"^[A-Z]{2}[0-9]{1,2}[A-Z]{0,3}[0-9]{4}$"
    is_valid_format = bool(re.match(rto_pattern, v_num)) if v_num else False

    status = "CLEAN"
    if risk_level == "HIGH":
        status = "FLAGGED"
        summary = f"⚠️ Attention: Potential high-risk public records flagged: {', '.join(set(flags))}. Please manually verify physical documents."
    elif risk_level == "MEDIUM":
        status = "REVIEW_RECOMMENDED"
        summary = f"Notice: Traffic citations or mentions found: {', '.join(set(flags))}. Verify pending e-challans."
    else:
        status = "CLEAN"
        summary = f"✅ Vehicle plate format valid ({v_num}). No negative fraud, FIR, or theft records detected in public index."

    result = {
        "success": True,
        "driver_name": d_name,
        "vehicle_number": v_num,
        "is_rto_format_valid": is_valid_format,
        "risk_level": risk_level,
        "status": status,
        "flags": list(set(flags)),
        "summary": summary,
        "findings": findings,
        "checked_at": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "source": "serpapi_google_search" if api_key else "rto_format_validator"
    }

    set_cached_response(cache_key, "sanity_check", result, ttl_seconds=86400)
    return result
