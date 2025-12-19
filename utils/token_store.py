import json

FILENAME = "refresh_tokens.json"


def save_refresh_token(user_id: int, token: str, filename: str = FILENAME):
    try:
        with open(filename, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}

    # Save/override token for this user
    data[str(user_id)] = token

    with open(filename, "w") as f:
        json.dump(data, f, indent=4)


def load_refresh_token(user_id: int, filename: str = FILENAME) -> str | None:
    try:
        with open(filename, "r") as f:
            data = json.load(f)
            return data.get(str(user_id))
    except FileNotFoundError:
        return None
