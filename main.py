import time
import threading
import signal
import sys
from config import Config
from database import Database
from sos_engine import SOSEngine
from bot_handler import BotHandler
from api import app as flask_app, set_bot_instance
from zlpp import ZaloAPI, ZaloAPIException, ThreadType

class SOSBotApp:
    def __init__(self):
        self.db = Database()
        self.sos_engine = SOSEngine(self.db)
        self.client = None
        self.bot_handler = None
        self.running = True
        self.internal_group_id = None

    def find_group_by_name(self, name):
        """Tìm groupId theo tên nhóm."""
        try:
            groups = self.client.fetchAllGroups().toDict()
            for gid in groups.get("gridVerMap", {}):
                info = self.client.fetchGroupInfo(gid).toDict()
                group_data = info.get("gridInfoMap", {}).get(gid, {})
                if group_data.get("name", "").lower() == name.lower():
                    return gid
        except Exception as e:
            print(f"⚠️ Lỗi tìm nhóm '{name}': {e}")
        return None

    def init_zalo(self):
        """Khởi tạo phiên đăng nhập Zalo."""
        cookies = Config.load_cookies()
        print("🔐 Đang đăng nhập tài khoản Zalo...")

        try:
            self.client = ZaloAPI(
                phone=Config.PHONE,
                password=Config.PASSWORD,
                imei=Config.IMEI,
                session_cookies=cookies,
                auto_login=True
            )
            Config.save_cookies(self.client.getSession())
            print(f"✅ Đăng nhập Zalo thành công! UID: {self.client.uid}")
        except Exception as e:
            print(f"❌ Đăng nhập thất bại: {e}")
            raise

        self.bot_handler = BotHandler(self.client, self.db, self.sos_engine)

        # Xác định nhóm nội bộ (Group ID hoặc tìm theo tên)
        gid = Config.INTERNAL_GROUP_ID or self.db.get_config("internal_group_id")
        if not gid and Config.INTERNAL_GROUP_NAME:
            print(f"🔍 Đang tìm kiếm nhóm nội bộ có tên: '{Config.INTERNAL_GROUP_NAME}'...")
            gid = self.find_group_by_name(Config.INTERNAL_GROUP_NAME)

        if gid:
            self.internal_group_id = gid
            self.bot_handler.set_internal_group_id(gid)
            print(f"🎯 Nhóm nội bộ quản lý SOS: gid={gid}")
        else:
            print("⚠️ Chưa xác định được nhóm nội bộ. Bot sẽ chấp nhận lệnh /sos setgroup trong nhóm bất kỳ để gán nhóm quản trị.")

    def _worker_loop(self):
        """Vòng lặp background worker kiểm tra đếm ngược Dead Man's Switch."""
        print("⏱️ Background SOS Worker đã khởi động.")
        while self.running:
            try:
                gid = self.bot_handler.get_internal_group_id() if self.bot_handler else self.internal_group_id
                self.sos_engine.worker_tick(self.client, gid)
            except Exception as e:
                print(f"⚠️ Lỗi trong worker tick: {e}")
            time.sleep(1.0)

    def _start_api_server(self):
        """Khởi động REST API Server cho Healthcheck Docker."""
        set_bot_instance(self)
        print(f"🌐 HTTP Healthcheck Server đang chạy trên port {Config.PORT}...")
        flask_app.run(host="0.0.0.0", port=Config.PORT, threaded=True, debug=False, use_reloader=False)

    def run(self):
        self.init_zalo()

        # Gán hàm xử lý tin nhắn
        def on_message(mid, author_id, text, msg_obj, thread_id, thread_type):
            if str(author_id) == str(self.client.uid):
                return
            self.bot_handler.handle_message(mid, author_id, text, msg_obj, thread_id, thread_type)

        self.client.onMessage = on_message

        # Khởi chạy Worker Thread
        worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        worker_thread.start()

        # Khởi chạy Flask Server Thread
        api_thread = threading.Thread(target=self._start_api_server, daemon=True)
        api_thread.start()

        # Lắng nghe websocket tin nhắn Zalo với cơ chế tự động kết nối lại
        print("📡 Bot đang lắng nghe tin nhắn Zalo...")
        while self.running:
            try:
                self.client.listen(type="websocket", run_forever=True)
            except KeyboardInterrupt:
                print("\n🛑 Nhận tín hiệu dừng từ người dùng.")
                self.running = False
                break
            except Exception as e:
                print(f"⚠️ Mất kết nối websocket Zalo: {e}. Đang thử kết nối lại sau 5 giây...")
                time.sleep(5)

def main():
    bot = SOSBotApp()

    def signal_handler(sig, frame):
        print("\n🛑 Đang tắt bot an toàn...")
        bot.running = False
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    bot.run()

if __name__ == "__main__":
    main()
