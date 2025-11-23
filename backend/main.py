from fastapi import FastAPI, Depends, Header, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

from schemas import APIResponse, User, UserUpdate
from services import supabase, upsert_user_from_profile, get_all_users, get_user_by_id, update_user, delete_user, insert_login_event
import os

app = FastAPI()

allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=APIResponse)
def health_check():
    return APIResponse(success=True, data={"status": "ok"})


def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header")

    token = parts[1]
    res = supabase.auth.get_user(token)
    user = res.user
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

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
    return db_user


@app.post("/auth/callback", response_model=APIResponse)
def auth_callback(payload: dict = Body(...)):
    # 从 JSON 里拿 access_token
    access_token = payload.get("access_token")
    if not access_token:
        return APIResponse(success=False, error="Missing access_token")

    res = supabase.auth.get_user(access_token)
    user = res.user
    if not user:
        return APIResponse(success=False, error="Invalid token")

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
    insert_login_event(profile)
    return APIResponse(success=True, data=db_user)


@app.get("/users/me", response_model=APIResponse)
def get_me(current_user=Depends(get_current_user)):
    return APIResponse(success=True, data=current_user)


@app.get("/users", response_model=APIResponse)
def list_users():
    users = get_all_users()
    return APIResponse(success=True, data=users)


@app.get("/users/{user_id}", response_model=APIResponse)
def get_user(user_id: str):
    user = get_user_by_id(user_id)
    if not user:
        return APIResponse(success=False, error="User not found")
    return APIResponse(success=True, data=user)


@app.put("/users/{user_id}", response_model=APIResponse)
def update_user_api(user_id: str, payload: UserUpdate):
    updated = update_user(user_id, payload.dict(exclude_unset=True))
    if not updated:
        return APIResponse(success=False, error="User not found")
    return APIResponse(success=True, data=updated)


@app.delete("/users/{user_id}", response_model=APIResponse)
def delete_user_api(user_id: str):
    delete_user(user_id)
    return APIResponse(success=True, data=True)

@app.get("/login-events", response_model=APIResponse)
def list_login_events():
    """
    最近 50 条登录记录，按时间倒序。
    """
    res = supabase.table("login_events") \
        .select("*") \
        .order("logged_in_at", desc=True) \
        .limit(50) \
        .execute()
    return APIResponse(success=True, data=res.data)
