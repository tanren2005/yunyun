import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


def is_qq_email(email: str) -> bool:
    return email.lower().endswith("@qq.com")


class SendCodeRequest(BaseModel):
    email: EmailStr
    purpose: str = "register"

    @field_validator("email")
    @classmethod
    def must_be_qq(cls, v: str) -> str:
        if not is_qq_email(v):
            raise ValueError("仅支持 QQ 邮箱（@qq.com）注册")
        return v.lower()


class RegisterRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=4, max_length=8)
    username: str = Field(min_length=2, max_length=32)
    password: str = Field(min_length=8, max_length=64)
    display_name: str = Field(min_length=1, max_length=64)

    @field_validator("email")
    @classmethod
    def must_be_qq(cls, v: str) -> str:
        if not is_qq_email(v):
            raise ValueError("仅支持 QQ 邮箱（@qq.com）注册")
        return v.lower()

    @field_validator("username")
    @classmethod
    def username_format(cls, v: str) -> str:
        name = v.strip()
        if len(name) < 2:
            raise ValueError("用户名至少 2 个字符")
        if re.search(r"[\s/@\\#?]", name):
            raise ValueError("用户名不能包含空格、@、斜杠等特殊符号")
        return name

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v) or not re.search(r"[a-z]", v):
            raise ValueError("密码须同时包含大写字母和小写字母")
        return v


class LoginRequest(BaseModel):
    account: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=6, max_length=64)


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    display_name: str
    is_admin: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class ProfileUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=64)


class ChangePasswordRequest(BaseModel):
    code: str = Field(min_length=4, max_length=8)
    new_password: str = Field(min_length=8, max_length=64)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v) or not re.search(r"[a-z]", v):
            raise ValueError("密码须同时包含大写字母和小写字母")
        return v


class ForgotPasswordRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=4, max_length=8)
    new_password: str = Field(min_length=8, max_length=64)
    username: str | None = Field(default=None, max_length=32)

    @field_validator("email")
    @classmethod
    def must_be_qq(cls, v: str) -> str:
        if not is_qq_email(v):
            raise ValueError("仅支持 QQ 邮箱（@qq.com）")
        return v.lower()

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v) or not re.search(r"[a-z]", v):
            raise ValueError("密码须同时包含大写字母和小写字母")
        return v


class NotificationOut(BaseModel):
    id: int
    kind: str
    title: str
    body: str
    link: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UnreadCountOut(BaseModel):
    count: int


class AdminUserOut(BaseModel):
    id: int
    username: str
    email: str
    display_name: str
    is_active: bool
    is_admin: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminUserUpdate(BaseModel):
    is_active: bool | None = None
    is_admin: bool | None = None
    display_name: str | None = Field(default=None, min_length=1, max_length=64)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class CategoryOut(BaseModel):
    id: int
    slug: str
    name: str
    description: str

    model_config = {"from_attributes": True}


class PostCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(default="", max_length=100000)
    category_id: int
    summary: str = Field(default="", max_length=300)


class PostUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=1, max_length=100000)
    category_id: int | None = None
    summary: str | None = Field(default=None, max_length=300)


class AuthorBrief(BaseModel):
    id: int
    username: str
    display_name: str

    model_config = {"from_attributes": True}


class AttachmentOut(BaseModel):
    id: int
    original_name: str
    url: str
    mime: str
    size: int
    kind: str


class PostOut(BaseModel):
    id: int
    title: str
    content: str
    summary: str
    view_count: int
    comment_count: int
    created_at: datetime
    updated_at: datetime
    author: AuthorBrief
    category: CategoryOut
    attachments: list[AttachmentOut] = []

    model_config = {"from_attributes": True}


class PostListItem(BaseModel):
    id: int
    title: str
    summary: str
    view_count: int
    comment_count: int
    created_at: datetime
    author: AuthorBrief
    category: CategoryOut
    has_files: bool = False

    model_config = {"from_attributes": True}


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)
    parent_id: int | None = None


class CommentOut(BaseModel):
    id: int
    content: str
    parent_id: int | None = None
    created_at: datetime
    author: AuthorBrief

    model_config = {"from_attributes": True}


class SendCodeOut(BaseModel):
    message: str
    emailed: bool = True
    dev_code: str | None = None


class MessageOut(BaseModel):
    message: str


class MomentCreate(BaseModel):
    content: str = Field(default="", max_length=5000)


class MomentOut(BaseModel):
    id: int
    content: str
    comment_count: int
    created_at: datetime
    author: AuthorBrief
    attachments: list[AttachmentOut] = []

    model_config = {"from_attributes": True}


class BookCreate(BaseModel):
    book_title: str = Field(min_length=1, max_length=200)
    book_author: str = Field(default="", max_length=120)
    content: str = Field(default="", max_length=20000)


class BookOut(BaseModel):
    id: int
    book_title: str
    book_author: str
    content: str
    comment_count: int
    created_at: datetime
    author: AuthorBrief
    attachments: list[AttachmentOut] = []

    model_config = {"from_attributes": True}


class DailyOut(BaseModel):
    id: int
    day: str
    kind: str
    kind_label: str
    title: str
    body: str
    source: str
    note: str = ""
