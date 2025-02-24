from tomlkit.api import parse
from pathlib import Path
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends, HTTPException, status
from typing import Optional
from functools import partial
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Any
import gettext

from fastapi import FastAPI

app = FastAPI(
    title="Emilia Hiring Challenge 👩‍💻",
    description="Help Emilia 👩 to fix our tests and get a job interview 💼🎙️!",
)

DEFAULT_LANGUAGE = "de"
SUPPORTED_GREETINGS = {
    "de": "Hallo {name}, ich bin Emilia.",
    "en": "Hello {name}, I am Emilia.",
    "es": "Hola {name}, soy Emilia."
}

UNSUPPORTED_LANGUAGE_MSG = "Hallo {name}, leider spreche ich nicht '{language}'!"

"""
Task 1 - Warmup
"""


@app.get("/task1/greet/{name}", tags=["Task 1"], summary="👋🇩🇪🇬🇧🇪🇸")
async def task1_greet(name: str, language: str = DEFAULT_LANGUAGE) -> str:
    """Greet somebody in German, English or Spanish!"""
    # import pydevd_pycharm
    # pydevd_pycharm.settrace('localhost', port=5678, stdoutToServer=True, stderrToServer=True)
    if language in SUPPORTED_GREETINGS:
        message = SUPPORTED_GREETINGS[language].format(name=name)
    else:
        message = UNSUPPORTED_LANGUAGE_MSG.format(name=name, language=language)

    return message


"""
Task 2 - snake_case to cameCase
"""


def camelize(key: str):
    """Takes string in snake_case format returns camelCase formatted version."""
    words = key.split('_')
    # Using title method capitalize the first letter of each word
    # Join them using join method
    return words[0] + ''.join(x.title() for x in words[1:])


@app.post("/task2/camelize", tags=["Task 2"], summary="🐍➡️🐪")
async def task2_camelize(data: dict[str, Any]) -> dict[str, Any]:
    """Takes a JSON object and transforms all keys from snake_case to camelCase."""
    return {camelize(key): value for key, value in data.items()}


"""
Task 3 - Handle User Actions
"""

friends = {
    "Matthias": ["Sahar", "Franziska", "Hans"],
    "Stefan": ["Felix", "Ben", "Philip"],
}


class ActionRequest(BaseModel):
    username: str
    action: str


class ActionResponse(BaseModel):
    message: str


def handle_call_action(username: str, action: str):
    # Write your code below
    user_friends_name = None
    friend_list = friends[username]
    for friend in friend_list:
        if friend in action:
            user_friends_name = friend
            break

    if user_friends_name:
        response = {"message": "🤙 Calling {user_friends_name} ...".format(user_friends_name=user_friends_name)}
    else:
        response = {"message": "{username}, I can't find this person in your contacts.".format(username=username)}

    return response


def handle_reminder_action(username: str, action: str):
    response = {"message": "🔔 Alright, I will remind you!"}
    return response


def handle_timer_action(username: str, action: str):
    response = {"message": "⏰ Alright, the timer is set!"}
    return response


def handle_unknown_action(username: str, action: str):
    response = {"message": "👀 Sorry , but I can't help with that!"}
    return response


@app.post("/task3/action", tags=["Task 3"], summary="🤌", response_model=ActionResponse)
def task3_action(request: ActionRequest):
    """Accepts an action request, recognizes its intent and forwards it to the corresponding action handler."""
    # tip: you have to use the response model above and also might change the signature
    #      of the action handlers

    # There must be a better way!
    action_map = {
        'call': handle_call_action,
        'remind': handle_reminder_action,
        'timer': handle_timer_action
    }

    handler = None
    user_list = list(friends.keys())
    if request.username in user_list:
        for act in action_map:
            if act in request.action.lower():
                handler = action_map[act]

        if handler is None:
            handler = handle_unknown_action

    else:
        return {
            "message": "Hi {username}, I don't know you yet. But I would love to meet you!".format(
                username=request.username),
        }

    return handler(request.username, request.action)


"""
Task 4 - Security
"""

# create secret key with: openssl rand -hex 32
SECRET_KEY = "069d49a9c669ddc08f496352166b7b5d270ff64d3009fc297689aa8b0fb66d98"
ALOGRITHM = "HS256"

encode_jwt = partial(jwt.encode, key=SECRET_KEY, algorithm=ALOGRITHM)
decode_jwt = partial(jwt.decode, key=SECRET_KEY, algorithms=[ALOGRITHM])

_crypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
verify_password = _crypt_context.verify
hash_password = _crypt_context.hash

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/task4/token")

fake_users_db = {
    "stefan": {
        "username": "stefan",
        "email": "stefan.buchkremer@meetap.de",
        "hashed_password": hash_password("decent-espresso-by-john-buckmann"),
        "secret": "I love pressure-profiled espresso ☕!",
    },
    "felix": {
        "username": "felix",
        "email": "felix.andreas@meetap.de",
        "hashed_password": hash_password("elm>javascript"),
        "secret": "Rust 🦀 is the best programming language ever!",
    },
}


class User(BaseModel):
    username: str
    email: str
    hashed_password: str
    secret: str


class Token(BaseModel):
    access_token: str
    token_type: str


@app.post("/task4/token", response_model=Token, summary="🔒", tags=["Task 4"])
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Allows registered users to obtain a bearer token."""
    # fixme 🔨, at the moment we allow everybody to obtain a token
    # this is probably not very secure 🛡️ ...
    # tip: check the verify_password above
    # Write your code below
    ...
    payload = {
        "sub": form_data.username,
        "exp": datetime.utcnow() + timedelta(minutes=30),
    }
    return {
        "access_token": encode_jwt(payload),
        "token_type": "bearer",
    }


def get_user(username: str) -> Optional[User]:
    if username not in fake_users_db:
        return
    return User(**fake_users_db[username])


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    # check if the token 🪙 is valid and return a user as specified by the tokens payload
    # otherwise raise the credentials_exception above
    # Write your code below
    ...


@app.get("/task4/users/{username}/secret", summary="🤫", tags=["Task 4"])
async def read_user_secret(
        username: str, current_user: User = Depends(get_current_user)
):
    """Read a user's secret."""
    # uppps 🤭 maybe we should check if the requested secret actually belongs to the user
    # Write your code below
    ...
    if user := get_user(username):
        return user.secret


"""
Task and Help Routes
"""

messages = parse((Path(__file__).parent / "messages.toml").read_text("utf-8"))


@app.get("/", summary="👋", tags=["Emilia"])
async def hello():
    return messages["hello"]


def identity(x): return x


for i in 1, 2, 3, 4:
    task = messages[f"task{i}"]
    info = partial(identity, task["info"])
    help_ = partial(identity, task["help"])
    tags = [f"Task {i}"]
    app.get(f"/task{i}", summary="📝", description=info(), tags=tags)(info)
    app.get(f"/task{i}/help", summary="🙋",
            description=help_(), tags=tags)(help_)
