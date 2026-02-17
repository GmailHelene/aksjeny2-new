#!/usr/bin/env python3
"""
Verify that a premium test user can log in and access /profile and /portfolio without 500 errors.
"""
import re
import sys
import time
import os
import requests
from pathlib import Path
from typing import Optional
from verify_helpers import detect_base_url

BASE = detect_base_url()
LOGIN_URL = f"{BASE}/auth/login"
PROFILE_URL = f"{BASE}/profile"
PORTFOLIO_URL = f"{BASE}/portfolio/"

EMAIL = "test@aksjeradar.trade"
PASSWORD = "aksjeradar2024"

s = requests.Session()

def get_csrf_token(html: str) -> Optional[str]:
    m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
    return m.group(1) if m else None

OUT = Path("verify_premium_access_result.txt")

try:
    # Wait briefly for server if just started
    for _ in range(5):
        try:
            r = s.get(f"{BASE}/health", timeout=2)
            if r.status_code in (200, 404):
                break
        except Exception:
            time.sleep(1)

    logs = []
    def log(line: str):
        logs.append(line)

    log(f"Detected base URL: {BASE}")
    log("Step 1: Fetch login page")
    resp = s.get(LOGIN_URL, timeout=10)
    log(f"  GET {LOGIN_URL} -> {resp.status_code}")
    token = get_csrf_token(resp.text)
    if not token:
        log("  ERROR: CSRF token not found on login page")
        OUT.write_text("\n".join(logs), encoding="utf-8")
        sys.exit(1)
    log("  CSRF token extracted")

    log("Step 2: Post login")
    data = {"csrf_token": token, "email": EMAIL, "password": PASSWORD, "submit": "Logg inn"}
    resp = s.post(LOGIN_URL, data=data, allow_redirects=False, timeout=15)
    log(f"  POST {LOGIN_URL} -> {resp.status_code}")
    if resp.status_code in (301,302,303,307,308):
        loc = resp.headers.get("Location")
        log(f"  Redirect to: {loc}")
        # follow one redirect
        resp = s.get(BASE + loc if loc and loc.startswith('/') else (loc or BASE), timeout=15)
        log(f"  Followed redirect -> {resp.status_code}")

    # Step 3: Profile
    log("Step 3: GET /profile")
    r_profile = s.get(PROFILE_URL, timeout=15, allow_redirects=False)
    log(f"  GET {PROFILE_URL} -> {r_profile.status_code}")
    if r_profile.status_code == 302:
        log(f"  Redirected to: {r_profile.headers.get('Location')}")
        r_profile = s.get(BASE + r_profile.headers.get('Location', ''), timeout=15)
        log(f"  Followed redirect -> {r_profile.status_code}")
    if r_profile.status_code >= 500:
        log("  ERROR: /profile returned server error")
        try:
            snippet = r_profile.text[:500]
            log("  Body snippet:\n" + snippet)
        except Exception:
            pass
        OUT.write_text("\n".join(logs), encoding="utf-8")
        sys.exit(2)

    # Step 4: Portfolio
    log("Step 4: GET /portfolio/")
    r_port = s.get(PORTFOLIO_URL, timeout=15, allow_redirects=False)
    log(f"  GET {PORTFOLIO_URL} -> {r_port.status_code}")
    if r_port.status_code == 302:
        log(f"  Redirected to: {r_port.headers.get('Location')}")
        r_port = s.get(BASE + r_port.headers.get('Location', ''), timeout=15)
        log(f"  Followed redirect -> {r_port.status_code}")
    if r_port.status_code >= 500:
        log("  ERROR: /portfolio returned server error")
        try:
            snippet = r_port.text[:500]
            log("  Body snippet:\n" + snippet)
        except Exception:
            pass
        OUT.write_text("\n".join(logs), encoding="utf-8")
        sys.exit(3)

    log("\nSUCCESS: Premium user can access /profile and /portfolio without 500 errors.")
    OUT.write_text("\n".join(logs), encoding="utf-8")
    sys.exit(0)
except Exception as e:
    try:
        OUT.write_text("Unexpected error: " + str(e), encoding="utf-8")
    except Exception:
        pass
    sys.exit(10)
