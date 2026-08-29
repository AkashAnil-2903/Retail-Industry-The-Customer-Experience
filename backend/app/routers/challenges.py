from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from ..database import get_db
from ..models import *
from ..auth import get_current_user

router = APIRouter(prefix="/api/challenges", tags=["challenges"])


@router.get("/")
def list_challenges(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    challenges = db.query(Challenge).filter(Challenge.is_active == True).all()
    
    # Get employee progress
    emp = None
    progress_map = {}
    if user.role == "employee":
        emp = db.query(Employee).filter(Employee.user_id == user.id).first()
        if emp:
            ec_records = db.query(EmployeeChallenge).filter(EmployeeChallenge.employee_id == emp.id).all()
            progress_map = {ec.challenge_id: {"progress": ec.progress, "completed": ec.completed} for ec in ec_records}
    
    return [{
        "id": c.id,
        "title": c.title,
        "description": c.description,
        "challenge_type": c.challenge_type,
        "xp_reward": c.xp_reward,
        "target_value": c.target_value,
        "skill_category": c.skill_category,
        "progress": progress_map.get(c.id, {"progress": 0, "completed": False}),
    } for c in challenges]


@router.post("/{challenge_id}/progress")
def update_challenge_progress(challenge_id: int, payload: dict, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.user_id == user.id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    ec = db.query(EmployeeChallenge).filter(
        EmployeeChallenge.employee_id == emp.id,
        EmployeeChallenge.challenge_id == challenge_id
    ).first()
    
    if not ec:
        ec = EmployeeChallenge(employee_id=emp.id, challenge_id=challenge_id, progress=0)
        db.add(ec)
    
    increment = payload.get("increment", 1)
    ec.progress = min(challenge.target_value, ec.progress + increment)
    
    if ec.progress >= challenge.target_value and not ec.completed:
        ec.completed = True
        ec.completed_at = datetime.utcnow()
        emp.xp += challenge.xp_reward
        emp.level = max(emp.level, 1 + emp.xp // 500)
        db.commit()
        return {"status": "completed", "xp_earned": challenge.xp_reward, "total_xp": emp.xp}
    
    db.commit()
    return {"status": "in_progress", "progress": ec.progress, "target": challenge.target_value}


@router.get("/leaderboard")
def get_leaderboard(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    employees = db.query(Employee).order_by(Employee.xp.desc()).all()
    
    # Calculate FairScore
    leaderboard = []
    for i, e in enumerate(employees):
        # FairScore = 40% Performance + 30% Improvement + 20% Learning + 10% Recognition
        performance = e.overall_skill_score
        improvement = e.engagement_score  # Use engagement as proxy
        learning = e.training_completion
        rec_count = db.query(Recognition).filter(Recognition.employee_id == e.id).count()
        recognition = min(100, rec_count * 25)
        
        fair_score = round(
            performance * 0.40 +
            improvement * 0.30 +
            learning * 0.20 +
            recognition * 0.10, 1
        )
        
        leaderboard.append({
            "rank": i + 1,
            "id": e.id,
            "name": e.name,
            "store": e.store.name if e.store else "",
            "xp": e.xp,
            "level": e.level,
            "rank_title": e.rank,
            "performance": performance,
            "improvement": improvement,
            "learning": learning,
            "recognition": recognition,
            "fair_score": fair_score,
            "streak_days": e.streak_days,
        })
    
    leaderboard.sort(key=lambda x: x["fair_score"], reverse=True)
    for i, entry in enumerate(leaderboard):
        entry["rank"] = i + 1
    
    return leaderboard
