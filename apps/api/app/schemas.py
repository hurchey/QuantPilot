from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr
    password: str = Field(min_length=8, max_length=256)
    workspace_name: str = Field(min_length=1, max_length=100)

    @field_validator("workspace_name")
    @classmethod
    def workspace_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Workspace name is required")
        return v

    @field_validator("password")
    @classmethod
    def password_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Password is required")
        return v


class LoginIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


class AuthMessageOut(BaseModel):
    message: str


class TaskCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=500)
    priority: Literal["low", "medium", "high"] = "medium"

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Title is required")
        return v


class TaskUpdateStatus(BaseModel):
    status: Literal["todo", "in_progress", "done"]


class TaskOut(BaseModel):
    id: int
    title: str
    status: str
    priority: str


class TasksListOut(BaseModel):
    tasks: list[TaskOut]

class TaskStatsOut(BaseModel):
    total: int
    todo: int
    in_progress: int
    done: int