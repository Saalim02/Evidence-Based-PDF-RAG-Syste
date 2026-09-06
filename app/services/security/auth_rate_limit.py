from fastapi import HTTPException

from app.services.security.rate_limiter import RateLimiter


LOGIN_RATE_LIMITER = RateLimiter(
    max_requests=5,
    window_seconds=60,
)

REGISTER_RATE_LIMITER = RateLimiter(
    max_requests=5,
    window_seconds=60,
)

PASSWORD_RESET_REQUEST_RATE_LIMITER = RateLimiter(
    max_requests=5,
    window_seconds=60,
)

PASSWORD_RESET_CONFIRM_RATE_LIMITER = RateLimiter(
    max_requests=5,
    window_seconds=60,
)


def check_auth_rate_limit(
    limiter: RateLimiter,
    client_id: str,
) -> None:
    if not limiter.is_allowed(client_id):
        raise HTTPException(
            status_code=429,
            detail="Too many authentication attempts. Please try again later.",
            headers={"Retry-After": str(limiter.window_seconds)},
        )


GOOGLE_LOGIN_RATE_LIMITER = RateLimiter(
    max_requests=10,
    window_seconds=60,
)
