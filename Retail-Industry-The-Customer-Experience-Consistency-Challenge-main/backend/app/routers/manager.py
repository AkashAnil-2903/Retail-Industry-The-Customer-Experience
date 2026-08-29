from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from ..database import get_db
from ..models import *
from ..auth import get_current_user

router = APIRouter(prefix="/api/manager", tags=["manager"])


def require_manager(user: User):
    if user.role not in ("manager", "admin"):
        raise HTTPException(status_code=403, detail="Manager access required")


@router.get("/dashboard")
def get_manager_dashboard(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_manager(user)
    
    # Get all stores (manager sees their store, admin sees all)
    if user.role == "admin":
        stores = db.query(Store).all()
    else:
        stores = db.query(Store).filter(Store.manager_id == user.id).all()
    
    store_ids = [s.id for s in stores]
    employees = db.query(Employee).filter(Employee.store_id.in_(store_ids)).all() if store_ids else []
    
    total_employees = len(employees)
    avg_skill = round(sum(e.overall_skill_score for e in employees) / total_employees, 1) if total_employees else 0
    avg_pos = round(sum(e.pos_adoption for e in employees) / total_employees, 1) if total_employees else 0
    avg_engagement = round(sum(e.engagement_score for e in employees) / total_employees, 1) if total_employees else 0
    avg_training = round(sum(e.training_completion for e in employees) / total_employees, 1) if total_employees else 0
    avg_upsell = round(sum(e.upsell_conversion for e in employees) / total_employees, 1) if total_employees else 0
    
    # Top performers
    top_performers = sorted(employees, key=lambda e: e.overall_skill_score, reverse=True)[:5]
    
    # Most improved (by XP)
    most_improved = sorted(employees, key=lambda e: e.xp, reverse=True)[:5]
    
    # Employees requiring attention (skill score < 50)
    attention_needed = [e for e in employees if e.overall_skill_score < 55]
    
    # Skill gaps across store
    skill_categories = ["product_knowledge", "pos_skills", "communication", "upselling", "objection_handling"]
    skill_gaps = {}
    for skill in skill_categories:
        scores = []
        for emp in employees:
            ss = db.query(SkillScore).filter(
                SkillScore.employee_id == emp.id,
                SkillScore.skill_name == skill,
                SkillScore.assessment_type == "current"
            ).first()
            if ss:
                scores.append(ss.score)
        skill_gaps[skill] = round(sum(scores) / len(scores), 1) if scores else 50
    
    # Recent recognitions
    recognitions = db.query(Recognition).filter(
        Recognition.employee_id.in_([e.id for e in employees])
    ).order_by(Recognition.created_at.desc()).limit(10).all()
    
    return {
        "summary": {
            "total_employees": total_employees,
            "training_completion": avg_training,
            "pos_adoption": avg_pos,
            "engagement": avg_engagement,
            "average_skill_score": avg_skill,
            "upsell_conversion": avg_upsell,
        },
        "top_performers": [{
            "id": e.id, "name": e.name,
            "skill_score": e.overall_skill_score,
            "xp": e.xp, "level": e.level,
            "store": e.store.name if e.store else "",
        } for e in top_performers],
        "most_improved": [{
            "id": e.id, "name": e.name,
            "xp": e.xp, "level": e.level,
            "engagement": e.engagement_score,
            "store": e.store.name if e.store else "",
        } for e in most_improved],
        "attention_needed": [{
            "id": e.id, "name": e.name,
            "skill_score": e.overall_skill_score,
            "pos_adoption": e.pos_adoption,
            "engagement": e.engagement_score,
            "store": e.store.name if e.store else "",
        } for e in attention_needed],
        "skill_gaps": skill_gaps,
        "recognitions": [{
            "id": r.id,
            "employee_name": next((e.name for e in employees if e.id == r.employee_id), ""),
            "type": r.recognition_type,
            "message": r.message,
            "date": r.created_at.isoformat() if r.created_at else "",
        } for r in recognitions],
        "stores": [{"id": s.id, "name": s.name, "code": s.code, "city": s.city} for s in stores],
    }


@router.get("/employees")
def list_store_employees(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_manager(user)
    
    if user.role == "admin":
        employees = db.query(Employee).all()
    else:
        stores = db.query(Store).filter(Store.manager_id == user.id).all()
        store_ids = [s.id for s in stores]
        employees = db.query(Employee).filter(Employee.store_id.in_(store_ids)).all() if store_ids else []
    
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
        "rank": e.rank,
        "streak_days": e.streak_days,
    } for e in employees]


@router.post("/recognize")
def recognize_employee(payload: dict, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_manager(user)
    
    employee_id = payload.get("employee_id")
    recognition_type = payload.get("recognition_type", "customer_hero")
    message = payload.get("message", "")
    
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    recognition = Recognition(
        employee_id=employee_id,
        manager_id=user.id,
        recognition_type=recognition_type,
        message=message,
        xp_awarded=100,
    )
    db.add(recognition)
    
    # Award XP
    employee.xp += 100
    employee.level = max(employee.level, 1 + employee.xp // 500)
    
    # Add badge if not already earned
    badge_name_map = {
        "customer_hero": "Customer Hero",
        "product_expert": "Product Expert",
        "digital_champion": "POS Champion",
        "great_team_player": "Learning Champion",
        "most_improved": "Most Improved",
    }
    badge_name = badge_name_map.get(recognition_type)
    if badge_name:
        badge = db.query(Badge).filter(Badge.name == badge_name).first()
        if badge:
            existing = db.query(EmployeeBadge).filter(
                EmployeeBadge.employee_id == employee_id,
                EmployeeBadge.badge_id == badge.id
            ).first()
            if not existing:
                db.add(EmployeeBadge(employee_id=employee_id, badge_id=badge.id))
    
    # Add notification
    type_labels = {
        "customer_hero": ("Customer Hero", "ग्राहक हीरो", "ଗ୍ରାହକ ହିରୋ"),
        "product_expert": ("Product Expert", "उत्पाद विशेषज्ञ", "ଉତ୍ପାଦ ବିଶେଷଜ୍ଞ"),
        "digital_champion": ("Digital Champion", "डिजिटल चैंपियन", "ଡିଜିଟାଲ ଚାମ୍ପିଅନ୍"),
        "great_team_player": ("Great Team Player", "बेहतरीन टीम प्लेयर", "ଉତ୍ତମ ଟିମ୍ ଖେଳୁଆଳ"),
        "most_improved": ("Most Improved", "सबसे ज्यादा सुधार", "ସବୁଠାରୁ ଉନ୍ନତ"),
    }
    labels = type_labels.get(recognition_type, ("Recognition", "मान्यता", "ସ୍ୱୀକୃତି"))
    
    db.add(Notification(
        employee_id=employee_id,
        title=f"Your manager recognized you as {labels[0]}!",
        title_hi=f"आपके प्रबंधक ने आपको {labels[1]} के रूप में मान्यता दी!",
        title_or=f"ଆପଣଙ୍କ ମ୍ୟାନେଜର ଆପଣଙ୍କୁ {labels[2]} ଭାବରେ ସ୍ୱୀକୃତି ଦେଲେ!",
        message=message,
        notification_type="recognition",
    ))
    
    db.commit()
    
    return {
        "status": "ok",
        "xp_awarded": 100,
        "new_xp": employee.xp,
        "new_level": employee.level,
    }


@router.get("/heatmap")
def get_skill_heatmap(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_manager(user)
    
    if user.role == "admin":
        stores = db.query(Store).all()
    else:
        stores = db.query(Store).filter(Store.manager_id == user.id).all()
    
    skill_categories = ["product_knowledge", "pos_skills", "communication", "upselling"]
    
    heatmap = []
    for store in stores:
        employees = db.query(Employee).filter(Employee.store_id == store.id).all()
        row = {"store": store.name, "code": store.code}
        
        for skill in skill_categories:
            scores = []
            for emp in employees:
                ss = db.query(SkillScore).filter(
                    SkillScore.employee_id == emp.id,
                    SkillScore.skill_name == skill,
                    SkillScore.assessment_type == "current"
                ).first()
                if ss:
                    scores.append(ss.score)
            avg = round(sum(scores) / len(scores), 1) if scores else 50
            row[skill] = avg
        
        heatmap.append(row)
    
    return {"heatmap": heatmap, "skill_categories": skill_categories}


@router.get("/employee/{employee_id}/progress")
def get_employee_progress(employee_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_manager(user)
    
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Get skill scores
    skills = {}
    skill_records = db.query(SkillScore).filter(
        SkillScore.employee_id == employee.id,
        SkillScore.assessment_type == "current"
    ).all()
    for sr in skill_records:
        skills[sr.skill_name] = sr.score
    
    # Get simulation sessions
    pre_sessions = db.query(SimulationSession).filter(
        SimulationSession.employee_id == employee.id,
        SimulationSession.assessment_type == "pre",
        SimulationSession.status == "completed"
    ).order_by(SimulationSession.created_at.desc()).limit(1).all()
    
    post_sessions = db.query(SimulationSession).filter(
        SimulationSession.employee_id == employee.id,
        SimulationSession.assessment_type == "post",
        SimulationSession.status == "completed"
    ).order_by(SimulationSession.created_at.desc()).limit(1).all()
    
    pre_score = pre_sessions[0].overall_score if pre_sessions else None
    post_score = post_sessions[0].overall_score if post_sessions else None
    improvement = (post_score - pre_score) if pre_score and post_score else None
    
    # Get training progress
    progress = db.query(TrainingProgress).filter(
        TrainingProgress.employee_id == employee.id
    ).all()
    completed_courses = sum(1 for p in progress if p.status == "completed")
    
    # Get recognitions
    recs = db.query(Recognition).filter(
        Recognition.employee_id == employee.id
    ).order_by(Recognition.created_at.desc()).limit(5).all()
    
    # Get badges
    badge_records = db.query(EmployeeBadge).filter(EmployeeBadge.employee_id == employee.id).all()
    badge_ids = [eb.badge_id for eb in badge_records]
    badges = db.query(Badge).filter(Badge.id.in_(badge_ids)).all() if badge_ids else []
    
    # Identify weakest skill
    weakest_skill = min(skills.items(), key=lambda x: x[1]) if skills else ("unknown", 0)
    
    return {
        "employee": {
            "id": employee.id,
            "name": employee.name,
            "store": employee.store.name if employee.store else "",
            "skill_score": employee.overall_skill_score,
            "pos_adoption": employee.pos_adoption,
            "engagement": employee.engagement_score,
            "training_completion": employee.training_completion,
            "xp": employee.xp,
            "level": employee.level,
            "rank": employee.rank,
        },
        "skills": skills,
        "pre_assessment_score": pre_score,
        "post_assessment_score": post_score,
        "improvement": improvement,
        "weakest_skill": weakest_skill[0],
        "weakest_skill_score": weakest_skill[1],
        "completed_courses": completed_courses,
        "recognitions": [{
            "type": r.recognition_type,
            "message": r.message,
            "date": r.created_at.isoformat() if r.created_at else "",
        } for r in recs],
        "badges": [{"name": b.name, "icon": b.icon} for b in badges],
    }


@router.get("/business-impact")
def get_business_impact(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_manager(user)
    
    # Return simulated business impact data (clearly labeled as demo)
    return {
        "disclaimer": "Simulated / Demo impact data — not actual business results",
        "before": {
            "training_completion": 64,
            "pos_adoption": 51,
            "skill_score": 58,
            "engagement": 61,
            "upsell_conversion": 12,
        },
        "after": {
            "training_completion": 89,
            "pos_adoption": 78,
            "skill_score": 81,
            "engagement": 84,
            "upsell_conversion": 18,
        },
        "trend_data": [
            {"month": "Jan", "training": 64, "pos": 51, "skill": 58, "engagement": 61, "upsell": 12},
            {"month": "Feb", "training": 68, "pos": 55, "skill": 62, "engagement": 65, "upsell": 13},
            {"month": "Mar", "training": 72, "pos": 60, "skill": 66, "engagement": 68, "upsell": 14},
            {"month": "Apr", "training": 78, "pos": 65, "skill": 71, "engagement": 73, "upsell": 15},
            {"month": "May", "training": 83, "pos": 71, "skill": 76, "engagement": 78, "upsell": 16},
            {"month": "Jun", "training": 89, "pos": 78, "skill": 81, "engagement": 84, "upsell": 18},
        ],
    }
