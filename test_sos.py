import sys
import os
import time

# Ensure S0szalo is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from database import Database
from sos_engine import SOSEngine, parse_duration, format_remaining_seconds

def test_duration_parsing():
    print("--- Test parse_duration ---")
    assert parse_duration("30m") == 1800
    assert parse_duration("1h") == 3600
    assert parse_duration("1h30m") == 5400
    assert parse_duration("120s") == 120
    assert parse_duration("45") == 45 * 60
    assert parse_duration("invalid") is None
    print("✅ parse_duration passed!")

def test_database_and_engine():
    print("--- Test Database & SOSEngine ---")
    test_db_path = "test_sos.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    db = Database(db_path=test_db_path)
    engine = SOSEngine(db)

    # 1. Test contacts
    db.add_contact("123456789", name="Anh Ba", phone="0901234567")
    db.add_contact("987654321", name="Chi Hai")
    contacts = db.list_contacts()
    assert len(contacts) == 2, f"Expected 2 contacts, got {len(contacts)}"
    print("✅ Contact addition passed!")

    # 2. Test arming
    ok, msg = engine.arm("user_admin", "30m")
    assert ok is True
    session = db.get_active_session()
    assert session is not None
    assert session["status"] == "ARMED"
    print("✅ Engine ARM passed!")

    # 3. Test extend
    ok, ext_msg = engine.extend("user_admin", "15m")
    assert ok is True
    updated_session = db.get_active_session()
    assert updated_session["expires_at"] > session["expires_at"]
    print("✅ Engine EXTEND passed!")

    # 4. Test safe / cancel
    ok, safe_msg = engine.safe("user_admin")
    assert ok is True
    assert db.get_active_session() is None
    print("✅ Engine SAFE passed!")

    # 5. Clean up
    import gc
    gc.collect()
    try:
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
    except Exception:
        pass
    print("🎉 All SOS logic tests passed successfully!")

if __name__ == "__main__":
    test_duration_parsing()
    test_database_and_engine()
