from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models import User
from app.schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    MessageOut,
    ProfileUpdateRequest,
    RegisterRequest,
    SendCodeOut,
    SendCodeRequest,
    TokenOut,
    UserOut,
)
from app.services import code as code_service

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


def _issue_token(user: User, db: Session) -> TokenOut:
    """签发令牌并使旧设备失效（session_version +1）。"""
    user.session_version = int(user.session_version or 0) + 1
    db.commit()
    db.refresh(user)
    token = create_access_token(user.id, extra={"sv": user.session_version})
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.post("/send-code", response_model=SendCodeOut)
def send_code(body: SendCodeRequest, db: Session = Depends(get_db)):
    purpose = body.purpose or "register"
    if purpose not in ("register", "reset_password"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的验证码用途")
    if purpose == "reset_password":
        exists = db.query(User.id).filter(User.email == body.email.lower()).first()
        if not exists:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该邮箱尚未注册")
    dev_code = code_service.send_code(body.email, purpose=purpose)
    if dev_code:
        return SendCodeOut(
            message="尚未配置发信邮箱，验证码已显示在本页（同时写入后端日志）",
            emailed=False,
            dev_code=dev_code,
        )
    return SendCodeOut(message="验证码已发送到你的 QQ 邮箱，请查收（含垃圾箱）", emailed=True)


@router.post("/register", response_model=TokenOut)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    code_service.verify_code(body.email, body.code, purpose="register")

    existing = db.query(User).filter(User.username == body.username).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已被占用")

    matched = (
        db.query(User)
        .filter(User.email == body.email.lower())
        .with_for_update()
        .all()
    )
    if len(matched) >= settings.max_accounts_per_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"该 QQ 邮箱最多只能注册 {settings.max_accounts_per_email} 个账号",
        )

    user = User(
        username=body.username,
        email=body.email.lower(),
        password_hash=hash_password(body.password),
        display_name=body.display_name.strip(),
        session_version=0,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _issue_token(user, db)


@router.post("/login", response_model=TokenOut)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    account = body.account.strip()
    user = (
        db.query(User)
        .filter(or_(User.username == account, User.email == account.lower()))
        .first()
    )
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="账号或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已禁用")
    return _issue_token(user, db)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return UserOut.model_validate(user)


@router.patch("/profile", response_model=UserOut)
def update_profile(
    body: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if body.display_name is not None:
        name = body.display_name.strip()
        if not name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="显示名不能为空")
        user.display_name = name
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


@router.post("/password/send-code", response_model=SendCodeOut)
def send_password_code(user: User = Depends(get_current_user)):
    dev_code = code_service.send_code(user.email, purpose="reset_password")
    if dev_code:
        return SendCodeOut(
            message="验证码已显示（未配 SMTP 时）",
            emailed=False,
            dev_code=dev_code,
        )
    return SendCodeOut(message=f"验证码已发送到 {user.email}", emailed=True)


@router.post("/password/change", response_model=MessageOut)
def change_password(
    body: ChangePasswordRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    code_service.verify_code(user.email, body.code, purpose="reset_password")
    user.password_hash = hash_password(body.new_password)
    # 改密后踢掉其他设备（含当前以外）
    user.session_version = int(user.session_version or 0) + 1
    db.commit()
    return MessageOut(message="密码已修改，请重新登录")


@router.post("/password/reset", response_model=MessageOut)
def reset_password(body: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """未登录找回密码：QQ 邮箱验证码 + 新密码。"""
    code_service.verify_code(body.email, body.code, purpose="reset_password")
    q = db.query(User).filter(User.email == body.email.lower())
    users = q.all()
    if not users:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该邮箱尚未注册")
    if len(users) > 1:
        name = (body.username or "").strip()
        if not name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该邮箱下有多个账号，请填写要重置的用户名",
            )
        user = next((u for u in users if u.username == name), None)
        if not user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名与邮箱不匹配")
    else:
        user = users[0]
        if body.username and body.username.strip() and body.username.strip() != user.username:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名与邮箱不匹配")

    user.password_hash = hash_password(body.new_password)
    user.session_version = int(user.session_version or 0) + 1
    db.commit()
    return MessageOut(message="密码已重置，请用新密码登录")
