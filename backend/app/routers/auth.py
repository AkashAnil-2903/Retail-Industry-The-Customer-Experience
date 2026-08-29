from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import get_db
from ..models import User, Employee
from ..auth import verify_password, create_access_token
from ..services.engagement_features import update_streak, check_auto_badges

router = APIRouter(prefix="/api/auth", tags=["auth"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int
    employee_id: int | None = None
    name: str | None = None


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token(data={"sub": user.id, "role": user.role})
    
    employee_id = None
    name = None
    if user.role == "employee":
        emp = db.query(Employee).filter(Employee.user_id == user.id).first()
        if emp:
            employee_id = emp.id
            name = emp.name
            # Update daily streak on login
            update_streak(db, emp.id)
            # Check for auto-earned badges
            check_auto_badges(db, emp.id)
    
    return TokenResponse(
        access_token=token,
        role=user.role,
        user_id=user.id,
        employee_id=employee_id,
        name=name,
    )
