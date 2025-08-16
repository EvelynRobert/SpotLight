# data.py
from __future__ import annotations
import os
from typing import Iterable, Optional, Dict, Any
import pandas as pd
import requests
import streamlit as st

# ---- Gainesville defaults (used by pages for centering) --------------------
GAINESVILLE_CENTER = (29.651634, -82.324826)                # (lat, lon)
GAINESVILLE_BBOX   = (-82.50, 29.56, -82.20, 29.80)         # minLon,minLat,maxLon,maxLat
CENTER_LAT, CENTER_LON = GAINESVILLE_CENTER

# ---- API base discovery ----------------------------------------------------

def _candidate_bases() -> list[str]:
    cands = [
        st.secrets.get("API_BASE_URL"),
        os.getenv("API_BASE_URL"),
        st.secrets.get("API_ROOT_URL"),
        os.getenv("API_ROOT_URL"),
        "http://localhost:5001/api",
        "http://localhost:5001",
    ]
    out: list[str] = []
    for b in cands:
        if b and b.rstrip("/") not in out:
            out.append(b.rstrip("/"))
    return out

def _api_call(method: str, path: str, *, params: Dict[str, Any] | None = None,
              json: Dict[str, Any] |
              None = None, timeout: int = 10) -> requests.Response:
    """
    Try the request against known base URLs until one succeeds.
    Caches the working base in session to speed up subsequent calls.
    Raises a RuntimeError if no base responds with 2xx.
    """
    bases = [st.session_state.get("_api_base")] if st.session_state.get("_api_base") else []
    bases += [b for b in _candidate_bases() if b not in bases]

    last_err: str | None = None
    for base in bases:
        url = f"{base}{path}"
        try:
            r = requests.request(method.upper(), url, params=params, 
                                 json=json, timeout=timeout)
            if r.ok:
                st.session_state["_api_base"] = base 
                return r
            last_err = f"{r.status_code} {r.text[:120]}"
        except Exception as e:
            last_err = str(e)
            continue
    raise RuntimeError(f"API request failed for {path}. Tried bases: {bases}. Last error: {last_err}")

# ---- Public helpers ------------------------------------

@st.cache_data(ttl=60, show_spinner=False)
def fetch_spots(
    statuses: Optional[Iterable[str]] = None,
    q: Optional[str] = None,
    bbox: Optional[tuple[float, float, float, float]] = None,
    limit: int = 300,
    offset: int = 0,
    sort: str = "spotID",
    order: str = "asc",
) -> pd.DataFrame:
    """
    GET /spots (works whether backend is /api/... or not).
    Raises RuntimeError if the API is unreachable.
    """
    params: Dict[str, Any] = {
        "limit": limit,
        "offset": offset,
        "sort": sort,
        "order": order,
    }
    if statuses:
        params["status"] = ",".join(statuses)
    if q:
        # Support both param names some backends use
        params["q"] = q
        params["key_word"] = q
    if bbox:
        params["bbox"] = ",".join(map(str, bbox))

    # Try both `/spots` and `/spots/` to be tolerant
    try:
        r = _api_call("GET", "/spots", params=params)
    except RuntimeError:
        r = _api_call("GET", "/spots/", params=params)

    df = pd.DataFrame(r.json())
    # Ensure expected columns exist 
    expected = ["spotID","address","status","price","estViewPerMonth",
                "imageURL","latitude","longitude","endTimeOfCurrentOrder"]
    for c in expected:
        if c not in df.columns:
            df[c] = None
    return df

@st.cache_data(ttl=60, show_spinner=False)
def fetch_spot(spot_id: int) -> dict:
    """GET /spots/{id} — raises RuntimeError if unreachable or 404."""
    r = _api_call("GET", f"/spots/{int(spot_id)}")
    return r.json()

def update_status(spot_id: int, new_status: str) -> bool:
    """
    Update a spot’s status. Supports both backend styles:
      1) PUT /om/spots/{id}/status   with JSON {"status": "..."}
      2) POST /spots/{id}/status/{status}
    Returns True on success, False otherwise (no CSV fallback).
    """
    try:
        r = _api_call("PUT", f"/om/spots/{int(spot_id)}/status", 
                      json={"status": new_status})
        return r.ok
    except Exception:
        # Try the alternate route
        try:
            r = _api_call("POST", f"/spots/{int(spot_id)}/status/{new_status}")
            return r.ok
        except Exception:
            return False

@st.cache_data(ttl=60, show_spinner=False)
def search_spots(q: str, top_n: int = 20) -> pd.DataFrame:
    """GET /spots/search — supports q or key_word."""
    r = _api_call("GET", "/spots/search", params={"q": q, "key_word": q, 
                                                  "top_n": top_n})
    df = pd.DataFrame(r.json())
    for c in ["spotID","address","status","price","estViewPerMonth",
              "latitude","longitude"]:
        if c not in df.columns:
            df[c] = None
    return df

@st.cache_data(ttl=60, show_spinner=False)
def kpi_summary() -> dict:
    """
    Lightweight KPIs for owner/O&M views. Tries /om/spots/metrics first,
    then /om/spots/summary. Returns {} if neither exists.
    """
    try:
        r = _api_call("GET", "/om/spots/metrics")
        return r.json()
    except Exception:
        try:
            r = _api_call("GET", "/om/spots/summary")
            return r.json()
        except Exception:
            return {}

def api_health() -> bool:
    """
    Quick health probe. Returns True if any base answers /health or /spots.
    """
    try:
        r = _api_call("GET", "/health", timeout=5)
        return r.ok
    except Exception:
        try:
            r = _api_call("GET", "/spots", params={"limit": 1}, timeout=5)
            return r.ok
        except Exception:
            return False

