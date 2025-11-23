from flask import Flask, request, jsonify
from flask_cors import CORS
import os

from dotenv import load_dotenv
from supabase import create_client, Client

# ======== 读取环境变量 / 初始化 Supabase ========
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# 尝试从你的 services.py 里导入已有的逻辑
try:
    from services import (
        upsert_user_from_profile,
        get_all_users,
        get_user_by_id,
        update_user,
        delete_user,
        insert_login_event,   # 如果你没实现这个函数，下面 except 会兜底
    )
except ImportError:
    from services import (
        upsert_user_from_profile,
        get_all_users,
        get_user_by_id,
        update_user,
        delete_user,
    )
    insert_login_event = None

app = Flask(__name__)

# ======== CORS 设置 ========
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
CORS(app, resources={r"/*": {"origins": allowed_origins}})


def api_response(success: bool, data=None, error: str | None = None):
    return jsonify({"success": success, "data": data, "error": error})


# ======== 路由实现 ========

@app.route("/health", methods=["GET"])
def health_check():
    return api_response(True, {"status": "ok"})


def get_current_user_from_auth_header():
    """解析 Authorization: Bearer <token>，并返回 db_user"""
    auth = request.headers.get("Authorization", "")
    parts = auth.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None, ("Invalid or missing Authorization header", 401)

    token = parts[1]
    res = supabase.auth.get_user(token)
    user = res.user
    if not user:
        return None, ("Invalid token", 401)

    profile = {
        "id": user.id,
        "email": user.email,
        "user_metadata": {
            "full_name": user.user_metadata.get("full_name") if user.user_metadata else None,
            "avatar_url": user.user_metadata.get("avatar_url") if user.user_metadata else None,
            "provider": user.app_metadata.get("provider") if user.app_metadata else None,
        },
    }
    db_user = upsert_user_from_profile(profile)
    return db_user, None


@app.route("/auth/callback", methods=["POST"])
def auth_callback():
    payload = request.get_json(silent=True) or {}
    access_token = payload.get("access_token")
    if not access_token:
        return api_response(False, error="Missing access_token"), 400

    res = supabase.auth.get_user(access_token)
    user = res.user
    if not user:
        return api_response(False, error="Invalid token"), 401

    profile = {
        "id": user.id,
        "email": user.email,
        "user_metadata": {
            "full_name": user.user_metadata.get("full_name") if user.user_metadata else None,
            "avatar_url": user.user_metadata.get("avatar_url") if user.user_metadata else None,
            "provider": user.app_metadata.get("provider") if user.app_metadata else None,
        },
    }

    db_user = upsert_user_from_profile(profile)

    # 记录登录历史（如果你实现了 insert_login_event）
    if insert_login_event is not None:
        try:
            insert_login_event(profile)
        except Exception:
            # 日志可以以后再加，这里先不让它影响主流程
            pass

    return api_response(True, data=db_user)


@app.route("/users/me", methods=["GET"])
def get_me():
    db_user, err = get_current_user_from_auth_header()
    if err:
        msg, code = err
        return api_response(False, error=msg), code
    return api_response(True, data=db_user)


@app.route("/users", methods=["GET"])
def list_users():
    users = get_all_users()
    return api_response(True, data=users)


@app.route("/users/<user_id>", methods=["GET"])
def get_user_api(user_id):
    user = get_user_by_id(user_id)
    if not user:
        return api_response(False, error="User not found"), 404
    return api_response(True, data=user)


@app.route("/users/<user_id>", methods=["PUT"])
def update_user_api(user_id):
    payload = request.get_json(silent=True) or {}
    updated = update_user(user_id, payload)
    if not updated:
        return api_response(False, error="User not found"), 404
    return api_response(True, data=updated)


@app.route("/users/<user_id>", methods=["DELETE"])
def delete_user_api(user_id):
    delete_user(user_id)
    return api_response(True, data=True)


@app.route("/login-events", methods=["GET"])
def list_login_events():
    """最近 50 条登录记录"""
    res = supabase.table("login_events") \
        .select("*") \
        .order("logged_in_at", desc=True) \
        .limit(50) \
        .execute()
    return api_response(True, data=res.data)


if __name__ == "__main__":
    # 本地调试用，PythonAnywhere 会用 WSGI 加载 app
    app.run(host="0.0.0.0", port=8001, debug=True)
