import sys
import os
import time

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from database import Database
from sos_engine import SOSEngine
from bot_handler import BotHandler
from zlpp._threads import ThreadType

class MockClient:
    def __init__(self):
        self.uid = "BOT_UID_123"
        self.sent_messages = []

    def send(self, message, thread_id, thread_type=ThreadType.USER):
        self.sent_messages.append({
            "text": getattr(message, "text", str(message)),
            "thread_id": thread_id,
            "thread_type": thread_type
        })
        return True

    def fetchUserInfo(self, uid):
        return {"changed_profiles": {uid: {"displayName": f"User_{uid}"}}}

def test_bot_handler():
    print("--- Test BotHandler Commands ---")
    test_db_path = "test_bot_handler.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    db = Database(db_path=test_db_path)
    engine = SOSEngine(db)
    client = MockClient()
    handler = BotHandler(client, db, engine)
    handler.set_internal_group_id("GROUP_INTERNAL_1")

    # 1. Test /help
    handler.handle_message("mid1", "user1", "/help", None, "GROUP_INTERNAL_1", ThreadType.GROUP)
    assert len(client.sent_messages) == 1
    assert "HỆ THỐNG BOT CỨU HỘ ZALO" in client.sent_messages[-1]["text"]
    print("✅ /help test passed!")

    # 2. Test /sos add
    handler.handle_message("mid2", "user1", "/sos add 999888777 Ba_Me", None, "GROUP_INTERNAL_1", ThreadType.GROUP)
    assert "Ba_Me" in client.sent_messages[-1]["text"]
    contacts = db.list_contacts()
    assert len(contacts) == 1
    print("✅ /sos add test passed!")

    # 3. Test /sos status
    handler.handle_message("mid3", "user1", "/sos status", None, "GROUP_INTERNAL_1", ThreadType.GROUP)
    assert "TRẠNG THÁI HỆ THỐNG SOS" in client.sent_messages[-1]["text"]
    print("✅ /sos status test passed!")

    # 4. Test /sos start 30m
    handler.handle_message("mid4", "user1", "/sos start 30m", None, "GROUP_INTERNAL_1", ThreadType.GROUP)
    assert "ĐÃ KÍCH HOẠT" in client.sent_messages[-1]["text"]
    assert db.get_active_session() is not None
    print("✅ /sos start test passed!")

    # 5. Test /sos safe
    handler.handle_message("mid5", "user1", "/sos safe", None, "GROUP_INTERNAL_1", ThreadType.GROUP)
    assert "XÁC NHẬN AN TOÀN" in client.sent_messages[-1]["text"]
    assert db.get_active_session() is None
    print("✅ /sos safe test passed!")

    # 6. Test message from unauthorized group (should be ignored)
    msg_count_before = len(client.sent_messages)
    handler.handle_message("mid6", "stranger", "/sos start 10m", None, "STRANGER_GROUP", ThreadType.GROUP)
    assert len(client.sent_messages) == msg_count_before
    print("✅ Unauthorized group blocking test passed!")

    # Clean up
    import gc
    gc.collect()
    try:
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
    except Exception:
        pass
    print("🎉 All BotHandler tests passed successfully!")

if __name__ == "__main__":
    test_bot_handler()
