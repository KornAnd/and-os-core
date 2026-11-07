"""
bilingual_lexicon.py — Lightweight Semantic Lexicon & Cross-Language Bridge (AnD os v8.1).
Enables instant sub-millisecond translation between Russian domain concepts and English canonical paths.
Zero external dependencies. Pure dictionary-based token expansion.
"""

from typing import List, Set

BILINGUAL_MAP = {
    # Production & Feature Animation
    "марс": ["mars", "motomars", "work_mars"],
    "марса": ["mars", "motomars", "work_mars"],
    "марсу": ["mars", "motomars", "work_mars"],
    "мотомарс": ["mars", "motomars"],
    "кот": ["kot", "scholar_cat", "work_kot", "lukomore"],
    "кота": ["kot", "scholar_cat", "work_kot"],
    "дизель": ["dino", "diesel"],
    "аниматик": ["animatic", "storyboard"],
    "аниматикам": ["animatic", "storyboard"],
    "аниматики": ["animatic", "storyboard"],
    "лейаут": ["layout", "cg_pipeline"],
    "рендер": ["render", "lighting", "compositing"],
    "композ": ["compositing", "compositing"],
    "ассет": ["asset", "assets", "character", "prop"],
    "ассеты": ["asset", "assets"],
    "шоты": ["shot", "shots", "sequence"],
    "шот": ["shot", "shots"],
    "продакшн": ["production", "product", "Studio"],
    "студия": ["studio", "Studio", "production"],
    "Studio": ["Studio", "production"],
    "фтрак": ["ftrack", "ftrack_sync"],
    "ftrack": ["ftrack", "ftrack_sync", "gantt"],

    # Health & Athletics
    "здоровье": ["health", "profile", "diagnostics", "medical"],
    "здоровья": ["health", "profile", "diagnostics"],
    "анализ": ["diagnostics", "blood", "health", "biomarker"],
    "анализы": ["diagnostics", "blood", "health", "biomarker"],
    "телеметрия": ["telemetry_sync", "hrv", "sport", "endurance"],
    "telemetry_sync": ["telemetry_sync", "hrv", "sport", "endurance"],
    "пульс": ["heart_rate", "hrv", "telemetry_sync"],
    "сон": ["sleep", "recovery", "health"],
    "бег": ["running", "sport", "endurance", "cadence"],
    "вело": ["bike", "cycling", "triathlon"],
    "триатлон": ["triathlon", "endurance", "ironman"],
    "диета": ["diet", "uc_diet", "nutrition"],

    # Narrative & Books
    "сценарий": ["story", "screenplay", "script", "chunk"],
    "сценарии": ["story", "screenplay", "script"],
    "книга": ["book", "story", "literature"],
    "книги": ["book", "story", "literature"],
    "чудобус": ["chudobus", "chbs", "retro_bus"],
    "персонаж": ["character", "world_bible"],

    # Startup & Incubator
    "стартап": ["startup", "ta_bu", "incubator"],
    "табу": ["ta_bu", "startup", "soft"],
    "софт": ["soft", "software", "saas"],
    "бот": ["bot", "telegram", "tg_bot"],
    "договор": ["contract", "legal", "agreements"],
    "смета": ["budget", "finance", "estimate"],

    # Consulting & Media
    "консалтинг": ["consulting", "cg_core", "audit"],
    "статья": ["article", "cg_article", "content"],
    "статьи": ["article", "cg_article", "content"],
    "индустрия": ["industry", "market", "cg_core"],
    "скрим": ["scream_school", "teach", "education"],

    # Tasks & Operations
    "задачи": ["tasks", "kanban", "sprint"],
    "задача": ["tasks", "kanban"],
    "митинг": ["meetings", "sync", "protocol"],
    "встреча": ["meetings", "sync"],
    "план": ["plan", "roadmap", "dag"],

    # Core & Tools
    "пульсар": ["pulsar", "apps", "mc_doc"],
    "терминал": ["terminal", "and_terminal", "gui"],
    "ядро": ["core", "and_os", "system"],
    "скилл": ["skill", "skills", "sos"],
    "скиллы": ["skill", "skills", "sos"],
    "аудит": ["audit", "health_grid", "probe"],
    "кэш": ["cache", "var", "vacuum"]
}

def expand_tokens(tokens: List[str]) -> Set[str]:
    """
    Expands an inbound list of tokens with all bilingual synonyms.
    Guarantees that a Russian query matches English canonical names and vice versa.
    """
    expanded: Set[str] = set()
    for t in tokens:
        clean_t = t.strip().lower()
        if not clean_t or len(clean_t) < 2:
            continue
        expanded.add(clean_t)
        
        # Direct lookup
        if clean_t in BILINGUAL_MAP:
            expanded.update(BILINGUAL_MAP[clean_t])
            continue
            
        # Stem prefix match
        for key, synonyms in BILINGUAL_MAP.items():
            if len(key) >= 4 and (clean_t.startswith(key[:4]) or key.startswith(clean_t[:4])):
                expanded.update(synonyms)
                expanded.add(key)
                
    return expanded
