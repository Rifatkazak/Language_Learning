import hashlib
import secrets
import datetime
import streamlit as st
from storage.user_store import (
    load_users_file, save_users_file, load_user_data, persist_current_user
)


def hash_password(plain: str, salt: str = None) -> tuple:
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac(
        "sha256", plain.encode("utf-8"), salt.encode("utf-8"), 200_000
    )
    return hashed.hex(), salt


def verify_password(plain: str, hash_hex: str, salt: str) -> bool:
    check, _ = hash_password(plain, salt)
    return check == hash_hex


def is_logged_in() -> bool:
    return bool(st.session_state.get("authenticated") and st.session_state.get("current_user"))


def login(username: str, password: str) -> tuple:
    """Returns (success: bool, message: str)"""
    if not username.strip():
        return False, "Kullanıcı adı boş olamaz."
    users = load_users_file()
    st.session_state["users"] = users

    if username not in users:
        return False, "Kullanıcı bulunamadı."

    user = users[username]

    # Legacy user without password — first-login migration
    if not user.get("password_hash"):
        return False, "BU_KULLANICI_SIFRESIZ"

    if not verify_password(password, user["password_hash"], user["password_salt"]):
        return False, "Hatalı şifre."

    load_user_data(username)
    st.session_state.authenticated = True
    st.session_state["_user_data_loaded"] = True

    # Set trial start for existing users who don't have one yet
    if username != "rifat":
        ai_cache = st.session_state.get("ai_cache", {})
        if "__trial_start__" not in ai_cache:
            ai_cache["__trial_start__"] = str(datetime.date.today())
            st.session_state.ai_cache = ai_cache
            persist_current_user()

    return True, "Giriş başarılı."


def register(username: str, password: str) -> tuple:
    """Returns (success: bool, message: str)"""
    username = username.strip().lower()
    if not username:
        return False, "Kullanıcı adı boş olamaz."
    if len(password) < 4:
        return False, "Şifre en az 4 karakter olmalı."

    users = load_users_file()
    if username in users:
        return False, "Bu kullanıcı adı zaten alınmış."

    h, s = hash_password(password)
    users[username] = {
        "password_hash": h,
        "password_salt": s,
        "created_at": str(datetime.date.today()),
        "progress": {},
        "last_study_date": None,
        "daily_streak": 0,
        "total_study_minutes": 0,
        "custom_words": [],
        "total_xp": 0,
        "earned_achievements": [],
        "ai_cache": {"__trial_start__": str(datetime.date.today())},
        "daily_tasks": {},
        "grace_period_used": False,
    }
    save_users_file(users)
    st.session_state["users"] = users
    load_user_data(username)
    st.session_state.authenticated = True
    st.session_state["_user_data_loaded"] = True
    return True, "Hesap oluşturuldu!"


def set_password_for_legacy(username: str, new_password: str) -> tuple:
    """First-time password set for existing passwordless users."""
    if len(new_password) < 4:
        return False, "Şifre en az 4 karakter olmalı."
    users = load_users_file()
    if username not in users:
        return False, "Kullanıcı bulunamadı."
    h, s = hash_password(new_password)
    users[username]["password_hash"] = h
    users[username]["password_salt"] = s
    # Set trial start if not already present
    if username != "rifat":
        ai_cache = users[username].get("ai_cache") or {}
        if "__trial_start__" not in ai_cache:
            ai_cache["__trial_start__"] = str(datetime.date.today())
            users[username]["ai_cache"] = ai_cache
    save_users_file(users)
    st.session_state["users"] = users
    load_user_data(username)
    st.session_state.authenticated = True
    st.session_state["_user_data_loaded"] = True
    return True, "Şifre ayarlandı!"


def logout() -> None:
    keys_to_clear = [
        "authenticated", "current_user", "progress", "custom_words",
        "daily_streak", "last_study_date", "total_xp", "earned_achievements",
        "ai_cache", "daily_tasks", "flash_deck", "quiz_deck", "flash_idx",
        "quiz_idx", "flash_flipped", "quiz_state", "ai_sentence",
        "_user_data_loaded", "users",
    ]
    for k in keys_to_clear:
        st.session_state.pop(k, None)
