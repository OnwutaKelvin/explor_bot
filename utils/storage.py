# utils/storage.py

onboarding_state = {}
user_details_temp = {}


def get_state(user_id: int) -> str:
    return onboarding_state.get(user_id, "new")

def set_state(user_id: int, state: str):
    onboarding_state[user_id] = state

def is_onboarded(user_id: int) -> bool:
    return onboarding_state.get(user_id) == "complete"

def save_temp_details(user_id: int, data: dict):
    user_details_temp[user_id] = data

def get_temp_details(user_id: int) -> dict:
    return user_details_temp.get(user_id, {})

def clear_temp_details(user_id: int):
    user_details_temp.pop(user_id, None)

def mark_pending(user_id: int):
    """Called when user joins — marks them as not yet onboarded."""
    if user_id not in onboarding_state:
        onboarding_state[user_id] = "pending"