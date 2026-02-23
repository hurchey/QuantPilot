from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from .db import get_db
from .models import User, Workspace
from .security import COOKIE_NAME, decode_access_token


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        user_id = decode_access_token(token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


def get_current_workspace(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Workspace:
    workspace = db.query(Workspace).filter(Workspace.owner_id == user.id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace