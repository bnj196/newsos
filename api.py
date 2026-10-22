import time
from flask import Flask, jsonify, request

app = Flask(__name__)
bot_instance = None
start_time = time.time()

def set_bot_instance(instance):
    global bot_instance
    bot_instance = instance

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "service": "Zalo SOS Dead Man's Switch Bot",
        "version": "1.0.0",
        "status": "running",
        "uptime_seconds": int(time.time() - start_time)
    })

@app.route("/health", methods=["GET"])
def health_check():
    """Healthcheck endpoint for Docker container."""
    is_logged_in = False
    if bot_instance and hasattr(bot_instance, "client") and bot_instance.client:
        is_logged_in = bool(bot_instance.client.uid)

    return jsonify({
        "status": "healthy",
        "logged_in": is_logged_in,
        "uptime_seconds": int(time.time() - start_time)
    }), 200

@app.route("/api/status", methods=["GET"])
def get_sos_status():
    if not bot_instance or not bot_instance.sos_engine:
        return jsonify({"error": "Bot engine not initialized"}), 503

    session = bot_instance.db.get_active_session()
    contacts = bot_instance.db.list_contacts()
    return jsonify({
        "active_session": session,
        "contacts_count": len(contacts),
        "sos_message": bot_instance.db.get_sos_message()
    })

@app.route("/api/arm", methods=["POST"])
def arm_sos():
    if not bot_instance or not bot_instance.sos_engine:
        return jsonify({"error": "Bot engine not initialized"}), 503

    data = request.get_json() or {}
    user_id = data.get("user_id", "API_USER")
    duration = data.get("duration", "30m")
    custom_msg = data.get("message")

    ok, message = bot_instance.sos_engine.arm(user_id=user_id, duration_str=duration, custom_msg=custom_msg)
    return jsonify({"success": ok, "message": message}), (200 if ok else 400)

@app.route("/api/safe", methods=["POST"])
def safe_sos():
    if not bot_instance or not bot_instance.sos_engine:
        return jsonify({"error": "Bot engine not initialized"}), 503

    data = request.get_json() or {}
    user_id = data.get("user_id", "API_USER")
    ok, message = bot_instance.sos_engine.safe(user_id=user_id)
    return jsonify({"success": ok, "message": message}), (200 if ok else 400)
