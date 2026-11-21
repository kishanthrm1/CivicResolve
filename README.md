# 🏛️ CivicResolve: AI-Powered Civic Issue Reporting and Resolution Platform
> **Production-Grade Civic Technology Platform** | Built with Python, Flask, SQLite, Tailwind CSS, Leaflet.js, Chart.js, and Google Gemini 2.5 Flash (with 100% Offline AI Fallback).

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Docker Ready](https://img.shields.io/badge/docker-Cloud%20Run%20Ready-blue)](https://cloud.google.com/run)
[![Tests Passing](https://img.shields.io/badge/pytest-N%20passed-brightgreen.svg)](tests/)
[![WCAG 2.1 AA Minded](https://img.shields.io/badge/accessibility-WCAG%202.1%20AA-teal.svg)](#accessibility-notes)
[![Security Hardened](https://img.shields.io/badge/security-CSRF%20%7C%20RateLimit%20%7C%20Hashed%20Auth-darkred.svg)](#security-notes)

---

## 📋 1. Project Overview & Problem Statement

Citizens encounter everyday infrastructure hazards—such as crater-like potholes, burst water mains, dangling live electric cables, open drainage manholes, and overflowing garbage bins. Reporting these issues is typically frustrating: citizens rarely know which specific municipal department is responsible, complaint intake forms are cumbersome, and status updates disappear into bureaucratic silos.

**CivicResolve** transforms municipal service delivery by applying automated AI triage and open-government transparency:
1. **Citizens** submit complaints in under 30 seconds with photos and browser GPS geolocation—no registration or login required.
2. **AI Triage Service** evaluates the public safety urgency (**Critical**, **High**, **Medium**, or **Low**), classifies the category, extracts a clean summary, and automatically routes the ticket to the responsible municipal department.
3. **Public Transparency & Tracking**: Citizens follow an interactive 3-stage progress timeline (`Reported` ➔ `In Progress` ➔ `Resolved`) with timestamped official staff remarks.
4. **Municipal Staff Command Center**: Staff prioritize life-safety hazards first, dispatch field crews, and override automated assignments when necessary.

---

## 🎯 2. Six Core Features & Problem Statement Alignment

| Feature | Citizen Capability | Municipal Authority Capability | Alignment with Civic Needs |
|---|---|---|---|
| **1. Citizen Issue Reporting** (`/report`) | Quick submission with title, description, address, browser GPS, category dropdown, and photo upload. | Receives structured, validated, and geotagged incident tickets. | Eliminates citizen friction; no account creation barrier. |
| **2. AI-Powered Classification** (`ai_service.py`) | Dual-mode: Cloud **Gemini 2.5 Flash** or 100% offline rule-based demo AI. | Consistent schema: category, department, priority, summary, confidence (0–100%). | Operates in low-connectivity or air-gapped scenarios without API keys. |
| **3. Priority Detection** | Clear badge showing severity: Critical, High, Medium, or Low. | Critical life hazards automatically float to the top of the queue. | Focuses emergency manpower on fatal threats (open manholes, live wires). |
| **4. Department Recommendation** | Automatically informs citizen which department owns the ticket. | Routes to Roads, Sanitation, Electricity, Water, or Drainage departments. | Stops ticket bouncing between municipal divisions. |
| **5. Tracking & Public Dashboard** (`/track`, `/dashboard`) | Real-time 3-stage visual timeline with official remarks; city-wide map view. | Public transparency fosters civic trust; Chart.js shows ward performance. | Accountability through open data and spatial visualization. |
| **6. Admin Command Center** (`/admin`) | N/A (Protected staff area). | Update status (`In Progress`, `Resolved`), append audit remarks, override AI triage, delete spam. | Complete operational control and audit history. |

---

## 🏛️ 3. Architecture & Code Structure

The project follows a modular, scalable architecture separating configuration, database layer, AI triage services, and routing blueprints:

```
civicresolve/
├── Dockerfile                  # Container definition for Google Cloud Run deployment
├── .dockerignore               # Optimized Docker build context
├── .gitignore                  # Git tracking rules
├── requirements.txt            # Production dependencies (Flask, Flask-WTF, Flask-Limiter, gunicorn, etc.)
├── requirements-dev.txt        # Development and testing dependencies (pytest)
├── config.py                   # Environment configuration classes (Dev, Prod, Test)
├── extensions.py               # CSRFProtect, Limiter, and login_required decorator
├── database.py                 # SQLite layer: parameterized queries, indexing, pagination, seeding
├── ai_service.py               # Dual-mode AI triage (Gemini 2.5 Flash + offline rules) with timeout
├── app.py                      # Application factory (create_app), security headers, structured JSON logging, error handlers, WSGI entry point
├── routes/                     # Clean Blueprint routing modules
│   ├── __init__.py             # Route exports
│   ├── citizen.py              # Citizen routes: /, /report, /success, /track, /dashboard, /complaint/<id>
│   ├── admin.py                # Admin routes: /admin/login, /admin/logout, /admin
│   └── api.py                  # API endpoints: /health, /api/stats, /api/complaints, /api/complaint/...
├── templates/                  # Accessible Jinja2 HTML templates
│   ├── base.html               # Semantic master layout, skip-link, CSRF meta, live regions
│   ├── index.html              # Landing page with hero, live KPIs, and how-it-works workflow
│   ├── report.html             # Citizen form with GPS, 5 MB image preview, and ARIA attributes
│   ├── success.html            # Confirmation screen with Complaint ID and AI diagnostic breakdown
│   ├── track.html              # Progress timeline and chronological audit history
│   ├── dashboard.html          # Public dashboard with Leaflet map, Chart.js, and pagination
│   ├── complaint_detail.html   # Comprehensive single-complaint inspection view
│   ├── admin_login.html        # Staff authentication with demo credentials hint
│   ├── admin.html              # Staff dispatch table with modal actions and CSRF fetch headers
│   ├── 404.html                # Branded "Page Not Found" error page (accessible)
│   └── 500.html                # Branded "Internal Server Error" error page (accessible)
├── static/
│   ├── css/style.css           # Custom animation keyframes, scrollbar, and Leaflet popup styles
│   ├── js/main.js              # Global toast manager and client utilities
│   └── uploads/                # Geotagged evidence uploads (UUID filenames)
└── tests/                      # Automated test suite (N tests)
    ├── __init__.py
    ├── conftest.py             # Pytest fixtures and test database lifecycle
    ├── test_classifier.py      # Rule-based AI triage unit tests
    ├── test_citizen_flow.py    # Reporting flow and input validation tests
    ├── test_admin.py           # Admin authentication and dispatch action tests
    ├── test_api.py             # /health check and public REST API tests
    ├── test_track.py           # Complaint tracking portal tests
    └── test_integration.py     # Full end-to-end integration suite (migrated from test_app.py)
```

---

## 💻 4. Tech Stack (100% Free, Zero Paid Subscriptions)

| Component | Technology | Rationale & Implementation Details |
|---|---|---|
| **Runtime & Backend** | Python 3.11+ & Flask | Lightweight, modular WSGI application with Blueprints |
| **WSGI Server** | Gunicorn | Production process manager binding to `0.0.0.0:$PORT` |
| **Database** | SQLite3 | Embedded SQL with connection pooling, indexes, and foreign keys |
| **Containerization** | Docker | Minimal `python:3.11-slim` image optimized for Cloud Run |
| **Security Layer** | Flask-WTF & Flask-Limiter | CSRF token validation on all forms; rate limiting on submissions and logins |
| **Password Storage** | Werkzeug Security | Constant-time `scrypt`/`pbkdf2` hashing (no plaintext secrets) |
| **GIS Mapping** | Leaflet.js + OpenStreetMap | Interactive spatial map with color-coded priority pins (no API key required) |
| **Analytics Charts** | Chart.js | Category distribution donut chart and resolution progression bar chart |
| **CSS & Design** | Tailwind CSS (CDN) | Modern civic-tech aesthetic, accessible color contrast, zero build step |
| **AI Integration** | Google GenAI SDK (`gemini-2.5-flash`) | Multimodal analysis with timeout enforcement and offline rule fallback |

---

## ⚡ 5. Local Setup Guide (Simple Language for Beginners)

### Step 1: Open Terminal & Navigate to Project
```powershell
git clone https://github.com/YOUR-USERNAME/CivicResolve.git
cd CivicResolve.gemini\antigravity\scratch\civicresolve
```

### Step 2: Install Dependencies
```powershell
pip install -r requirements.txt
```
*What this does: Downloads Flask, Flask-WTF, Flask-Limiter, Pillow, and Gunicorn to run the application.*

### Step 3: Run the Server
```powershell
python app.py
```
*What this does: Starts the web server on port 5000 (or the port specified by `$PORT`).*

### Step 4: Open in Your Browser
Open your browser and visit:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## ⚙️ 6. Environment Variables Table

| Variable | Description | Default | Production Note |
|---|---|---|---|
| `SECRET_KEY` | Cryptographic secret for session signing & CSRF protection | `civicresolve-super-secret-key-...` | Must be a random 32-byte hex string in production. |
| `ADMIN_USERNAME` | Username for municipal staff portal | `admin` | Set to your administrative team account name. |
| `ADMIN_PASSWORD` | Password for municipal staff portal | `admin123` | Hashed automatically with scrypt on startup. |
| `ADMIN_PASSWORD_HASH` | Optional: pre-computed password hash | `None` | Use to store pre-hashed credentials. |
| `GEMINI_API_KEY` | Google Gemini API key for multimodal classification | *(Empty)* | Leave empty for 100% offline Demo Mode. |
| `PORT` | Container HTTP listen port | `5000` | Google Cloud Run automatically injects `PORT=8080`. |
| `SESSION_COOKIE_SECURE`| Enforces HTTPS-only cookies | `False` | Set to `True` on production Cloud Run. |
| `DATABASE_PATH` | Path to SQLite database file | `civicresolve.db` | Auto-seeds 12 Coimbatore complaints if empty. |

---

## 🧪 7. How to Run Tests

The test suite covers classifier accuracy, reporting flows, input validation failures, admin route protection, and health checks.

Install development test dependencies:
```powershell
pip install -r requirements-dev.txt
```

Run all 37 tests via pytest:
```powershell
python -m pytest -v
```

Expected output:
```
tests/test_admin.py::test_admin_route_protected_redirects_unauthenticated PASSED [ 24%]
tests/test_admin.py::test_admin_login_success PASSED                     [ 27%]
tests/test_admin.py::test_admin_login_invalid_password_rejected PASSED   [ 29%]
tests/test_admin.py::test_admin_status_update_action PASSED              [ 32%]
tests/test_admin.py::test_admin_override_action PASSED                   [ 35%]
tests/test_admin.py::test_admin_rerun_ai_action PASSED                   [ 37%]
tests/test_admin.py::test_unauthenticated_api_status_update_blocked PASSED [ 40%]
tests/test_api.py::test_health_check_endpoint PASSED                     [ 43%]
tests/test_api.py::test_api_stats_endpoint PASSED                        [ 45%]
tests/test_api.py::test_api_complaints_endpoint PASSED                   [ 48%]
tests/test_citizen_flow.py::test_homepage_loads PASSED                   [ 51%]
tests/test_citizen_flow.py::test_report_form_page_loads PASSED           [ 54%]
tests/test_citizen_flow.py::test_valid_complaint_submission PASSED       [ 56%]
tests/test_citizen_flow.py::test_validation_empty_title_fails PASSED     [ 59%]
tests/test_citizen_flow.py::test_validation_short_description_fails PASSED [ 62%]
tests/test_citizen_flow.py::test_validation_empty_location_fails PASSED  [ 64%]
tests/test_citizen_flow.py::test_validation_invalid_latitude_fails PASSED [ 67%]
tests/test_citizen_flow.py::test_validation_invalid_file_type_fails PASSED [ 70%]
tests/test_citizen_flow.py::test_dashboard_pagination PASSED             [ 72%]
tests/test_classifier.py::test_critical_manhole_drainage PASSED          [ 75%]
tests/test_classifier.py::test_critical_burst_water_main PASSED          [ 78%]
tests/test_classifier.py::test_critical_sparking_electric_wire PASSED    [ 81%]
tests/test_classifier.py::test_high_priority_pothole PASSED              [ 83%]
tests/test_classifier.py::test_medium_priority_garbage PASSED            [ 86%]
tests/test_classifier.py::test_low_priority_dim_bulb PASSED              [ 89%]
tests/test_classifier.py::test_user_category_override PASSED             [ 91%]
tests/test_track.py::test_track_empty_view PASSED                        [ 94%]
tests/test_track.py::test_track_valid_code PASSED                        [ 97%]
tests/test_track.py::test_track_invalid_code_not_found PASSED            [100%]

============================= 37 passed in 6.50s ==============================
```

---

## ☁️ 8. Google Cloud Run Deployment

Deploy CivicResolve directly to Google Cloud Run with containerized auto-scaling:

### 1. Build and Test Container Locally
```bash
docker build -t civicresolve:latest .
docker run -p 8080:8080 -e PORT=8080 civicresolve:latest
```

### 2. Deploy to Google Cloud Run
```bash
# 1. Set your Google Cloud project ID
gcloud config set project YOUR_PROJECT_ID

# 2. Build image via Google Cloud Build
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/civicresolve

# 3. Deploy to Cloud Run (Serverless, auto-scales down to 0)
gcloud run deploy civicresolve \
    --image gcr.io/YOUR_PROJECT_ID/civicresolve \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars "SECRET_KEY=$(openssl rand -hex 32),SESSION_COOKIE_SECURE=True,ADMIN_USERNAME=admin,ADMIN_PASSWORD=change-me-in-production"
```

> **Cloud Run Ephemeral Storage Handling**: Cloud Run containers use ephemeral container storage. On cold starts, `app.py` automatically initializes the SQLite schema and seeds 12 realistic Coimbatore complaints via `database.init_db()` so the dashboard, map, and charts are live immediately.

---

## 🔒 9. Security Hardening Notes

1. **CSRF Protection**: All citizen reporting forms and admin authentication forms include Flask-WTF CSRF tokens. AJAX requests deliver CSRF tokens via `X-CSRFToken` request headers.
2. **Password Security**: Passwords are never stored in plaintext. Authentication verifies credentials via Werkzeug `check_password_hash` in constant time, preventing timing attacks.
3. **Strict Parameterized Queries**: All database operations use SQLite parameter substitution (`?`). Dynamic SQL string concatenation is strictly banned.
4. **Input Sanitization & Length Caps**:
   - Title: 3 to 150 characters.
   - Description: 10 to 3,000 characters.
   - Location: 3 to 250 characters.
   - Coordinates: Validated numeric floats (`-90 <= lat <= 90`, `-180 <= lon <= 180`).
5. **Secure File Uploads**:
   - Whitelist enforcement: `PNG`, `JPG`, `JPEG`, `WEBP` only.
   - Size limit: Capped at 5 MB via `MAX_CONTENT_LENGTH`.
   - File naming: `uuid.uuid4().hex` prepended to `secure_filename`.
   - Integrity: Pillow `Image.verify()` inspects header signatures to reject forged payloads.
6. **Rate Limiting**: Configured with Flask-Limiter (`15/min` on complaint reports, `5/min` on admin login attempts) to protect against spam and brute-force attacks.
7. **HTTP Security Headers**: Injected via Flask middleware:
   - `X-Content-Type-Options: nosniff`
   - `X-Frame-Options: SAMEORIGIN`
   - `Referrer-Policy: strict-origin-when-cross-origin`
   - `Content-Security-Policy`: Permits self-hosted resources and required CDNs.

---

## ♿ 10. Accessibility Notes (WCAG 2.1 AA Minded)

- **Semantic HTML Structure**: Built with `<header>`, `<nav>`, `<main>`, `<fieldset>`, `<legend>`, and `<footer>` landmarks. Exactly **one `<h1>` tag per page**.
- **Skip to Content Link**: A keyboard-accessible skip link (`#main-content`) is placed at the top of every page for screen reader and keyboard navigators.
- **Form Accessibility**: Every `<input>`, `<textarea>`, and `<select>` has an associated visible `<label for="...">`. Error instructions are linked with `aria-describedby`.
- **Dynamic Feedback (WCAG 4.1.3)**: Form submission overlays and flash toast notifications utilize `aria-live="polite"` and `aria-live="assertive"` regions.
- **Visual Contrast & Color Reliance**: Text meets or exceeds the **4.5:1 WCAG contrast ratio**. Status and priority badges combine color, text, and icons so color is never used as the sole conveyor of information (WCAG 1.4.1).
- **Responsive down to 320px**: Tested on small mobile viewports with flexible grid layouts, eliminating horizontal scrolling.

---

## 📸 11. Screenshots

### Home Page
![Home Page](screenshots/home.png)

### Report an Issue
![Report Form](screenshots/report.png)

### AI Classification Track
![AI Result](screenshots/track.png)

### Public Dashboard
![Dashboard](screenshots/dashboard.png)

### Admin Dashboard
![Admin Panel](screenshots/admin.png). Screenshots & Interface Previews

```
+-------------------------------------------------------------------------------+
| [CivicResolve]  Home  Report Issue  Track  Public Dashboard  Admin  [Staff]  |
|                                                                               |
|   Report Civic Issues in Seconds. Resolved with AI Precision.                 |
|   [ Enter Complaint ID (e.g. CR-2026-0001) ]   [ Track Status ]               |
|   [ Report an Issue Now ]    [ Public Dashboard ]                             |
+-------------------------------------------------------------------------------+
|  KPI Counters:  [12 Total]   [4 Reported]   [4 In Progress]   [4 Resolved]    |
+-------------------------------------------------------------------------------+
|  Workflow: [1. Report] -> [2. AI Triage] -> [3. Dept Routing] -> [4. Resolve] |
+-------------------------------------------------------------------------------+
```

*Screenshots Placeholders:*
- **Citizen Report Form (`/report`)**: Interactive GPS acquisition and 5 MB image preview.
- **AI Confirmation Screen (`/success/CR-2026-XXXX`)**: AI confidence score, priority justification, and assigned department.
- **Citizen Tracking Timeline (`/track`)**: 3-stage progress indicator with official staff remarks.
- **Public Map & Dashboard (`/dashboard`)**: Leaflet.js priority-coded pins and Chart.js category donut.
- **Staff Command Center (`/admin`)**: Priority-ranked complaints table with status update and override modals.

---

## 🎤 12. Demo Script (2–3 Minutes for Hackathon Presentation)

1. **Problem (0:00–0:40)**: Open the homepage (`/`). Explain that citizens don't know which municipal department handles their complaints, and city workers receive vague, unranked tickets. Point out the live KPI metrics and active AI badge.
2. **Citizen Submission (0:40–1:20)**: Click **Report Issue** (`/report`). Submit a ticket with title *"Deep crater-like pothole near bus stand"* and click **Use My Current Location**. Submit and highlight the AI triage animation.
3. **AI Triage & Tracking (1:20–2:00)**: Show the Confirmation screen (`/success/...`). Point out that AI assigned **High Priority** and routed it to the **Roads & Highways Department**. Click **Track Status** to show the 3-stage progress timeline.
4. **Staff Management (2:00–2:40)**: Navigate to `/admin` and log in (`admin` / `admin123`). Show that **Critical complaints (burst mains, open manholes) are sorted at the top**. Update a ticket's status to `In Progress` with a staff remark, and demonstrate the **Re-run AI Analysis** and **Override** tools.
5. **Conclusion (2:40–3:00)**: Highlight Cloud Run readiness, WCAG accessibility, CSRF protection, and 100% offline rule resilience.
