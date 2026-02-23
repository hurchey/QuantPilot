from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .config import settings
from .db import Base, engine, get_db
from .models import Task, User, Workspace
from .schemas import (
    AuthMessageOut,
    LoginIn,
    RegisterIn,
    TaskCreate,
    TaskOut,
    TasksListOut,
    TaskUpdateStatus,
    TaskStatsOut,
)
from .security import (
    COOKIE_NAME,
    clear_auth_cookie,
    create_access_token,
    decode_access_token,
    hash_password,
    password_needs_rehash,
    set_auth_cookie,
    verify_password,
)

app = FastAPI(title="WorkPilot API", version="0.1.0")


# --- CORS ---
# Allow both localhost and 127.0.0.1 in dev to avoid origin mismatches
allowed_origins = {
    settings.frontend_url.rstrip("/"),
}

if "localhost" in settings.frontend_url:
    allowed_origins.add(settings.frontend_url.replace("localhost", "127.0.0.1").rstrip("/"))
if "127.0.0.1" in settings.frontend_url:
    allowed_origins.add(settings.frontend_url.replace("127.0.0.1", "localhost").rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(allowed_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Startup ---
@app.on_event("startup")
def on_startup() -> None:
    # Creates tables if they don't exist yet
    Base.metadata.create_all(bind=engine)


# --- Helpers / dependencies ---
def _task_to_dict(task: Task) -> dict:
    return {
        "id": task.id,
        "title": task.title,
        "status": task.status,
        "priority": task.priority,
    }


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        user_id = decode_access_token(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


def get_current_workspace(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Workspace:
    workspace = (
        db.query(Workspace)
        .filter(Workspace.owner_id == user.id)
        .order_by(Workspace.id.asc())
        .first()
    )
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace


# --- Health ---
@app.get("/health")
def health() -> dict:
    return {"ok": True}


# --- Auth ---
@app.post("/auth/register", response_model=AuthMessageOut, status_code=201)
def register(payload: RegisterIn, response: Response, db: Session = Depends(get_db)) -> dict:
    email = payload.email.lower()

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")

    try:
        user = User(
            email=email,
            hashed_password=hash_password(payload.password),
        )
        db.add(user)
        db.flush()  # gets user.id before commit

        workspace = Workspace(
            name=payload.workspace_name.strip(),
            owner_id=user.id,
        )
        db.add(workspace)

        db.commit()
        db.refresh(user)

    except Exception:
        db.rollback()
        raise

    token = create_access_token(user.id)
    set_auth_cookie(response, token)
    return {"message": "registered"}


@app.post("/auth/login", response_model=AuthMessageOut)
def login(payload: LoginIn, response: Response, db: Session = Depends(get_db)) -> dict:
    user = db.query(User).filter(User.email == payload.email.lower()).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Upgrade older hashes (e.g., bcrypt) to argon2 after successful login
    if password_needs_rehash(user.hashed_password):
        try:
            user.hashed_password = hash_password(payload.password)
            db.add(user)
            db.commit()
        except Exception:
            db.rollback()
            # Don't block login if rehash fails; continue

    token = create_access_token(user.id)
    set_auth_cookie(response, token)
    return {"message": "logged_in"}


@app.post("/auth/logout", response_model=AuthMessageOut)
def logout(response: Response) -> dict:
    clear_auth_cookie(response)
    return {"message": "logged_out"}


@app.get("/me")
def me(user: User = Depends(get_current_user)) -> dict:
    return {
        "id": user.id,
        "email": user.email,
    }


# Optional alias if your frontend calls /auth/me
@app.get("/auth/me")
def auth_me(user: User = Depends(get_current_user)) -> dict:
    return {
        "id": user.id,
        "email": user.email,
    }


# --- Tasks ---
@app.get("/tasks", response_model=TasksListOut)
def list_tasks(
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db),
) -> dict:
    tasks = (
        db.query(Task)
        .filter(Task.workspace_id == workspace.id)
        .order_by(Task.id.desc())
        .all()
    )
    return {"tasks": [_task_to_dict(task) for task in tasks]}


@app.post("/tasks", response_model=TaskOut, status_code=201)
def create_task(
    payload: TaskCreate,
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db),
) -> dict:
    task = Task(
        title=payload.title.strip(),
        status="todo",
        priority=payload.priority,
        workspace_id=workspace.id,
    )

    try:
        db.add(task)
        db.commit()
        db.refresh(task)
    except Exception:
        db.rollback()
        raise

    return _task_to_dict(task)

@app.get("/tasks/stats", response_model=TaskStatsOut)
def task_stats(
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db),
) -> dict:
    tasks = (
        db.query(Task)
        .filter(Task.workspace_id == workspace.id)
        .all()
    )

    stats = {
        "total": len(tasks),
        "todo": 0,
        "in_progress": 0,
        "done": 0,
    }

    for task in tasks:
        if task.status in stats:
            stats[task.status] += 1

    return stats

@app.patch("/tasks/{task_id}", response_model=TaskOut)
def update_task_status(
    task_id: int,
    payload: TaskUpdateStatus,
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db),
) -> dict:
    task = (
        db.query(Task)
        .filter(Task.id == task_id, Task.workspace_id == workspace.id)
        .first()
    )

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = payload.status

    # If your model has updated_at, update it safely
    if hasattr(task, "updated_at"):
        task.updated_at = datetime.now(timezone.utc)

    try:
        db.add(task)
        db.commit()
        db.refresh(task)
    except Exception:
        db.rollback()
        raise

    return _task_to_dict(task)


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db),
) -> Response:
    task = (
        db.query(Task)
        .filter(Task.id == task_id, Task.workspace_id == workspace.id)
        .first()
    )

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    try:
        db.delete(task)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return Response(status_code=204)