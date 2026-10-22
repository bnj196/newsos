import time
import re
from datetime import datetime, timezone, timedelta
from zlpp._threads import ThreadType
from zlpp._message import Message

# GMT+7 Timezone for Vietnam
VN_TZ = timezone(timedelta(hours=7))

def format_time_vn(ts):
    dt = datetime.fromtimestamp(ts, tz=VN_TZ)
    return dt.strftime("%H:%M:%S ngày %d/%m/%Y")

def parse_duration(time_str):
    """
    Parses human-readable duration strings like:
      - '30m' or '30' -> 30 minutes
      - '1h' -> 60 minutes
      - '1h30m' -> 90 minutes
      - '120s' -> 120 seconds
      - '2h' -> 120 minutes
    Returns duration in seconds.
    """
    if not time_str or not time_str.strip():
        return None
    
    text = time_str.strip().lower()
    
    # Simple integer: default to minutes
    if text.isdigit():
        return int(text) * 60

    total_seconds = 0
    matched = False

    hours_match = re.search(r"(\d+)\s*(?:h|giờ|g)", text)
    if hours_match:
        total_seconds += int(hours_match.group(1)) * 3600
        matched = True

    mins_match = re.search(r"(\d+)\s*(?:m|phút|p)", text)
    if mins_match:
        total_seconds += int(mins_match.group(1)) * 60
        matched = True

    secs_match = re.search(r"(\d+)\s*(?:s|giây)", text)
    if secs_match:
        total_seconds += int(secs_match.group(1))
        matched = True

    return total_seconds if matched and total_seconds > 0 else None

def format_remaining_seconds(seconds):
    if seconds <= 0:
        return "0 giây"
    mins, secs = divmod(int(seconds), 60)
    hours, mins = divmod(mins, 60)
    parts = []
    if hours > 0:
        parts.append(f"{hours} giờ")
    if mins > 0:
        parts.append(f"{mins} phút")
    if secs > 0 or not parts:
        parts.append(f"{secs} giây")
    return " ".join(parts)


class SOSEngine:
    def __init__(self, db):
        self.db = db

    def arm(self, user_id, duration_str=None, custom_msg=None):
        """Bật chế độ khẩn cấp (Dead Man's Switch)."""
        duration_seconds = None
        if duration_str:
            duration_seconds = parse_duration(duration_str)
            if not duration_seconds:
                return False, "❌ Định dạng thời gian không hợp lệ. Ví dụ: /sos start 30m, /sos start 1h, /sos start 45"

        if not duration_seconds:
            def_mins = int(self.db.get_config("default_timeout_minutes", 30))
            duration_seconds = def_mins * 60

        # Giới hạn tối thiểu 10 giây, tối đa 48 giờ
        if duration_seconds < 10:
            return False, "❌ Thời gian đếm ngược tối thiểu là 10 giây."
        if duration_seconds > 48 * 3600:
            return False, "❌ Thời gian đếm ngược tối đa là 48 giờ."

        contacts = self.db.list_contacts()
        if not contacts:
            return False, (
                "⚠️ Chưa có bạn bè/người thân nào trong danh sách nhận tin SOS!\n"
                "Hãy thêm ít nhất 1 người bằng lệnh:\n"
                "/sos addfriend <zalo_id> [tên_gợi_nhớ]\n"
                "Sau đó mới có thể kích hoạt hẹn giờ."
            )

        session_id, expires_at = self.db.create_session(user_id, duration_seconds, custom_msg)
        deadline_text = format_time_vn(expires_at)
        duration_human = format_remaining_seconds(duration_seconds)

        msg = (
            "🚨 [ĐÃ KÍCH HOẠT HỆ THỐNG SOS - DEAD MAN'S SWITCH] 🚨\n"
            f"👤 Người kích hoạt: {user_id}\n"
            f"⏳ Thời gian đếm ngược: {duration_human}\n"
            f"⏰ Hạn chót xác nhận: {deadline_text}\n"
            f"👥 Số bạn bè nhận tin nếu quá hạn: {len(contacts)} người\n"
            "------------------------------------\n"
            "💡 QUY TẮC AN TOÀN:\n"
            "• Nếu bạn an toàn: Hãy gõ /sos safe hoặc /sos cancel để HỦY lệnh.\n"
            "• Nếu cần thêm thời gian: Gõ /sos extend 30m để GIA HẠN.\n"
            "• NẾU QUÁ THỜI HẠN MÀ KHÔNG TẮT LỆNH: Tin nhắn cứu hộ sẽ TỰ ĐỘNG gửi đến danh sách bạn bè!"
        )
        return True, msg

    def safe(self, user_id):
        """Báo an toàn, hủy phiên đếm ngược."""
        session = self.db.get_active_session()
        if not session:
            return False, "ℹ️ Hiện không có phiên đếm ngược SOS nào đang hoạt động."

        session_id = self.db.cancel_active_session(user_id)
        msg = (
            "🛡️ [XÁC NHẬN AN TOÀN - ĐÃ TẮT SOS] 🛡️\n"
            f"👤 Người xác nhận: {user_id}\n"
            f"✅ Đã hủy lệnh đếm ngược (Phiên #{session_id}).\n"
            "Tin nhắn cứu hộ sẽ KHÔNG được gửi đi. Hệ thống đã trở về trạng thái an toàn!"
        )
        return True, msg

    def extend(self, user_id, duration_str):
        """Gia hạn thêm thời gian cho phiên hiện tại."""
        session = self.db.get_active_session()
        if not session:
            return False, "ℹ️ Hiện không có phiên SOS nào đang chạy để gia hạn. Dùng /sos start <thời_gian> để bật mới."

        extra_seconds = parse_duration(duration_str)
        if not extra_seconds:
            return False, "❌ Định dạng thời gian gia hạn không hợp lệ. Ví dụ: /sos extend 30m, /sos extend 1h"

        session_id, new_expires = self.db.extend_active_session(user_id, extra_seconds)
        deadline_text = format_time_vn(new_expires)
        remaining = new_expires - time.time()

        msg = (
            "⏱️ [ĐÃ GIA HẠN THỜI GIAN SOS] ⏱️\n"
            f"➕ Đã cộng thêm: {format_remaining_seconds(extra_seconds)}\n"
            f"⏳ Thời gian còn lại: {format_remaining_seconds(remaining)}\n"
            f"⏰ Hạn chót mới: {deadline_text}\n"
            "Hãy nhớ gõ /sos safe khi bạn đã hoàn toàn an toàn!"
        )
        return True, msg

    def get_status_text(self):
        """Trả về thông tin trạng thái SOS tổng quan."""
        session = self.db.get_active_session()
        contacts = self.db.list_contacts()
        sos_msg = self.db.get_sos_message()

        status_icon = "🔴 ĐANG ĐẾM NGƯỢC (ARMED)" if session else "🟢 AN TOÀN (STANDBY)"
        
        lines = [
            f"🛡️ TRẠNG THÁI HỆ THỐNG SOS: {status_icon}",
            "------------------------------------"
        ]

        if session:
            now = time.time()
            rem = session["expires_at"] - now
            rem_str = format_remaining_seconds(rem) if rem > 0 else "HẾT GIỜ (Đang xử lý gửi tin...)"
            lines.append(f"🆔 Phiên hiện tại: #{session['id']}")
            lines.append(f"👤 Kích hoạt bởi: {session['user_id']}")
            lines.append(f"⏳ Thời gian còn lại: {rem_str}")
            lines.append(f"⏰ Hạn chót: {format_time_vn(session['expires_at'])}")
            lines.append("👉 Gõ /sos safe để báo an toàn ngay!")
        else:
            lines.append("Hiện tại không có lịch đếm ngược khẩn cấp nào.")
            def_mins = self.db.get_config("default_timeout_minutes", 30)
            lines.append(f"Thời gian mặc định khi bật: {def_mins} phút")
            lines.append("👉 Gõ /sos start <thời_gian> để bắt đầu.")

        lines.append("------------------------------------")
        lines.append(f"👥 Danh sách bạn bè nhận cứu hộ ({len(contacts)} người):")
        if contacts:
            for idx, c in enumerate(contacts, 1):
                name = c.get("name") or "Chưa đặt tên"
                lines.append(f"  {idx}. {name} (Zalo UID: {c['zalo_id']})")
        else:
            lines.append("  (Chưa có bạn bè nào. Dùng /sos addfriend <uid> để thêm)")

        lines.append("------------------------------------")
        lines.append("📝 Mẫu tin nhắn SOS sẽ gửi đi:")
        lines.append(sos_msg.format(time=format_time_vn(time.time())))

        return "\n".join(lines)

    def trigger_immediate(self, client, user_id, internal_group_id=None):
        """Kích hoạt gửi SOS ngay lập tức mà không cần chờ hết giờ."""
        session = self.db.get_active_session()
        session_id = session["id"] if session else None
        return self._execute_sos_dispatch(client, session_id, internal_group_id, reason=f"Kích hoạt khẩn cấp ngay bởi user {user_id}")

    def worker_tick(self, client, internal_group_id):
        """
        Được gọi tuần hoàn từ background thread (mỗi 1-2 giây).
        Kiểm tra trạng thái đếm ngược, gửi cảnh báo trước khi hết hạn và kích hoạt bắn SOS khi quá hạn.
        """
        session = self.db.get_active_session()
        if not session:
            return

        now = time.time()
        session_id = session["id"]
        expires_at = session["expires_at"]
        remaining = expires_at - now

        # 1. Cảnh báo trước 5 phút (300 giây)
        if 0 < remaining <= 300 and not session["warning_5m_sent"]:
            self.db.mark_warning_sent(session_id, "5m")
            if internal_group_id:
                warn_msg = (
                    "⚠️ [CẢNH BÁO SOS - CÒN 5 PHÚT] ⚠️\n"
                    f"Phiên #{session_id} sẽ hết hạn sau 5 phút nữa!\n"
                    "• Nếu bạn an toàn: Hãy gõ /sos safe ngay lập tức!\n"
                    "• Nếu cần thêm thời gian: Gõ /sos extend 30m.\n"
                    "🚨 NẾU KHÔNG CÓ PHẢN HỒI, BOT SẼ TỰ ĐỘNG GỬI TIN NHẮN CỨU HỘ ĐẾN TẤT CẢ BẠN BÈ!"
                )
                try:
                    client.send(Message(text=warn_msg), internal_group_id, ThreadType.GROUP)
                except Exception as e:
                    print(f"❌ Lỗi gửi cảnh báo 5m: {e}")

        # 2. Cảnh báo khẩn cấp trước 1 phút (60 giây)
        if 0 < remaining <= 60 and not session["warning_1m_sent"]:
            self.db.mark_warning_sent(session_id, "1m")
            if internal_group_id:
                warn_msg = (
                    "🚨🚨 [BÁO ĐỘNG ĐỎ - CÒN 1 PHÚT NỮA!] 🚨🚨\n"
                    f"Chỉ còn {int(remaining)} giây trước khi hệ thống kích hoạt gửi SOS!\n"
                    "👉 Gõ ngay /sos safe nếu bạn an toàn!"
                )
                try:
                    client.send(Message(text=warn_msg), internal_group_id, ThreadType.GROUP)
                except Exception as e:
                    print(f"❌ Lỗi gửi cảnh báo 1m: {e}")

        # 3. Quá thời hạn mà user KHÔNG tắt lệnh -> KÍCH HOẠT GỬI SOS!
        if remaining <= 0:
            print(f"🚨 [SOS TIMEOUT] Phiên #{session_id} đã hết hạn mà user không tắt lệnh! Đang gửi SOS...")
            self._execute_sos_dispatch(client, session_id, internal_group_id, reason="Quá thời hạn quy định (Dead Man's Switch Triggered)")

    def _execute_sos_dispatch(self, client, session_id, internal_group_id, reason=""):
        """Thực hiện gửi tin nhắn cứu hộ đến toàn bộ danh sách bạn bè."""
        if session_id:
            self.db.mark_session_triggered(session_id)

        contacts = self.db.list_contacts()
        sos_template = self.db.get_sos_message()
        now_str = format_time_vn(time.time())
        final_sos_msg = sos_template.replace("{time}", now_str)

        success_list = []
        fail_list = []

        for c in contacts:
            target_id = c["zalo_id"]
            name = c.get("name") or target_id
            try:
                # Gửi tin nhắn cá nhân đến Zalo UID của bạn bè
                client.send(Message(text=final_sos_msg), target_id, ThreadType.USER)
                success_list.append(f"{name} ({target_id})")
                self.db.log_event(session_id, "ALERT_SENT", target_id, "SUCCESS", "Đã gửi tin nhắn SOS")
                time.sleep(0.5)  # Tránh rate limit
            except Exception as e:
                err_str = str(e)
                print(f"❌ Không thể gửi SOS tới {name} ({target_id}): {err_str}")
                fail_list.append(f"{name} ({target_id}) - Lỗi: {err_str}")
                self.db.log_event(session_id, "ALERT_SENT", target_id, "FAILED", err_str)

        # Gửi thông báo báo cáo kết quả vào nhóm nội bộ
        if internal_group_id:
            summary_msg = (
                "🚨🚨 [ĐÃ KÍCH HOẠT BẮN TIN CỨU HỘ KHẨN CẤP] 🚨🚨\n"
                f"Lý do: {reason}\n"
                f"Thời gian: {now_str}\n"
                "------------------------------------\n"
                f"✅ Gửi thành công ({len(success_list)}/{len(contacts)} người):\n" +
                ("\n".join([f"  • {item}" for item in success_list]) if success_list else "  (Không có)") +
                "\n" +
                (f"❌ Thất bại ({len(fail_list)} người):\n" + "\n".join([f"  • {item}" for item in fail_list]) if fail_list else "")
            )
            try:
                client.send(Message(text=summary_msg), internal_group_id, ThreadType.GROUP)
            except Exception as e:
                print(f"❌ Lỗi gửi báo cáo tổng kết vào nhóm nội bộ: {e}")

        return True, f"Đã gửi SOS tới {len(success_list)}/{len(contacts)} người bạn."
