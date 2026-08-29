from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
import json

from ..database import get_db
from ..models import *
from ..auth import get_current_user
from ..services.ai_simulator import get_skill_gap_recommendations, get_next_best_action
from ..services.engagement_features import (
    give_peer_recognition, get_peer_recognitions,
    get_pos_micro_lessons, complete_pos_lesson,
    update_streak, check_and_update_last_activity,
    check_auto_badges
)

router = APIRouter(prefix="/api/employee", tags=["employee"])


def get_employee_profile(user: User, db: Session):
    if user.role != "employee":
        raise HTTPException(status_code=403, detail="Not an employee")
    emp = db.query(Employee).filter(Employee.user_id == user.id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    return emp


@router.get("/dashboard")
def get_dashboard(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    emp = get_employee_profile(user, db)
    
    # Get skill scores
    skills = {}
    skill_records = db.query(SkillScore).filter(
        SkillScore.employee_id == emp.id,
        SkillScore.assessment_type == "current"
    ).all()
    for sr in skill_records:
        skills[sr.skill_name] = sr.score
    
    # Get training progress
    progress = db.query(TrainingProgress).filter(TrainingProgress.employee_id == emp.id).all()
    completed_courses = sum(1 for p in progress if p.status == "completed")
    total_courses = db.query(Course).count()
    
    # Get badges
    badge_records = db.query(EmployeeBadge).filter(EmployeeBadge.employee_id == emp.id).all()
    badge_ids = [eb.badge_id for eb in badge_records]
    badges = db.query(Badge).filter(Badge.id.in_(badge_ids)).all() if badge_ids else []
    
    # Get challenges
    ec_records = db.query(EmployeeChallenge).filter(EmployeeChallenge.employee_id == emp.id).all()
    challenge_ids = [ec.challenge_id for ec in ec_records]
    challenges = db.query(Challenge).filter(Challenge.id.in_(challenge_ids)).all() if challenge_ids else []
    challenge_progress = []
    for ec in ec_records:
        ch = db.query(Challenge).filter(Challenge.id == ec.challenge_id).first()
        if ch:
            challenge_progress.append({
                "id": ch.id,
                "title": ch.title,
                "progress": ec.progress,
                "target": ch.target_value,
                "completed": ec.completed,
                "xp_reward": ch.xp_reward,
            })
    
    # Get notifications
    notifs = db.query(Notification).filter(
        Notification.employee_id == emp.id
    ).order_by(Notification.created_at.desc()).limit(10).all()
    
    # Get recent recognitions
    recs = db.query(Recognition).filter(Recognition.employee_id == emp.id).all()
    
    # Get skill gap recommendations
    all_skills = {**skills, "pos_skills": skills.get("pos_skills", emp.pos_adoption)}
    skill_gaps = get_skill_gap_recommendations(all_skills)
    next_action = get_next_best_action(all_skills, {"completed": completed_courses})
    
    # Get recommended courses (not completed)
    completed_course_ids = [p.course_id for p in progress if p.status == "completed"]
    in_progress = [p.course_id for p in progress if p.status == "in_progress"]
    recommended_courses = db.query(Course).filter(
        Course.is_active == True,
        ~Course.id.in_(completed_course_ids)
    ).order_by(Course.sort_order).limit(3).all()
    
    # Get leaderboard
    all_emps = db.query(Employee).order_by(Employee.xp.desc()).all()
    leaderboard = [{"name": e.name, "xp": e.xp, "level": e.level, "rank": e.rank} for e in all_emps[:10]]
    current_rank = next((i+1 for i, e in enumerate(all_emps) if e.id == emp.id), len(all_emps))
    
    # Pre/Post assessment scores
    pre_sessions = db.query(SimulationSession).filter(
        SimulationSession.employee_id == emp.id,
        SimulationSession.assessment_type == "pre",
        SimulationSession.status == "completed"
    ).order_by(SimulationSession.created_at.desc()).limit(1).all()
    
    post_sessions = db.query(SimulationSession).filter(
        SimulationSession.employee_id == emp.id,
        SimulationSession.assessment_type == "post",
        SimulationSession.status == "completed"
    ).order_by(SimulationSession.created_at.desc()).limit(1).all()
    
    pre_score = pre_sessions[0].overall_score if pre_sessions else None
    post_score = post_sessions[0].overall_score if post_sessions else None
    
    return {
        "employee": {
            "id": emp.id,
            "name": emp.name,
            "store_id": emp.store_id,
            "store_name": emp.store.name if emp.store else "",
            "preferred_language": emp.preferred_language,
            "xp": emp.xp,
            "level": emp.level,
            "rank": emp.rank,
            "streak_days": emp.streak_days,
            "pos_adoption": emp.pos_adoption,
            "engagement_score": emp.engagement_score,
            "overall_skill_score": emp.overall_skill_score,
            "training_completion": emp.training_completion,
            "upsell_conversion": emp.upsell_conversion,
            "has_completed_pre_assessment": emp.has_completed_pre_assessment,
            "has_completed_post_assessment": emp.has_completed_post_assessment,
        },
        "skills": skills,
        "badges": [{"id": b.id, "name": b.name, "icon": b.icon, "description": b.description} for b in badges],
        "challenges": challenge_progress,
        "notifications": [{
            "id": n.id, "title": n.title, "message": n.message,
            "type": n.notification_type, "is_read": n.is_read,
        } for n in notifs],
        "recognitions": [{
            "id": r.id, "type": r.recognition_type, "message": r.message,
            "xp_awarded": r.xp_awarded,
        } for r in recs],
        "skill_gaps": skill_gaps[:3],
        "next_action": next_action,
        "recommended_courses": [{
            "id": c.id, "title": c.title, "duration": c.duration_minutes,
            "difficulty": c.difficulty, "skill_category": c.skill_category,
        } for c in recommended_courses],
        "leaderboard": leaderboard,
        "current_rank": current_rank,
        "completed_courses": completed_courses,
        "total_courses": total_courses,
        "pre_assessment_score": pre_score,
        "post_assessment_score": post_score,
    }


@router.put("/language")
def update_language(lang_data: dict, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    emp = get_employee_profile(user, db)
    emp.preferred_language = lang_data.get("language", "en")
    db.commit()
    return {"status": "ok", "language": emp.preferred_language}


# ─── PEER RECOGNITION ───

@router.post("/peer-recognize")
def peer_recognize(payload: dict, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Employee can recognize a peer in the same store."""
    emp = get_employee_profile(user, db)
    to_employee_id = payload.get("employee_id")
    recognition_type = payload.get("recognition_type", "helpful_teammate")
    message = payload.get("message", "Great work!")

    result, error = give_peer_recognition(db, emp.id, to_employee_id, recognition_type, message)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return result


@router.get("/peer-recognitions")
def list_peer_recognitions(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get peer recognitions for the employee's store."""
    emp = get_employee_profile(user, db)
    return get_peer_recognitions(db, emp.store_id)


@router.get("/teammates")
def list_teammates(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get employees in the same store for peer recognition."""
    emp = get_employee_profile(user, db)
    teammates = db.query(Employee).filter(
        Employee.store_id == emp.store_id,
        Employee.id != emp.id
    ).all()
    return [{"id": e.id, "name": e.name, "xp": e.xp, "level": e.level} for e in teammates]


# ─── POS MICRO-LEARNING ───

@router.get("/pos-lessons")
def list_pos_lessons(trigger: str = "after_sale", language: str = "en", user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get micro-lessons for current POS context."""
    return get_pos_micro_lessons(trigger=trigger, language=language)


@router.post("/pos-lesson/{lesson_id}/complete")
def complete_pos_lesson_endpoint(lesson_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Complete a POS micro-lesson and earn XP."""
    emp = get_employee_profile(user, db)
    result, error = complete_pos_lesson(db, emp.id, lesson_id)
    if error:
        raise HTTPException(status_code=400, detail=error)
    # Auto-check badges after earning XP
    check_auto_badges(db, emp.id)
    return result


# ─── STREAK TRACKING ───

@router.post("/activity")
def record_activity(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Record daily activity and update streak. Call on login and meaningful actions."""
    emp = get_employee_profile(user, db)
    update_streak(db, emp.id)
    # Refresh emp data
    db.refresh(emp)
    return {
        "streak_days": emp.streak_days,
        "xp": emp.xp,
        "level": emp.level,
    }


# ─── AUTO BADGES ───

@router.get("/badges/check")
def check_badges(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Check and award any qualifying automatic badges."""
    emp = get_employee_profile(user, db)
    earned = check_auto_badges(db, emp.id)
    return {"newly_earned": earned, "count": len(earned)}
