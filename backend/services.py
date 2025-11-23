import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")

print("DEBUG SUPABASE_URL =", SUPABASE_URL)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def insert_login_event(profile: dict):
    """
    往 login_events 表插入一条登录记录。
    一个人可以有很多条记录。
    """
    user_id = profile.get("id")
    email = profile.get("email")
    meta = profile.get("user_metadata", {}) or {}
    provider = meta.get("provider")

    data = {
        "auth_user_id": user_id,
        "email": email,
        "provider": provider,
        # logged_in_at 用默认 now() 就行，不传也可以
    }

    supabase.table("login_events").insert(data).execute()


def upsert_user_from_profile(profile: dict):
    user_id = profile.get("id")
    email = profile.get("email")
    meta = profile.get("user_metadata", {}) or {}
    name = meta.get("full_name") or meta.get("name")
    avatar_url = meta.get("avatar_url")
    provider = meta.get("provider")

    data = {
        "id": user_id,
        "email": email,
        "name": name,
        "avatar_url": avatar_url,
        "provider": provider,
    }

    # 一人一行：主键是 id（auth user id），存在则更新，不存在则插入
    res = supabase.table("users").upsert(data).execute()
    return res.data[0] if res.data else None


def get_all_users():
    res = supabase.table("users").select("*").execute()
    return res.data or []


def get_user_by_id(user_id: str):
    res = supabase.table("users").select("*").eq("id", user_id).single().execute()
    return res.data


def update_user(user_id: str, payload: dict):
    res = supabase.table("users").update(payload).eq("id", user_id).execute()
    return res.data[0] if res.data else None


def delete_user(user_id: str):
    supabase.table("users").delete().eq("id", user_id).execute()
    return True

