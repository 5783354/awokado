from typing import Optional

import falcon
from dynaconf import settings
from jose import jwt


def set_bearer_header(resp: falcon.response.Response, payload: dict) -> str:
    token = jwt.encode(
        payload, settings.AWOKADO_AUTH_BEARER_SECRET, algorithm="HS256"
    )
    resp.set_header("Authorization", f"Bearer {token}")
    return token


def get_bearer_payload(req: falcon.request.Request) -> Optional[dict]:
    bearer_header = req.get_header("Authorization")

    if not bearer_header or "Bearer " not in bearer_header:
        return None

    bearer = bearer_header.split(" ")

    if len(bearer) != 2:
        return None

    bearer_token = bearer[1]

    payload = jwt.decode(
        bearer_token, settings.AWOKADO_AUTH_BEARER_SECRET, algorithms=["HS256"]
    )

    return payload
