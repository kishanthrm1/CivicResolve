"""
AI Triage Service for CivicResolve.
Provides dual-mode classification:
- Mode A (Gemini 2.5 Flash): Multimodal analysis with timeout enforcement.
- Mode B (Demo Mode): Offline smart rule-based keyword & risk classifier.
Fail-safe fallback: If Gemini fails for any reason (network, quota, timeout, bad key),
it seamlessly falls back to Demo Mode without interrupting the user.
"""

import os
import json
import re
import logging
from typing import Optional, Dict, Any, List
from config import Config

logger = logging.getLogger(__name__)

# Standard Department Mapping
DEPARTMENT_MAP: Dict[str, str] = {
    "Pothole": "Roads & Highways Department",
    "Road Damage": "Roads & Highways Department",
    "Garbage": "Solid Waste Management / Sanitation Department",
    "Streetlight": "Electricity Department / Street Lighting Division",
    "Water Leakage": "Water Supply & Sewerage Board",
    "Drainage": "Storm Water Drain Department",
    "Other": "General Municipal Administration"
}

VALID_CATEGORIES: List[str] = [
    "Pothole",
    "Garbage",
    "Streetlight",
    "Water Leakage",
    "Road Damage",
    "Drainage",
    "Other"
]

VALID_PRIORITIES: List[str] = ["Critical", "High", "Medium", "Low"]

# Execution timeout for cloud Gemini API calls (in seconds)
GEMINI_TIMEOUT_SECONDS = 7.0

def analyze_complaint(
    title: str,
    description: str,
    location: str = "",
    user_selected_category: Optional[str] = None,
    image_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main triage entry point.
    Attempts Gemini 2.5 Flash classification if GEMINI_API_KEY is present;
    otherwise or upon failure/timeout, falls back to offline Demo Mode.
    """
    api_key = Config.GEMINI_API_KEY

    if api_key:
        try:
            logger.info("Attempting AI classification using Google Gemini 2.5 Flash...")
            gemini_result = _classify_with_gemini(
                api_key=api_key,
                title=title,
                description=description,
                location=location,
                user_selected_category=user_selected_category,
                image_path=image_path
            )
            if gemini_result:
                gemini_result["ai_mode"] = "Gemini"
                return gemini_result
        except Exception as e:
            logger.warning("Gemini API call failed (%s). Falling back to offline Demo Mode.", e)

    # Fallback to Demo Mode (rule-based)
    demo_result = _classify_with_demo_rules(
        title=title,
        description=description,
        location=location,
        user_selected_category=user_selected_category,
        image_path=image_path
    )
    demo_result["ai_mode"] = "Demo Mode"
    return demo_result

def _classify_with_gemini(
    api_key: str,
    title: str,
    description: str,
    location: str,
    user_selected_category: Optional[str],
    image_path: Optional[str]
) -> Optional[Dict[str, Any]]:
    """Executes multimodal classification via Gemini 2.5 Flash with timeout protection."""
    try:
        from google import genai
        from google.genai import types
        from PIL import Image

        # Initialize client with timeout config
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=int(GEMINI_TIMEOUT_SECONDS * 1000))
        )

        prompt = f"""
You are the AI triage engine for CivicResolve, an urban civic issue management platform.
Analyze the following citizen complaint and return ONLY a valid JSON object matching the exact specification.

Citizen Complaint:
- Title: {title}
- Description: {description}
- Location: {location}
- User Suggested Category: {user_selected_category or "Auto-detect with AI"}

Guidelines for Classification:
1. Category must be one of:
   - Pothole
   - Garbage
   - Streetlight
   - Water Leakage
   - Road Damage
   - Drainage
   - Other

2. Priority Guidelines:
   - Critical: Imminent threat to human life or health (e.g., open uncovered manhole, high pressure burst water main, exposed sparking electrical wires, hazard next to school/hospital/pedestrian crossing).
   - High: Severe disruption to traffic or public mobility (e.g., large deep potholes on main roads/highways, major road subsidence/cave-in, huge debris blocking roadway).
   - Medium: Moderate public nuisance or sanitation issue (e.g., overflowing garbage dumpsters, clogged drain creating stagnant water, multi-street lamp outage).
   - Low: Minor localized aesthetic or low-risk issue (e.g., single dim or flickering bulb on walkway, slow dripping municipal tap).

3. Department Mapping:
   - Pothole / Road Damage -> "Roads & Highways Department"
   - Garbage -> "Solid Waste Management / Sanitation Department"
   - Streetlight -> "Electricity Department / Street Lighting Division"
   - Water Leakage -> "Water Supply & Sewerage Board"
   - Drainage -> "Storm Water Drain Department"
   - Other -> "General Municipal Administration"

JSON Output Format (Strictly return ONLY JSON, no markdown fences):
{{
  "category": "Pothole | Garbage | Streetlight | Water Leakage | Road Damage | Drainage | Other",
  "priority": "Critical | High | Medium | Low",
  "priority_reason": "One clear sentence explaining the risk and urgency",
  "department": "Name of the recommended department",
  "summary": "A concise one-line summary of the issue",
  "confidence": 92
}}
"""

        contents: List[Any] = [prompt]

        if image_path and os.path.exists(image_path):
            try:
                img = Image.open(image_path)
                contents.append(img)
            except Exception as img_err:
                logger.warning("Could not load image for Gemini: %s", img_err)

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents
        )

        response_text = response.text.strip() if response and response.text else ""
        if not response_text:
            return None

        # Strip markdown fences
        if response_text.startswith("```"):
            response_text = re.sub(r"^```(?:json)?\s*", "", response_text)
            response_text = re.sub(r"\s*```$", "", response_text)

        parsed = json.loads(response_text)

        # Sanitize and validate fields
        category = parsed.get("category", "Other")
        if category not in VALID_CATEGORIES:
            category = "Other"

        priority = parsed.get("priority", "Medium")
        if priority not in VALID_PRIORITIES:
            priority = "Medium"

        department = parsed.get("department") or DEPARTMENT_MAP.get(category, "General Municipal Administration")
        confidence = int(parsed.get("confidence", 90))
        confidence = max(60, min(99, confidence))

        return {
            "category": category,
            "priority": priority,
            "priority_reason": parsed.get("priority_reason", f"Assessed as {priority} priority based on public impact."),
            "department": department,
            "summary": parsed.get("summary", title[:60]),
            "confidence": confidence
        }

    except Exception as e:
        logger.error("Error inside _classify_with_gemini: %s", e)
        return None

def _classify_with_demo_rules(
    title: str,
    description: str,
    location: str,
    user_selected_category: Optional[str],
    image_path: Optional[str]
) -> Dict[str, Any]:
    """
    Intelligent offline rule-based classification engine.
    Uses weighted keyword analysis, contextual risk detection, and department routing.
    """
    text = f"{title} {description} {location}".lower()

    preset_cat: Optional[str] = None
    if user_selected_category and user_selected_category != "Auto-detect with AI" and user_selected_category in VALID_CATEGORIES:
        preset_cat = user_selected_category

    # Keyword scoring dictionaries
    category_keywords: Dict[str, List[str]] = {
        "Pothole": ["pothole", "potholes", "crater", "road ditch", "pit on road", "asphalt hole", "wheel rim damage"],
        "Road Damage": ["road broken", "cave-in", "subsidence", "sunken road", "cracks on road", "gravel", "pavement broken", "uneven road", "asphalt cracked", "unpaved trench", "sidewalk broken", "footpath damaged"],
        "Garbage": ["garbage", "waste", "trash", "rubbish", "dump", "bin", "bins", "debris", "smell", "stench", "rotting", "litter", "compactor", "refuse", "dumpster"],
        "Streetlight": ["streetlight", "street light", "lamp", "lamps", "bulb", "dark", "pitch dark", "blackout", "illumination", "flicker", "flickering", "pole", "light pole"],
        "Water Leakage": ["leak", "leakage", "pipe", "pipeline", "burst pipe", "pipe burst", "potable water", "drinking water", "water line", "valve", "spewing water", "spraying water"],
        "Drainage": ["drain", "drainage", "sewage", "sewer", "manhole", "gutter", "stormwater", "culvert", "sullage", "overflowing sewage", "clogged drain", "drain block"]
    }

    # Calculate scores
    scores: Dict[str, int] = {}
    for cat, kws in category_keywords.items():
        score = 0
        for kw in kws:
            if kw in text:
                score += 3 if kw in title.lower() else 1
        scores[cat] = score

    # Select best matching category
    best_category = preset_cat
    if not best_category:
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_cat, top_score = sorted_scores[0]
        if top_score > 0:
            best_category = top_cat
        else:
            best_category = "Other"

    # Priority determination
    critical_triggers: List[str] = [
        "open manhole", "manhole open", "missing manhole cover", "uncovered manhole",
        "burst water main", "pipe burst", "burst pipe", "pipeline ruptured",
        "exposed wire", "exposed wires", "live wire", "sparking", "dangling wire", "hanging wire",
        "school", "elementary school", "kindergarten", "hospital", "clinic",
        "life threatening", "fatal", "electrocution", "severe flooding", "emergency", "collapse"
    ]

    high_triggers: List[str] = [
        "main road", "highway", "arterial", "bus stand", "bus stop", "crater", "sinkhole",
        "heavy traffic", "swerving", "accident", "tripping", "blocking road", "road subsidence",
        "cave-in", "large pothole", "debris blocking", "high speed"
    ]

    low_triggers: List[str] = [
        "single dim", "dim light", "flickering bulb", "minor leak", "slow drip", "dripping tap",
        "aesthetic", "small puddle", "seepage", "faint", "jogging track"
    ]

    priority = "Medium"
    priority_reason = ""

    # Check critical triggers first
    matched_critical = [trig for trig in critical_triggers if trig in text]
    if matched_critical:
        priority = "Critical"
        if any(w in text for w in ["school", "hospital"]):
            priority_reason = f"Immediate severe safety hazard ({matched_critical[0]}) adjacent to high-vulnerability public institutions."
        elif any(w in text for w in ["wire", "sparking", "electrocution"]):
            priority_reason = "Live electrical danger with acute risk of electrocution in a public access zone."
        elif any(w in text for w in ["manhole"]):
            priority_reason = "Open uncovered drainage chamber posing an imminent fatal fall hazard."
        elif any(w in text for w in ["burst", "water main"]):
            priority_reason = "High-pressure utility rupture causing rapid flood inundation and structural roadway damage."
        else:
            priority_reason = f"Emergency safety concern flagged due to '{matched_critical[0]}' requiring immediate department intervention."

    # Check high triggers
    elif any(trig in text for trig in high_triggers):
        priority = "High"
        if "pothole" in text or "crater" in text:
            priority_reason = "Deep pavement defect located on a critical transit corridor causing recurring vehicle swerving and collision hazards."
        elif "road" in text or "trench" in text:
            priority_reason = "Significant roadway displacement obstructing vehicular and pedestrian throughput."
        elif "garbage" in text or "debris" in text:
            priority_reason = "Heavy debris accumulation creating traffic impediments and sanitary escalation."
        else:
            priority_reason = "High-impact civic issue causing disruption to urban transport and public safety."

    # Check low triggers
    elif any(trig in text for trig in low_triggers):
        priority = "Low"
        if "light" in text or "bulb" in text:
            priority_reason = "Minor localized illumination fluctuation with adequate residual street visibility."
        elif "drip" in text or "leak" in text:
            priority_reason = "Low-rate localized utility seepage posing no structural threat."
        else:
            priority_reason = "Routine localized civic maintenance item with low public exposure."

    # Default medium
    else:
        priority = "Medium"
        priority_reason = f"Standard priority civic concern requiring planned remediation by the {DEPARTMENT_MAP.get(best_category, 'General Municipal Administration')}."

    department = DEPARTMENT_MAP.get(best_category, "General Municipal Administration")

    clean_title = title.strip()
    if len(clean_title) > 60:
        clean_title = clean_title[:57] + "..."
    summary = f"{best_category}: {clean_title}"

    cat_score = scores.get(best_category, 0)
    confidence = min(96, max(82, 80 + cat_score * 4))

    return {
        "category": best_category,
        "priority": priority,
        "priority_reason": priority_reason,
        "department": department,
        "summary": summary,
        "confidence": confidence
    }
