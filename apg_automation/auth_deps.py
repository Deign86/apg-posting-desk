from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, HTTPException


def require_role(
    *roles: str,
    user_dependency: Callable | None = None,
) -> Callable:
    def dep(user: dict = Depends(user_dependency)) -> dict:
        if user.get("role") not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return user

    return dep
