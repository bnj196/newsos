import os
import json
from pathlib import Path

# Load .env if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Hardcoded fallback cookies from original bot project
FALLBACK_COOKIES = {"_ga":"GA1.2.1067746044.1727246425","__zi":"3000.SSZzejyD6zOgdh2mtnLQWYQN_RAG01ICFjIXe9fEM8WuckkZcqjQYNETwAtVILw0VPVYgpWm.1","__zi-legacy":"3000.SSZzejyD6zOgdh2mtnLQWYQN_RAG01ICFjIXe9fEM8WuckkZcqjQYNETwAtVILw0VPVYgpWm.1","_zlang":"vn","_gid":"GA1.2.873898871.1792657782","_ga_3EM8ZPYYN3":"GS2.2.s1792657782$o5$g0$t1792657782$j60$l0$h0","zpsid":"aOHM.463677646.2.BnVOnmg4Lyx4hFJL1eHNpd_t9Veyjs7vFR9Z-0kpn7NSaojf2okU5s24Lyu","zpw_sek":"XP2l.463677646.a0.c5vtWB6oXyyonmAYtU-XkOVDnDBUrOFniPhqy9w2vjAgbzJ0hSJ9xCM0yDwRqfoRWUwMAa0vjiLRxWvm9OMXkG","app.event.zalo.me":"8223689134614708137"}

class Config:
    PHONE = os.getenv("ZALO_PHONE", "84793634088")
    PASSWORD = os.getenv("ZALO_PASSWORD", ";;;tuienBin")
    IMEI = "5fe2bd7c-47ae-461e-914f-cf01e4670243-16453d6e2683b8800ded2a27c7f595d9"#os.getenv("ZALO_IMEI", "5fe2bd7c-47ae-461e-914f-cf01e4670243-16453d6e2683b8800ded2a27c7f595d9")
    
    COOKIE_FILE = os.getenv("COOKIE_FILE", "zalo_cookies.json")
    DB_PATH = os.getenv("DB_PATH", "sos_database.db")
    
    INTERNAL_GROUP_ID = os.getenv("INTERNAL_GROUP_ID", "").strip()
    INTERNAL_GROUP_NAME = os.getenv("INTERNAL_GROUP_NAME", "test group").strip()
    
    # Admins list
    raw_admins = os.getenv("ADMIN_USER_IDS", "").strip()
    ADMIN_USER_IDS = [x.strip() for x in raw_admins.split(",") if x.strip()] if raw_admins else []
    
    DEFAULT_TIMEOUT_MINUTES = int(os.getenv("DEFAULT_TIMEOUT_MINUTES", "30"))
    
    # Warnings in seconds before expiry
    raw_warnings = os.getenv("WARNING_SECONDS_BEFORE", "300,60").strip()
    WARNING_SECONDS_BEFORE = [int(x.strip()) for x in raw_warnings.split(",") if x.strip().isdigit()]
    
    PORT = int(os.getenv("PORT", "8080"))

    @classmethod
    def load_cookies(cls):
        """Loads cookies from COOKIE_FILE, or falls back to FALLBACK_COOKIES."""
        cookie_path = Path(cls.COOKIE_FILE)
        if cookie_path.exists():
            try:
                with open(cookie_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and len(data) > 0:
                        return data
            except Exception as e:
                print(f"⚠️ [Config] Lỗi đọc file cookie {cls.COOKIE_FILE}: {e}")
        return FALLBACK_COOKIES

    @classmethod
    def save_cookies(cls, session_dict):
        """Saves current session cookies to file."""
        try:
            cookie_path = Path(cls.COOKIE_FILE)
            cookie_path.parent.mkdir(parents=True, exist_ok=True)
            with open(cookie_path, "w", encoding="utf-8") as f:
                json.dump(session_dict, f, indent=2, ensure_ascii=False)
            print(f"✅ [Config] Đã lưu session cookie vào {cls.COOKIE_FILE}")
        except Exception as e:
            print(f"❌ [Config] Không thể lưu cookie: {e}")
