import os
from urllib.parse import urlencode

import httpx
from joserfc import jwt
from joserfc.errors import JoseError
from joserfc.jwt import JWTClaimsRegistry


GOOGLE_AUTHORIZATION_URL = (
    "https://accounts.google.com/o/oauth2/v2/auth"
)

GOOGLE_TOKEN_URL = (
    "https://oauth2.googleapis.com/token"
)

GOOGLE_JWKS_URL = (
    "https://www.googleapis.com/oauth2/v3/certs"
)

GOOGLE_ISSUER = "https://accounts.google.com"

GOOGLE_SCOPES = (
    "openid email profile"
)


def get_google_config() -> dict[str, str]:
    client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "").strip()

    if not client_id or not client_secret or not redirect_uri:
        raise RuntimeError(
            "Google OAuth is not configured."
        )

    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
    }


def build_google_authorization_url(
    state: str,
) -> str:
    config = get_google_config()

    params = {
        "client_id": config["client_id"],
        "redirect_uri": config["redirect_uri"],
        "response_type": "code",
        "scope": GOOGLE_SCOPES,
        "state": state,
        "access_type": "offline",
        "prompt": "select_account",
    }

    return (
        GOOGLE_AUTHORIZATION_URL
        + "?"
        + urlencode(params)
    )


async def exchange_code_for_tokens(
    code: str,
) -> dict:
    config = get_google_config()

    data = {
        "code": code,
        "client_id": config["client_id"],
        "client_secret": config["client_secret"],
        "redirect_uri": config["redirect_uri"],
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            GOOGLE_TOKEN_URL,
            data=data,
        )

    if response.status_code != 200:
        raise ValueError(
            "Google authorization code exchange failed."
        )

    return response.json()


async def fetch_google_jwks() -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            GOOGLE_JWKS_URL
        )

    if response.status_code != 200:
        raise ValueError(
            "Unable to retrieve Google signing keys."
        )

    return response.json()


async def verify_google_id_token(
    id_token: str,
    client_id: str,
) -> dict:
    jwks = await fetch_google_jwks()

    try:
        token = jwt.decode(
            id_token,
            jwks,
            algorithms=["RS256"],
        )

        claims = token.claims

        registry = JWTClaimsRegistry(
            iss={
                "essential": True,
                "value": GOOGLE_ISSUER,
            },
            aud={
                "essential": True,
                "value": client_id,
            },
            exp={
                "essential": True,
            },
            sub={
                "essential": True,
            },
            email={
                "essential": True,
            },
            email_verified={
                "essential": True,
            },
        )

        registry.validate(claims)

    except (JoseError, ValueError, TypeError, KeyError) as exc:
        raise ValueError(
            "Invalid Google identity token."
        ) from exc

    if claims.get("email_verified") is not True:
        raise ValueError(
            "Google email address is not verified."
        )

    return dict(claims)


def generate_oauth_state() -> str:
    return os.urandom(32).hex()


def verify_oauth_state(
    received_state: str,
    stored_state: str,
) -> bool:
    import secrets

    if not received_state or not stored_state:
        return False

    return secrets.compare_digest(
        received_state,
        stored_state,
    )


GOOGLE_STATE_COOKIE_NAME = "google_oauth_state"
GOOGLE_AUTH_COOKIE_NAME = "access_token"
GOOGLE_STATE_MAX_AGE_SECONDS = 600
GOOGLE_AUTH_COOKIE_MAX_AGE_SECONDS = 3600
