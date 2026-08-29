from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import *
from ..auth import get_current_user

router = APIRouter(prefix="/api/admin", tags=["admin"])


def require_admin(user: User):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")


@router.get("/dashboard")
def get_admin_dashboard(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_admin(user)
    
    total_employees = db.query(Employee).count()
    total_stores = db.query(Store).count()
    total_courses = db.query(Course).filter(Course.is_active == True).count()
    total_users = db.query(User).count()
    
    # Organization-level stats
    employees = db.query(Employee).all()
    avg_skill = round(sum(e.overall_skill_score for e in employees) / len(employees), 1) if employees else 0
    avg_pos = round(sum(e.pos_adoption for e in employees) / len(employees), 1) if employees else 0
    avg_engagement = round(sum(e.engagement_score for e in employees) / len(employees), 1) if employees else 0
    
    # Store summary
    stores = db.query(Store).all()
    store_summary = []
    for store in stores:
        store_emps = db.query(Employee).filter(Employee.store_id == store.id).all()
        store_summary.append({
            "id": store.id,
            "name": store.name,
            "code": store.code,
            "city": store.city,
            "employee_count": len(store_emps),
            "avg_skill": round(sum(e.overall_skill_score for e in store_emps) / len(store_emps), 1) if store_emps else 0,
            "avg_pos": round(sum(e.pos_adoption for e in store_emps) / len(store_emps), 1) if store_emps else 0,
        })
    
    return {
        "summary": {
            "total_employees": total_employees,
            "total_stores": total_stores,
            "total_courses": total_courses,
            "total_users": total_users,
            "avg_skill": avg_skill,
            "avg_pos": avg_pos,
            "avg_engagement": avg_engagement,
        },
        "stores": store_summary,
    }


@router.get("/employees")
def list_all_employees(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_admin(user)
    
    employees = db.query(Employee).all()
    return [{
        "id": e.id,
        "name": e.name,
        "store": e.store.name if e.store else "",
        "skill_score": e.overall_skill_score,
        "pos_adoption": e.pos_adoption,
        "engagement": e.engagement_score,
        "training_completion": e.training_completion,
        "xp": e.xp,
        "level": e.level,
    } for e in employees]


@router.get("/stores")
def list_all_stores(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_admin(user)
    
    stores = db.query(Store).all()
    return [{
        "id": s.id,
        "name": s.name,
        "code": s.code,
        "region": s.region,
        "city": s.city,
    } for s in stores]


@router.get("/courses")
def list_all_courses(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_admin(user)
    
    courses = db.query(Course).all()
    return [{
        "id": c.id,
        "title": c.title,
        "description": c.description,
        "duration_minutes": c.duration_minutes,
        "difficulty": c.difficulty,
        "skill_category": c.skill_category,
        "is_active": c.is_active,
    } for c in courses]


@router.get("/scenarios")
def list_all_scenarios(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_admin(user)
    
    scenarios = db.query(CustomerScenario).all()
    return [{
        "id": s.id,
        "name": s.name,
        "persona": s.persona,
        "difficulty": s.difficulty,
        "skill_category": s.skill_category,
        "budget": s.budget,
    } for s in scenarios]
