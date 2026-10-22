import json
import time
from zlpp import ThreadType
from zlpp._message import Message
from config import Config

HELP_TEXT = (
    "📖 ====== HỆ THỐNG BOT CỨU HỘ ZALO (SOS BACKEND) ======\n"
    "Hệ thống 'Dead Man's Switch' giúp bạn tự động gửi thông tin cứu nạn\n"
    "đến người thân/bạn bè khi gặp nạn và không thể phản hồi đúng hạn.\n"
    "----------------------------------------------------\n"
    "📌 CÁC LỆNH CẤU HÌNH:\n"
    "• /sos status : Xem trạng thái đếm ngược, danh bạ SOS & mẫu tin\n"
    "• /sos setmsg <nội dung> : Cài đặt nội dung tin nhắn SOS cứu trợ\n"
    "• /sos add <uid_zalo> [tên] : Thêm bạn bè/người thân vào danh sách nhận SOS\n"
    "  (Có thể tag @bạn_bè trong nhóm để thêm nhanh)\n"
    "• /sos remove <uid_zalo> : Xóa một người khỏi danh sách nhận SOS\n"
    "• /sos list : Xem danh sách bạn bè đã thêm\n"
    "• /sos timeout <phút> : Cài đặt thời gian đếm ngược mặc định (VD: /sos timeout 45)\n"
    "----------------------------------------------------\n"
    "🚨 CÁC LỆNH ĐIỀU KHIỂN KHẨN CẤP:\n"
    "• /sos start <thời_gian> : BẬT hẹn giờ đếm ngược (VD: /sos start 30m, /sos start 1h)\n"
    "• /sos safe : BÁO AN TOÀN! Tắt đếm ngược, hủy gửi tin SOS\n"
    "• /sos extend <thời_gian> : Gia hạn thêm thời gian (VD: /sos extend 30m)\n"
    "• /sos now : Kích hoạt gửi tin SOS NGAY LẬP TỨC (trường hợp cấp bách)\n"
    "• /sos test : Gửi tin nhắn SOS thử nghiệm vào nhóm để kiểm tra\n"
    "• /sos logs : Xem nhật ký các sự kiện và lịch sử gửi SOS gần nhất\n"
    "----------------------------------------------------\n"
    "💡 Quy tắc: Sau khi bật (/sos start), nếu bạn an toàn hãy gõ /sos safe.\n"
    "Nếu quá thời hạn mà không tắt lệnh, bot sẽ TỰ ĐỘNG gửi tin SOS đến danh sách bạn bè!"
)

class BotHandler:
    def __init__(self, client, db, sos_engine):
        self.client = client
        self.db = db
        self.sos_engine = sos_engine
        self.internal_group_id = Config.INTERNAL_GROUP_ID

    def set_internal_group_id(self, group_id):
        self.internal_group_id = str(group_id)
        self.db.set_config("internal_group_id", str(group_id))

    def get_internal_group_id(self):
        return self.internal_group_id or self.db.get_config("internal_group_id")

    def is_authorized(self, author_id, thread_id, thread_type):
        """
        Kiểm tra quyền thực hiện lệnh:
        1. Nếu là nhóm nội bộ (internal_group_id) -> Cho phép
        2. Nếu người gửi nằm trong ADMIN_USER_IDS -> Cho phép
        3. Nếu chưa set internal_group_id -> Tự động nhận nhóm đầu tiên gửi lệnh /sos setgroup
        """
        curr_internal = self.get_internal_group_id()

        # Nếu chưa cấu hình nhóm nội bộ, và có ai gõ /sos setgroup trong nhóm
        if not curr_internal:
            return True

        # Cho phép nếu là nhóm nội bộ
        if thread_type == ThreadType.GROUP and str(thread_id) == str(curr_internal):
            return True

        # Cho phép nếu tác giả là admin
        if Config.ADMIN_USER_IDS and str(author_id) in Config.ADMIN_USER_IDS:
            return True

        return False

    def handle_message(self, mid, author_id, text, msg_obj, thread_id, thread_type):
        body = (text or "").strip()
        if not body.startswith(("/", "!")):
            return

        # Tách lệnh và đối số
        parts = body[1:].split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1].strip() if len(parts) > 1 else ""

        # Hỗ trợ cả /help hoặc /sos ...
        if cmd == "help":
            self._reply(HELP_TEXT, thread_id, thread_type)
            return

        if cmd != "sos":
            return

        # Kiểm tra quyền truy cập lệnh trong nhóm nội bộ
        if not self.is_authorized(author_id, thread_id, thread_type):
            print(f"⚠️ Từ chối lệnh từ thread_id={thread_id}, author={author_id} (Không phải nhóm nội bộ)")
            return

        # Phân tích lệnh con sau /sos
        sub_parts = args.split(maxsplit=1)
        sub_cmd = sub_parts[0].lower() if sub_parts else "help"
        sub_args = sub_parts[1].strip() if len(sub_parts) > 1 else ""

        print(f"📥 [SOS Command] '{sub_cmd}' từ user {author_id} trong thread {thread_id}")

        # 1. Hướng dẫn sử dụng
        if sub_cmd in ("help", "h"):
            self._reply(HELP_TEXT, thread_id, thread_type)

        # 2. Xem trạng thái
        elif sub_cmd in ("status", "st", "info"):
            status_text = self.sos_engine.get_status_text()
            self._reply(status_text, thread_id, thread_type)

        # 3. Cài đặt nội dung tin nhắn SOS
        elif sub_cmd in ("setmsg", "msg"):
            if not sub_args:
                current_msg = self.db.get_sos_message()
                reply = (
                    f"📝 Mẫu tin nhắn SOS hiện tại:\n\n{current_msg}\n\n"
                    "👉 Để thay đổi, gõ: /sos setmsg <nội dung mới>\n"
                    "(Có thể chèn biến {time} để hiển thị thời gian)"
                )
            else:
                self.db.set_sos_message(sub_args)
                reply = (
                    "✅ Đã cập nhật thành công nội dung tin nhắn SOS cứu trợ!\n"
                    f"Nội dung mới:\n{sub_args}"
                )
            self._reply(reply, thread_id, thread_type)

        # 4. Thêm bạn bè/người thân nhận SOS
        elif sub_cmd in ("add", "addfriend"):
            # Kiểm tra xem có mention (tag) không
            mention_uids = self._extract_mentions(msg_obj)
            if mention_uids:
                added_names = []
                for uid in mention_uids:
                    user_info = self._get_user_display_name(uid)
                    self.db.add_contact(uid, name=user_info)
                    added_names.append(f"{user_info} ({uid})")
                reply = f"✅ Đã thêm {len(added_names)} người vào danh sách nhận SOS:\n" + "\n".join([f"• {x}" for x in added_names])
            elif sub_args:
                arg_parts = sub_args.split(maxsplit=1)
                zalo_uid = arg_parts[0]
                name = arg_parts[1] if len(arg_parts) > 1 else self._get_user_display_name(zalo_uid)
                self.db.add_contact(zalo_uid, name=name)
                reply = f"✅ Đã thêm bạn bè vào danh sách SOS:\n👤 {name} (Zalo UID: {zalo_uid})"
            else:
                reply = (
                    "❌ Thiếu thông tin. Cú pháp:\n"
                    "• /sos add <uid_zalo> [tên_gợi_nhớ]\n"
                    "• Hoặc tag người muốn thêm: /sos add @NgườiA"
                )
            self._reply(reply, thread_id, thread_type)

        # 5. Xóa bạn bè khỏi danh sách nhận SOS
        elif sub_cmd in ("remove", "removefriend", "del", "rm"):
            mention_uids = self._extract_mentions(msg_obj)
            target_uid = mention_uids[0] if mention_uids else sub_args.split()[0] if sub_args else None
            if not target_uid:
                reply = "❌ Cú pháp: /sos remove <uid_zalo> hoặc tag @NgườiDùng"
            else:
                success = self.db.remove_contact(target_uid)
                if success:
                    reply = f"✅ Đã xóa Zalo UID {target_uid} khỏi danh sách nhận SOS."
                else:
                    reply = f"⚠️ Không tìm thấy UID {target_uid} trong danh sách."
            self._reply(reply, thread_id, thread_type)

        # 6. Xem danh sách bạn bè
        elif sub_cmd in ("list", "listfriends", "friends"):
            contacts = self.db.list_contacts()
            if not contacts:
                reply = "📋 Danh sách bạn bè nhận SOS đang trống.\nDùng /sos add <uid> để thêm."
            else:
                lines = [f"📋 DANH SÁCH BẠN BÈ NHẬN TIN SOS ({len(contacts)} người):"]
                for i, c in enumerate(contacts, 1):
                    lines.append(f"{i}. {c.get('name') or 'Chưa đặt tên'} (UID: {c['zalo_id']})")
                reply = "\n".join(lines)
            self._reply(reply, thread_id, thread_type)

        # 7. Bật đếm ngược (ARM / START)
        elif sub_cmd in ("start", "arm", "on"):
            ok, response = self.sos_engine.arm(user_id=author_id, duration_str=sub_args)
            self._reply(response, thread_id, thread_type)

        # 8. Báo an toàn (SAFE / CANCEL / STOP)
        elif sub_cmd in ("safe", "cancel", "stop", "off"):
            ok, response = self.sos_engine.safe(user_id=author_id)
            self._reply(response, thread_id, thread_type)

        # 9. Gia hạn thời gian (EXTEND)
        elif sub_cmd in ("extend", "more", "addtime"):
            if not sub_args:
                reply = "❌ Cần nhập thời gian muốn gia hạn. Ví dụ: /sos extend 30m, /sos extend 1h"
            else:
                ok, response = self.sos_engine.extend(user_id=author_id, duration_str=sub_args)
                reply = response
            self._reply(reply, thread_id, thread_type)

        # 10. Kích hoạt gửi ngay lập tức (NOW / TRIGGER)
        elif sub_cmd in ("now", "trigger", "fire", "emergency"):
            curr_internal = self.get_internal_group_id()
            self._reply("🚨 ĐANG KÍCH HOẠT GỬI CỨU HỘ NGAY LẬP TỨC...", thread_id, thread_type)
            self.sos_engine.trigger_immediate(self.client, user_id=author_id, internal_group_id=curr_internal)

        # 11. Cài đặt thời gian mặc định (TIMEOUT)
        elif sub_cmd in ("timeout", "deftime"):
            if not sub_args or not sub_args.isdigit():
                reply = "❌ Cú pháp: /sos timeout <số_phút> (Ví dụ: /sos timeout 45)"
            else:
                mins = int(sub_args)
                self.db.set_config("default_timeout_minutes", str(mins))
                reply = f"✅ Đã đặt thời gian đếm ngược mặc định là {mins} phút."
            self._reply(reply, thread_id, thread_type)

        # 12. Cấu hình nhóm nội bộ (SETGROUP)
        elif sub_cmd in ("setgroup", "initgroup"):
            target_gid = sub_args if sub_args else (str(thread_id) if thread_type == ThreadType.GROUP else None)
            if not target_gid:
                reply = "❌ Vui lòng chạy lệnh này trong nhóm hoặc cung cấp ID nhóm: /sos setgroup <group_id>"
            else:
                self.set_internal_group_id(target_gid)
                reply = f"✅ Đã cấu hình nhóm nội bộ quản lý SOS: {target_gid}"
            self._reply(reply, thread_id, thread_type)

        # 13. Gửi tin nhắn thử nghiệm (TEST)
        elif sub_cmd == "test":
            sos_msg = self.db.get_sos_message()
            now_str = time.strftime("%H:%M:%S %d/%m/%Y")
            test_content = (
                "🧪 [TIN NHẮN TEST SOS]\n"
                "Đây là tin nhắn kiểm tra thử nghiệm định dạng hiển thị.\n"
                "------------------------------------\n" +
                sos_msg.replace("{time}", now_str)
            )
            self._reply(test_content, thread_id, thread_type)

        # 14. Xem lịch sử (LOGS)
        elif sub_cmd in ("logs", "history"):
            logs = self.db.get_recent_logs(limit=8)
            if not logs:
                reply = "ℹ️ Chưa có sự kiện nào được ghi nhận."
            else:
                lines = ["📜 NHẬT KÝ SỰ KIỆN GẦN NHẤT:"]
                for l in logs:
                    dt = time.strftime("%H:%M:%S %d/%m", time.localtime(l["created_at"]))
                    lines.append(f"• [{dt}] [{l['event_type']}] {l['status']}: {l['details']}")
                reply = "\n".join(lines)
            self._reply(reply, thread_id, thread_type)

        else:
            self._reply(f"❓ Lệnh không hợp lệ: /sos {sub_cmd}. Gõ /sos help để xem danh sách lệnh.", thread_id, thread_type)

    def _reply(self, text, thread_id, thread_type):
        try:
            self.client.send(Message(text=text), thread_id, thread_type)
        except Exception as e:
            print(f"❌ Lỗi gửi tin nhắn phản hồi: {e}")

    def _extract_mentions(self, msg_obj):
        """Trích xuất UID từ mention nếu có trong tin nhắn."""
        uids = []
        try:
            if hasattr(msg_obj, "mention") and msg_obj.mention:
                info = msg_obj.mention.get("mentionInfo")
                if info:
                    data = json.loads(info) if isinstance(info, str) else info
                    for item in data:
                        if "uid" in item:
                            uids.append(str(item["uid"]))
            elif hasattr(msg_obj, "mentions") and msg_obj.mentions:
                for item in msg_obj.mentions:
                    if "uid" in item:
                        uids.append(str(item["uid"]))
        except Exception as e:
            print(f"⚠️ Lỗi trích xuất mention: {e}")
        return uids

    def _get_user_display_name(self, uid):
        try:
            info = self.client.fetchUserInfo(uid)
            if hasattr(info, "toDict"):
                info = info.toDict()
            if isinstance(info, dict):
                profiles = info.get("changed_profiles", {})
                if uid in profiles:
                    return profiles[uid].get("displayName") or profiles[uid].get("zaloName") or str(uid)
        except Exception:
            pass
        return str(uid)
