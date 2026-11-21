"""
Database layer for CivicResolve.
Provides SQLite connection management, schema initialization, sample data seeding,
database indexing, and parameterized query execution with pagination.
"""

import sqlite3
import os
import math
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from config import Config

def get_db_path(override_path: Optional[str] = None) -> str:
    """Returns database path from override, config, or default."""
    return override_path or Config.DB_PATH

def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Returns an active SQLite connection configured with Row factory and foreign keys."""
    conn = sqlite3.connect(get_db_path(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(db_path: Optional[str] = None) -> None:
    """
    Initializes database schema, creates performance indexes,
    and seeds sample data if empty (crucial for Cloud Run ephemeral storage).
    """
    path = get_db_path(db_path)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    conn = get_db_connection(path)
    cursor = conn.cursor()

    # 1. Complaints Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_code TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            location TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            category TEXT NOT NULL,
            priority TEXT NOT NULL,
            priority_reason TEXT,
            department TEXT NOT NULL,
            ai_summary TEXT,
            ai_confidence INTEGER DEFAULT 85,
            ai_mode TEXT DEFAULT 'Demo Mode',
            image_path TEXT,
            citizen_name TEXT,
            citizen_contact TEXT,
            status TEXT NOT NULL DEFAULT 'Reported',
            admin_remarks TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 2. Status History Audit Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS status_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            remark TEXT,
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (complaint_id) REFERENCES complaints (id) ON DELETE CASCADE
        );
    """)

    # 3. Performance Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_complaints_status ON complaints(status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_complaints_priority ON complaints(priority);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_complaints_category ON complaints(category);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_complaints_created ON complaints(created_at);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_complaint ON status_history(complaint_id);")

    conn.commit()

    # Seed initial dataset if table is newly created or empty
    cursor.execute("SELECT COUNT(*) FROM complaints")
    count = cursor.fetchone()[0]
    if count == 0:
        seed_sample_complaints(conn)

    conn.close()

def seed_sample_complaints(conn: sqlite3.Connection) -> None:
    """Seeds 12 realistic civic complaints around Coimbatore, Tamil Nadu."""
    cursor = conn.cursor()
    now = datetime.now()

    sample_data = [
        {
            "code": "CR-2026-0001",
            "title": "Deep crater-like pothole near Gandhipuram Central Bus Stand",
            "desc": "Heavy buses and two-wheelers are swerving abruptly to dodge a 2-foot wide pothole right at the bus stand entrance. Two motorbikers slipped yesterday during the evening drizzle.",
            "loc": "Cross Cut Road, Gandhipuram, Coimbatore",
            "lat": 11.0168, "lon": 76.9558,
            "cat": "Pothole", "prio": "High",
            "reason": "Severe vehicular hazard at a high-density transit hub causing recurring traffic disruptions and minor accidents.",
            "dept": "Roads & Highways Department",
            "summary": "Dangerous 2-foot pothole near bus terminal causing traffic obstruction and vehicle accidents.",
            "conf": 94, "mode": "Demo Mode",
            "img": None, "name": "Karthik Subramanian", "contact": "+91 98421 11234",
            "status": "In Progress",
            "remarks": "Road repair crew assigned with hot asphalt mix patch kit. Work scheduled for completion tonight.",
            "days_ago": 3,
            "history": [
                (3, "Reported", "Complaint registered via citizen portal with automated AI triage."),
                (1, "In Progress", "Road repair crew assigned with hot asphalt mix patch kit. Inspection completed.")
            ]
        },
        {
            "code": "CR-2026-0002",
            "title": "Overflowing commercial garbage bins emitting severe odor",
            "desc": "Public waste bins behind DB Road restaurants have not been cleared for 3 days. Waste is scattered onto the sidewalk and stray cattle and dogs are blocking pedestrians.",
            "loc": "DB Road, RS Puram, Coimbatore",
            "lat": 11.0090, "lon": 76.9470,
            "cat": "Garbage", "prio": "Medium",
            "reason": "Public health concern and pedestrian obstruction from uncollected commercial food waste.",
            "dept": "Solid Waste Management / Sanitation Department",
            "summary": "Overflowing commercial dumpster with pest infestation blocking pedestrian sidewalk.",
            "conf": 89, "mode": "Demo Mode",
            "img": None, "name": "Ananya Ramesh", "contact": "+91 97890 22345",
            "status": "Reported",
            "remarks": "Ticket queued for morning compactor truck pickup route.",
            "days_ago": 2,
            "history": [
                (2, "Reported", "Complaint submitted by local resident. Queued for sanitation dispatch.")
            ]
        },
        {
            "code": "CR-2026-0003",
            "title": "Major drinking water main burst flooding Avinashi Road",
            "desc": "High pressure 12-inch potable water pipeline has ruptured near PSG Tech. Drinking water is spewing 4 feet into the air and submerging one entire carriageway and adjacent basements.",
            "loc": "Avinashi Road, Peelamedu, Coimbatore",
            "lat": 11.0267, "lon": 77.0028,
            "cat": "Water Leakage", "prio": "Critical",
            "reason": "High-volume main line rupture causing active structural street flooding, severe drinking water loss, and traffic gridlock.",
            "dept": "Water Supply & Sewerage Board",
            "summary": "High-pressure potable water pipeline rupture causing severe roadway flooding and property inundation.",
            "conf": 98, "mode": "Demo Mode",
            "img": None, "name": "Dr. Senthil Kumar", "contact": "+91 94432 33456",
            "status": "In Progress",
            "remarks": "Emergency isolation valve shut off by TWAD maintenance team. Excavator deployed for pipe sleeve replacement.",
            "days_ago": 1,
            "history": [
                (1, "Reported", "Urgent citizen alert recorded. Automatic AI flagged critical due to main line burst."),
                (0.5, "In Progress", "TWAD emergency squad arrived at site. Water supply temporarily rerouted; welding in progress.")
            ]
        },
        {
            "code": "CR-2026-0004",
            "title": "Missing concrete manhole cover adjacent to primary school",
            "desc": "A stormwater drainage manhole cover broke under a heavy truck and fell in. It is completely open on the school pedestrian route on NSR Road with zero barricades.",
            "loc": "NSR Road, Saibaba Colony, Coimbatore",
            "lat": 11.0315, "lon": 76.9442,
            "cat": "Drainage", "prio": "Critical",
            "reason": "Fatal fall hazard next to an elementary school without physical safety barriers.",
            "dept": "Storm Water Drain Department",
            "summary": "Uncovered open manhole chamber on school walking route presenting imminent fall hazard.",
            "conf": 97, "mode": "Demo Mode",
            "img": None, "name": "Meenakshi Sundaram", "contact": "+91 98940 44567",
            "status": "Reported",
            "remarks": "Red barricade cones placed temporarily. Heavy-duty SFRC cover dispatched from central depot.",
            "days_ago": 1,
            "history": [
                (1, "Reported", "Complaint received. Immediate safety alert dispatched to ward supervisor.")
            ]
        },
        {
            "code": "CR-2026-0005",
            "title": "Sparking damaged electric pole with hanging bare cables",
            "desc": "A truck scraped a street pole last night. Loose overhead power cables are dangling at waist height and sparking intermittently near the vegetable market entrance.",
            "loc": "Bypass Road, Ukkadam, Coimbatore",
            "lat": 10.9880, "lon": 76.9622,
            "cat": "Streetlight", "prio": "Critical",
            "reason": "Live exposed electrical wires posing immediate life-threatening electrocution risk in crowded marketplace.",
            "dept": "Electricity Department / Street Lighting Division",
            "summary": "Damaged electric utility pole with live sparking cables dangling in crowded public market.",
            "conf": 96, "mode": "Demo Mode",
            "img": None, "name": "Mohammed Farooq", "contact": "+91 98430 55678",
            "status": "In Progress",
            "remarks": "TANGEDCO line supervisor isolated local feeder circuit. Linemen rewiring pole and overhead insulation.",
            "days_ago": 2,
            "history": [
                (2, "Reported", "Emergency electrical hazard reported by market merchant association."),
                (1, "In Progress", "TANGEDCO team isolated feeder. Crane truck on site to realign bent pole.")
            ]
        },
        {
            "code": "CR-2026-0006",
            "title": "Asphalt cave-in and broken road surface after rain",
            "desc": "Substantial section of the left lane has sunken 8 inches down creating sharp asphalt ridges. Cars are forced into oncoming traffic lane.",
            "loc": "Trichy Road, Singanallur, Coimbatore",
            "lat": 10.9985, "lon": 77.0210,
            "cat": "Road Damage", "prio": "High",
            "reason": "Significant road subsidence forcing vehicles into opposing traffic lanes on major arterial highway.",
            "dept": "Roads & Highways Department",
            "summary": "Sunken asphalt pavement on Trichy Road forcing dangerous oncoming lane diversions.",
            "conf": 91, "mode": "Demo Mode",
            "img": None, "name": "Rajesh Kannan", "contact": "+91 97500 66789",
            "status": "Reported",
            "remarks": "Engineering survey team scheduled to inspect road base layer tomorrow morning.",
            "days_ago": 3,
            "history": [
                (3, "Reported", "Issue logged by commuter. AI classified as High priority road damage.")
            ]
        },
        {
            "code": "CR-2026-0007",
            "title": "Complete streetlight blackout for five consecutive blocks",
            "desc": "Eight consecutive streetlights along Big Bazaar Street are completely non-functional. The entire commercial corridor becomes pitch dark after 9 PM.",
            "loc": "Big Bazaar Street, Town Hall, Coimbatore",
            "lat": 10.9950, "lon": 76.9605,
            "cat": "Streetlight", "prio": "Medium",
            "reason": "Multi-block commercial blackout increasing risk of night crimes and pedestrian trip accidents.",
            "dept": "Electricity Department / Street Lighting Division",
            "summary": "Multiple contiguous streetlamps out of service creating darkness across market stretch.",
            "conf": 88, "mode": "Demo Mode",
            "img": None, "name": "Venkatesh Babu", "contact": "+91 98650 77890",
            "status": "Resolved",
            "remarks": "Blown underground junction fuse replaced. All 8 LED luminaires tested and functional.",
            "days_ago": 5,
            "history": [
                (5, "Reported", "Merchant complaints logged regarding multi-pole outage."),
                (3, "In Progress", "Cable fault detected in feeder junction box near clock tower."),
                (1, "Resolved", "Underground cable spliced and replaced. All lights illuminated and verified.")
            ]
        },
        {
            "code": "CR-2026-0008",
            "title": "Stormwater drain blocked by silt causing stagnant pool",
            "desc": "Heavy monsoon silt and plastic rubbish have clogged the roadside canal. Stagnant foul water is breeding mosquitoes outside residential apartments.",
            "loc": "Sathy Road, Ganapathy, Coimbatore",
            "lat": 11.0410, "lon": 76.9780,
            "cat": "Drainage", "prio": "Medium",
            "reason": "Stagnant drainage water creating sanitary hazard and vector breeding site near high-density residences.",
            "dept": "Storm Water Drain Department",
            "summary": "Clogged stormwater channel with plastic blockage generating stagnant mosquito breeding water.",
            "conf": 87, "mode": "Demo Mode",
            "img": None, "name": "Lakshmi Priya", "contact": "+91 99440 88901",
            "status": "Resolved",
            "remarks": "Sanitation excavator desilted 150 meters of concrete culvert. Water flowing freely now.",
            "days_ago": 6,
            "history": [
                (6, "Reported", "Resident association reported standing water and stench."),
                (4, "In Progress", "Backhoe loader deployed to clear sediment blockages."),
                (2, "Resolved", "Drainage channel fully desilted and treated with anti-larval spray.")
            ]
        },
        {
            "code": "CR-2026-0009",
            "title": "Dim flickering fixture on southern jogging perimeter",
            "desc": "One streetlight head on the southern inner path is flickering dimly like a strobe light. Walking path is still partially lit by adjacent lights.",
            "loc": "Thomas Park, Race Course, Coimbatore",
            "lat": 11.0025, "lon": 76.9760,
            "cat": "Streetlight", "prio": "Low",
            "reason": "Localized lighting fixture defect on pedestrian path with adequate ambient illumination from neighboring poles.",
            "dept": "Electricity Department / Street Lighting Division",
            "summary": "Single flickering LED streetlight on park jogging track with minor visibility impact.",
            "conf": 85, "mode": "Demo Mode",
            "img": None, "name": "Gautham Balaji", "contact": "+91 98425 99012",
            "status": "Resolved",
            "remarks": "Faulty LED driver module swapped out. Restored to full brightness.",
            "days_ago": 7,
            "history": [
                (7, "Reported", "Citizen note received from morning walker."),
                (5, "In Progress", "Maintenance electrician dispatched during daytime maintenance shift."),
                (3, "Resolved", "Replaced defective 45W driver module and cleaned optical lens.")
            ]
        },
        {
            "code": "CR-2026-0010",
            "title": "Construction concrete rubble dumped along road shoulder",
            "desc": "Unidentified contractor dumped 2 truckloads of brick mortar and broken tiles along the bus route shoulder, forcing pedestrians into fast-moving vehicle lanes.",
            "loc": "Trichy Road, Ramanathapuram, Coimbatore",
            "lat": 10.9930, "lon": 76.9890,
            "cat": "Garbage", "prio": "High",
            "reason": "Massive debris obstructing vehicle shoulder and endangering pedestrian traffic on a high-speed corridor.",
            "dept": "Solid Waste Management / Sanitation Department",
            "summary": "Unauthorized construction debris dumping occupying roadway shoulder.",
            "conf": 90, "mode": "Demo Mode",
            "img": None, "name": "Deepak Narayanan", "contact": "+91 98945 10123",
            "status": "In Progress",
            "remarks": "Notice served on site owner. JCB loader and 10-wheeler dumper mobilized to clear debris.",
            "days_ago": 4,
            "history": [
                (4, "Reported", "Citizen submitted report with photos of illegal dump pile."),
                (2, "In Progress", "Sanitation enforcement issued fine and heavy machinery scheduled for removal.")
            ]
        },
        {
            "code": "CR-2026-0011",
            "title": "Slow dripping pipe connection at public distribution tap",
            "desc": "Minor water seepage from the gate valve flange at public corner drinking tap. Slow drip forming small puddle on curb.",
            "loc": "IT Corridor, Saravanampatti, Coimbatore",
            "lat": 11.0805, "lon": 76.9955,
            "cat": "Water Leakage", "prio": "Low",
            "reason": "Low pressure valve gasket weep with minimal resource loss and zero structural hazard.",
            "dept": "Water Supply & Sewerage Board",
            "summary": "Low-rate flange leakage at municipal distribution tap.",
            "conf": 86, "mode": "Demo Mode",
            "img": None, "name": "Divya Krishnan", "contact": "+91 97860 11234",
            "status": "Reported",
            "remarks": "Assigned to ward plumbing maintenance team for routine washer replacement.",
            "days_ago": 2,
            "history": [
                (2, "Reported", "Citizen complaint registered for dripping municipal tap.")
            ]
        },
        {
            "code": "CR-2026-0012",
            "title": "Unpaved utility trench left open across pedestrian pathway",
            "desc": "Contractors finished underground cable laying 2 weeks ago but left a 3-foot wide unfinished dirt trench across the sidewalk without re-paving.",
            "loc": "Avinashi Road, Hopes College, Coimbatore",
            "lat": 11.0345, "lon": 77.0135,
            "cat": "Road Damage", "prio": "High",
            "reason": "Unfilled excavation across pedestrian corridor causing tripping hazards and wheelchair inaccessibility.",
            "dept": "Roads & Highways Department",
            "summary": "Un-reinstated utility excavation trench across pedestrian walkway.",
            "conf": 92, "mode": "Demo Mode",
            "img": None, "name": "Prasanth Vijayan", "contact": "+91 94420 12345",
            "status": "Resolved",
            "remarks": "Contractor summoned; trench backfilled with wet gravel and cold rolled asphalt.",
            "days_ago": 8,
            "history": [
                (8, "Reported", "Student complaint recorded regarding unpaved walking trench."),
                (5, "In Progress", "Highway engineer inspected site and issued stop-work notice to utility vendor."),
                (2, "Resolved", "Asphalt leveling and compaction completed. Pathway restored.")
            ]
        }
    ]

    for item in sample_data:
        created_dt = now - timedelta(days=item["days_ago"])
        created_str = created_dt.strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO complaints (
                complaint_code, title, description, location, latitude, longitude,
                category, priority, priority_reason, department, ai_summary,
                ai_confidence, ai_mode, image_path, citizen_name, citizen_contact,
                status, admin_remarks, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item["code"], item["title"], item["desc"], item["loc"], item["lat"], item["lon"],
            item["cat"], item["prio"], item["reason"], item["dept"], item["summary"],
            item["conf"], item["mode"], item["img"], item["name"], item["contact"],
            item["status"], item["remarks"], created_str, created_str
        ))
        complaint_id = cursor.lastrowid

        for h in item["history"]:
            h_dt = now - timedelta(days=h[0])
            cursor.execute("""
                INSERT INTO status_history (complaint_id, status, remark, changed_at)
                VALUES (?, ?, ?, ?)
            """, (complaint_id, h[1], h[2], h_dt.strftime("%Y-%m-%d %H:%M:%S")))

    conn.commit()

def generate_complaint_code(db_path: Optional[str] = None) -> str:
    """Generates the next sequential unique complaint code (e.g. CR-2026-0013)."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(id) FROM complaints")
    row = cursor.fetchone()
    max_id = row[0] if (row and row[0] is not None) else 0
    conn.close()
    next_num = max_id + 1
    current_year = datetime.now().year
    return f"CR-{current_year}-{next_num:04d}"

def get_all_complaints(
    status: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    search: Optional[str] = None,
    sort_priority: bool = False,
    page: int = 1,
    per_page: int = 10,
    db_path: Optional[str] = None
) -> Tuple[List[sqlite3.Row], int, int, int]:
    """
    Fetches complaints with optional filtering, sorting, and pagination.
    Returns: (complaints, total_count, total_pages, current_page)
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    base_where = "WHERE 1=1"
    params: List[Any] = []

    if status and status != "All":
        base_where += " AND status = ?"
        params.append(status)

    if category and category != "All":
        base_where += " AND category = ?"
        params.append(category)

    if priority and priority != "All":
        base_where += " AND priority = ?"
        params.append(priority)

    if search:
        search_pattern = f"%{search.strip()}%"
        base_where += " AND (complaint_code LIKE ? OR title LIKE ? OR description LIKE ? OR location LIKE ? OR citizen_name LIKE ?)"
        params.extend([search_pattern, search_pattern, search_pattern, search_pattern, search_pattern])

    # Count total matching rows
    count_query = f"SELECT COUNT(*) FROM complaints {base_where}"
    cursor.execute(count_query, params)
    total_count = cursor.fetchone()[0]

    # Calculate pagination
    per_page = max(1, per_page)
    total_pages = max(1, math.ceil(total_count / per_page))
    page = max(1, min(page, total_pages))
    offset = (page - 1) * per_page

    # Order clause
    if sort_priority:
        order_clause = """
            ORDER BY 
            CASE priority
                WHEN 'Critical' THEN 1
                WHEN 'High' THEN 2
                WHEN 'Medium' THEN 3
                WHEN 'Low' THEN 4
                ELSE 5
            END ASC,
            created_at DESC
        """
    else:
        order_clause = " ORDER BY created_at DESC"

    query = f"SELECT * FROM complaints {base_where} {order_clause} LIMIT ? OFFSET ?"
    query_params = list(params) + [per_page, offset]

    cursor.execute(query, query_params)
    rows = cursor.fetchall()
    conn.close()

    return rows, total_count, total_pages, page

def get_complaint_by_id(complaint_id: int, db_path: Optional[str] = None) -> Optional[sqlite3.Row]:
    """Fetches a single complaint by its primary integer key."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM complaints WHERE id = ?", (complaint_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def get_complaint_by_code(complaint_code: str, db_path: Optional[str] = None) -> Optional[sqlite3.Row]:
    """Fetches a single complaint by unique code (case-insensitive)."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM complaints WHERE UPPER(complaint_code) = UPPER(?)", (complaint_code.strip(),))
    row = cursor.fetchone()
    conn.close()
    return row

def get_status_history(complaint_id: int, db_path: Optional[str] = None) -> List[sqlite3.Row]:
    """Returns chronological timeline status records for a complaint."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM status_history WHERE complaint_id = ? ORDER BY changed_at ASC", (complaint_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def insert_complaint(data: Dict[str, Any], db_path: Optional[str] = None) -> Tuple[int, str]:
    """Inserts a new complaint using parameterized query and initializes status history."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    complaint_code = generate_complaint_code(db_path)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO complaints (
            complaint_code, title, description, location, latitude, longitude,
            category, priority, priority_reason, department, ai_summary,
            ai_confidence, ai_mode, image_path, citizen_name, citizen_contact,
            status, admin_remarks, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        complaint_code,
        data["title"],
        data["description"],
        data["location"],
        data.get("latitude"),
        data.get("longitude"),
        data["category"],
        data["priority"],
        data.get("priority_reason", ""),
        data["department"],
        data.get("ai_summary", ""),
        data.get("ai_confidence", 85),
        data.get("ai_mode", "Demo Mode"),
        data.get("image_path"),
        data.get("citizen_name", "Anonymous Citizen"),
        data.get("citizen_contact", ""),
        "Reported",
        "Complaint received and queued for department review.",
        now_str,
        now_str
    ))
    complaint_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO status_history (complaint_id, status, remark, changed_at)
        VALUES (?, ?, ?, ?)
    """, (complaint_id, "Reported", "Complaint submitted via citizen portal with automated AI triage.", now_str))

    conn.commit()
    conn.close()
    return complaint_id, complaint_code

def update_complaint_status(complaint_id: int, new_status: str, remark: Optional[str] = None, db_path: Optional[str] = None) -> None:
    """Updates complaint status, logs remark in audit history, and updates timestamp."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    clean_remark = remark or f"Status changed to {new_status}"

    cursor.execute("""
        UPDATE complaints 
        SET status = ?, admin_remarks = ?, updated_at = ?
        WHERE id = ?
    """, (new_status, clean_remark, now_str, complaint_id))

    cursor.execute("""
        INSERT INTO status_history (complaint_id, status, remark, changed_at)
        VALUES (?, ?, ?, ?)
    """, (complaint_id, new_status, clean_remark, now_str))

    conn.commit()
    conn.close()

def update_complaint_details(
    complaint_id: int,
    category: str,
    priority: str,
    department: str,
    priority_reason: Optional[str] = None,
    db_path: Optional[str] = None
) -> None:
    """Allows admin override of category, priority, department, and priority reason."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        UPDATE complaints 
        SET category = ?, priority = ?, department = ?, 
            priority_reason = COALESCE(?, priority_reason), updated_at = ?
        WHERE id = ?
    """, (category, priority, department, priority_reason, now_str, complaint_id))

    cursor.execute("""
        INSERT INTO status_history (complaint_id, status, remark, changed_at)
        VALUES (?, (SELECT status FROM complaints WHERE id = ?), ?, ?)
    """, (complaint_id, complaint_id, f"Admin updated assignment: {category} ({priority}) -> {department}", now_str))

    conn.commit()
    conn.close()

def update_complaint_ai(complaint_id: int, ai_result: Dict[str, Any], db_path: Optional[str] = None) -> None:
    """Updates a complaint with fresh AI analysis output."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        UPDATE complaints
        SET category = ?, priority = ?, priority_reason = ?, department = ?,
            ai_summary = ?, ai_confidence = ?, ai_mode = ?, updated_at = ?
        WHERE id = ?
    """, (
        ai_result["category"],
        ai_result["priority"],
        ai_result.get("priority_reason", ""),
        ai_result["department"],
        ai_result.get("summary", ""),
        ai_result.get("confidence", 85),
        ai_result.get("ai_mode", "Demo Mode"),
        now_str,
        complaint_id
    ))

    cursor.execute("""
        INSERT INTO status_history (complaint_id, status, remark, changed_at)
        VALUES (?, (SELECT status FROM complaints WHERE id = ?), ?, ?)
    """, (
        complaint_id,
        complaint_id,
        f"AI re-analysis executed ({ai_result.get('ai_mode', 'AI')}) - Category: {ai_result['category']}, Priority: {ai_result['priority']}",
        now_str
    ))

    conn.commit()
    conn.close()

def delete_complaint(complaint_id: int, db_path: Optional[str] = None) -> None:
    """Deletes a complaint and its status history."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM status_history WHERE complaint_id = ?", (complaint_id,))
    cursor.execute("DELETE FROM complaints WHERE id = ?", (complaint_id,))
    conn.commit()
    conn.close()

def get_dashboard_stats(db_path: Optional[str] = None) -> Dict[str, Any]:
    """Calculates summary metrics, category breakdown, and status counts."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM complaints")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM complaints WHERE status = 'Reported'")
    reported = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM complaints WHERE status = 'In Progress'")
    in_progress = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM complaints WHERE status = 'Resolved'")
    resolved = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM complaints WHERE priority = 'Critical'")
    critical = cursor.fetchone()[0]

    cursor.execute("""
        SELECT category, COUNT(*) as count 
        FROM complaints 
        GROUP BY category 
        ORDER BY count DESC
    """)
    category_counts = {row["category"]: row["count"] for row in cursor.fetchall()}

    cursor.execute("""
        SELECT status, COUNT(*) as count 
        FROM complaints 
        GROUP BY status
    """)
    status_counts = {row["status"]: row["count"] for row in cursor.fetchall()}

    cursor.execute("""
        SELECT priority, COUNT(*) as count 
        FROM complaints 
        GROUP BY priority
    """)
    priority_counts = {row["priority"]: row["count"] for row in cursor.fetchall()}

    conn.close()

    return {
        "total": total,
        "reported": reported,
        "in_progress": in_progress,
        "resolved": resolved,
        "critical": critical,
        "category_counts": category_counts,
        "status_counts": status_counts,
        "priority_counts": priority_counts
    }
