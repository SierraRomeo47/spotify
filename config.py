"""Configuration and constants for Sierra Romeo Editorial Intelligence Lab."""

from pathlib import Path

from dotenv import load_dotenv

# Paths — ROOT_DIR must be set before load_dotenv (Streamlit cwd may be parent folder)
ROOT_DIR = Path(__file__).resolve().parent

# Always load .env from project root, not the process working directory
load_dotenv(ROOT_DIR / ".env", override=True)
ASSETS_DIR = ROOT_DIR / "assets"
HOME_HERO_BACKGROUND = ASSETS_DIR / "home_hero_background.png"
OUTPUTS_DIR = ROOT_DIR / "outputs"
EXPORTIFY_PLAYLISTS_DIR = ROOT_DIR / "spotify_playlists"
MY_SPOTIFY_DATA_DIR = ROOT_DIR / "my_spotify_data"
SPOTIFY_ACCOUNT_DATA_DIR = MY_SPOTIFY_DATA_DIR / "Spotify Account Data"
DATA_DIR = ROOT_DIR / "data"
ENRICHMENT_CACHE_PATH = DATA_DIR / "enrichment_cache.json"
SITE_DATA_PATH = ROOT_DIR / "web" / "public" / "data" / "portfolio.json"

# Auto bootstrap on session start
AUTO_BOOTSTRAP_DATA = True
AUTO_ENRICH_GENRES = True
ENRICH_MAX_ARTISTS_BOOTSTRAP = 50
EXPORTIFY_CACHE_TTL_SEC = 3600

# Spotify OAuth
SPOTIFY_CACHE_PATH = str(ROOT_DIR / ".spotify_cache")
SCOPES = " ".join(
    [
        "user-top-read",
        "user-read-recently-played",
        "user-library-read",
        "playlist-read-private",
        "playlist-read-collaborative",
    ]
)

# Theme tokens (Spotify-inspired dark UI — not official Spotify branding)
BG = "#000000"
BG_ELEVATED = "#121212"
CARD = "#181818"
CARD_ELEVATED = "#282828"
ACCENT = "#1ed760"
ACCENT_RED = "#c41e3a"
ACCENT_GREEN = ACCENT  # alias for legacy imports
TEXT = "#ffffff"
MUTED = "#b3b3b3"

PROFILE_PILLS = [
    "MUSIC CULTURE",
    "EDITORIAL STRATEGY",
    "DATA-LED AUDIENCE INSIGHTS",
]
PROFILE_TAGLINE = "INTERNATIONAL & HIP-HOP EDITORIAL PORTFOLIO"

# Editorial playlist concepts (JD-aligned; club + India ↔ global hip-hop)
EDITORIAL_CONCEPTS = [
    "Breakout Watch: Pre-Mainstream",
    "Global Hip-Hop: India Entry Points",
    "Indian Hip-Hop Export Radar",
    "High-Energy Club Crossover",
    "Late Night Mumbai Flow",
]

PROFILE_ROLE_PILLS = [
    "CLUB & ELECTRONIC DISCOVERY",
    "INDIA ↔ GLOBAL HIP-HOP",
    "EDITORIAL PROGRAMMING",
]

MINIMAL_NAV = True

SEQUENCE_ROLES = [
    "Opener",
    "Early Build",
    "Momentum",
    "Peak",
    "Left-field Discovery",
    "Cooldown",
]

TIME_RANGES = ["short_term", "medium_term", "long_term"]
TIME_RANGE_LABELS = {
    "short_term": "Last 4 weeks",
    "medium_term": "Last 6 months",
    "long_term": "All time",
}

# Spotify account listening tenure (user-reported; for JD 6+ years framing)
SPOTIFY_MEMBER_SINCE_YEAR = 2017

# Artist scoring weights
SCORE_WEIGHTS = {
    "affinity": 0.35,
    "discovery": 0.25,
    "india": 0.15,
    "global": 0.15,
    "club": 0.10,
}

# Genre classification keywords (first match wins)
HIP_HOP_KEYWORDS = [
    "rap",
    "hip hop",
    "hip-hop",
    "trap",
    "drill",
    "grime",
    "desi hip hop",
    "indian hip hop",
    "punjabi hip hop",
    "underground hip hop",
    "gangsta rap",
    "conscious hip hop",
]

INDIA_KEYWORDS = [
    "indian",
    "desi",
    "hindi",
    "punjabi",
    "tamil",
    "telugu",
    "bollywood",
    "bhangra",
    "filmi",
]

INTERNATIONAL_BUCKETS = {
    "Pop": ["pop", "dance pop", "synth-pop"],
    "R&B/Soul": ["r&b", "soul", "neo soul", "alternative r&b"],
    "Afrobeats": ["afrobeats", "afrobeat", "afropop"],
    "Latin/Reggaeton": ["reggaeton", "latin", "urbano latino", "latin pop"],
    "Dancehall": ["dancehall", "ragga"],
    "Electronic/Club": ["house", "techno", "edm", "electronic", "uk garage", "drum and bass"],
    "K-Pop": ["k-pop", "korean pop"],
}

DEFAULT_DJ_STORY = (
    "Between 2021 and 2023, during a pause from my maritime career, I rebuilt creatively "
    "through DJ classes, YouTube-led practice, and selected club and private gigs in Mumbai. "
    "That period sharpened how I read rooms, sequence energy, and spot what listeners lean "
    "into before it becomes mainstream—skills I now pair with regulated analytics work."
)

# CV ↔ Spotify Editor JD (aligned with LinkedIn: sumit-redu-643a66196)
CV_LINKEDIN_URL = "https://www.linkedin.com/in/sumit-redu-643a66196/"

CV_PROFILE = {
    "name": "Sumit Redu",
    "alias": "Sierra Romeo",
    "headline": "Senior Emissions Analyst @ ShipWatch | IIM Mumbai MBA '26",
    "location": "Mumbai, Maharashtra, India",
    "contact": "sumitredu@hotmail.com | +91-9529307047",
    "linkedin_url": CV_LINKEDIN_URL,
    "target_role": "Editor, Music & Culture (International & Hip-Hop) — Spotify, Mumbai",
}

CV_EXPERIENCE_HIGHLIGHTS = [
    "ShipWatch (Jul 2025–present), Mumbai — Senior Emissions Analyst: FuelEU Maritime, EU MRV/ETS, IMO DCS–CII; audit-ready workflows, evidence packs, and analyst playbooks for fleet clients.",
    "GeoServe (Apr 2024–Jul 2025) — Senior Emissions Analyst / Emissions Officer: FuelEU calculator in GeoPerform VPS; DNV Veracity API integration (~30% less manual processing).",
    "Scorpio India (Apr 2023–Mar 2024) — Emission Monitoring Officer: voyage and emissions data with DNV; ~20% fewer data discrepancies.",
    "A.P. Moller–Maersk (Jan 2009–Mar 2021) — Dual Cadet → Third Officer → Second Officer: voyage planning, bridge operations, fuel optimisation.",
    "Career transition (Mar 2021–Apr 2023) — DJ classes, YouTube-led practice, and club/private gigs in Mumbai.",
    "IIM Mumbai — Executive MBA, Logistics Supply Chain & Maritime Management (2024–2026, completing Mar 2026).",
    "Side projects — FPL analytics app (https://fpl-lac.vercel.app); Sierra Romeo Editorial Intelligence Lab (this dashboard).",
]

CV_CERTIFICATIONS = [
    "Generative AI for Data-Driven Business Decision-Making, IIM Mumbai (Apr 2025)",
    "Modelling Digital Supply Chain Twins (anyLogistix), IIM Mumbai (May 2025)",
    "Google Data Analytics Professional Certificate, Coursera (2021–2022)",
]

CV_JD_BRIDGE = {
    "trends": "At ShipWatch I monitor regulatory and performance signals and turn them into playbooks—parallel to spotting artists early via listen velocity in this lab.",
    "curate": "Voyage sequencing at sea and emissions reporting SOPs map to editorial playlist flow (opener → peak → cooldown) with clear narrative.",
    "india_global": "Mumbai-based; programme global club/electronic listening for Indian audiences while elevating desi hip-hop in long-term taste.",
    "data": "Sensor vs report reconciliation, alert rules, and KPI dashboards mirror how this lab reads listener behaviour and playlist metrics.",
    "collaborate": "Work with verifiers, platform engineers, and enterprise clients (e.g. ADNOC L&S, Navig8 contexts at ShipWatch); comfortable presenting data products.",
    "story": "DJ practice in 2021–2023 and this portfolio show culture-first storytelling backed by listening evidence.",
    "experience": "~15 years professional experience (LinkedIn): 12 years at sea with Maersk, emissions analytics since 2023, MBA in progress, plus shipped analytics products—meets the JD’s 6+ years in data-driven, culture-aware work.",
}

# Early discovery scoring (Editor role: spot before mainstream)
EARLY_DISCOVERY_WEIGHTS = {
    "listen_velocity": 0.30,
    "not_in_long_term": 0.25,
    "low_popularity": 0.20,
    "recent_release": 0.15,
    "manual_editorial": 0.10,
}
POPULARITY_PRE_MAINSTREAM_MAX = 45
RECENT_RELEASE_MONTHS = 18

# Scene / language heuristics (from Exportify genres + artist names)
SCENE_KEYWORDS = {
    "Stutter House": ["stutter house"],
    "Melodic Techno": ["melodic techno", "melodic house"],
    "Tech House": ["tech house"],
    "Deep House": ["deep house"],
    "Afro House": ["afro house"],
    "Club / Electronic": ["house", "techno", "edm", "electronic", "uk garage", "drum and bass"],
    "Hip-Hop / Drill": ["drill", "grime", "trap"],
    "Punjabi / Desi": ["punjabi", "bhangra", "desi"],
}

LANGUAGE_KEYWORDS = {
    "Punjabi": ["punjabi", "bhangra"],
    "Hindi": ["hindi", "bollywood", "filmi"],
    "Tamil": ["tamil"],
    "Telugu": ["telugu"],
    "English": ["english"],
}

ROLE_WORKFLOW = "Discover → Program → Tell the story"

ROLE_PAGE_MAP = {
    "home": "Positioning and DJ narrative",
    "discovery": "Breakout watchlist and plays per day",
    "culture": "India export and global entry programming lanes",
    "curate": "Playlist sequencing proof and your playlist scores",
    "role_fit": "Job description mapped to your live data",
}

APP_TITLE = "Sierra Romeo Editorial Intelligence Lab"
APP_SUBTITLE = "Club & electronic discovery • India ↔ global hip-hop • Editorial programming"
FOOTER_TAGLINE = "Music Culture • Editorial Strategy • Data-led Audience Insights"
DISCLAIMER = (
    "Portfolio project using authorized personal listening data; "
    "not affiliated with Spotify."
)
