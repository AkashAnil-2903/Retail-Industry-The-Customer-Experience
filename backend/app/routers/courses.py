from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import json

from ..database import get_db
from ..models import *
from ..auth import get_current_user
from ..services.engagement_features import check_auto_badges

router = APIRouter(prefix="/api/courses", tags=["courses"])


@router.get("/")
def list_courses(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    courses = db.query(Course).filter(Course.is_active == True).order_by(Course.sort_order).all()
    
    # Get employee progress if employee
    progress_map = {}
    if user.role == "employee":
        emp = db.query(Employee).filter(Employee.user_id == user.id).first()
        if emp:
            progress_records = db.query(TrainingProgress).filter(
                TrainingProgress.employee_id == emp.id
            ).all()
            progress_map = {p.course_id: {"status": p.status, "percent": p.progress_percent} for p in progress_records}
    
    return [{
        "id": c.id,
        "title": c.title,
        "description": c.description,
        "duration_minutes": c.duration_minutes,
        "difficulty": c.difficulty,
        "skill_category": c.skill_category,
        "progress": progress_map.get(c.id, {"status": "not_started", "percent": 0}),
    } for c in courses]


@router.get("/{course_id}")
def get_course(course_id: int, language: str = "en", user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Select content based on language
    title = course.title
    description = course.description
    content = course.content
    if language == "hi":
        title = course.title_hi or course.title
        description = course.description_hi or course.description
        content = course.content_hi or course.content
    elif language == "or":
        title = course.title_or or course.title
        description = course.description_or or course.description
        content = course.content_or or course.content
    
    # Get quiz
    quiz = db.query(Quiz).filter(Quiz.course_id == course_id).first()
    
    return {
        "id": course.id,
        "title": title,
        "description": description,
        "content": content,
        "duration_minutes": course.duration_minutes,
        "difficulty": course.difficulty,
        "skill_category": course.skill_category,
        "has_quiz": quiz is not None,
        "quiz_id": quiz.id if quiz else None,
    }


@router.post("/{course_id}/start")
def start_course(course_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.user_id == user.id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    progress = db.query(TrainingProgress).filter(
        TrainingProgress.employee_id == emp.id,
        TrainingProgress.course_id == course_id
    ).first()
    
    if not progress:
        progress = TrainingProgress(
            employee_id=emp.id,
            course_id=course_id,
            status="in_progress",
            progress_percent=0,
            started_at=datetime.utcnow(),
        )
        db.add(progress)
    elif progress.status == "not_started":
        progress.status = "in_progress"
        progress.started_at = datetime.utcnow()
    
    db.commit()
    return {"status": "ok", "progress_status": progress.status}


@router.post("/{course_id}/complete")
def complete_course(course_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.user_id == user.id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    progress = db.query(TrainingProgress).filter(
        TrainingProgress.employee_id == emp.id,
        TrainingProgress.course_id == course_id
    ).first()
    
    if not progress:
        progress = TrainingProgress(
            employee_id=emp.id,
            course_id=course_id,
            status="completed",
            progress_percent=100,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        db.add(progress)
    else:
        progress.status = "completed"
        progress.progress_percent = 100
        progress.completed_at = datetime.utcnow()
    
    # Award XP
    emp.xp += 50
    
    # Update training completion
    total_courses = db.query(Course).filter(Course.is_active == True).count()
    completed = db.query(TrainingProgress).filter(
        TrainingProgress.employee_id == emp.id,
        TrainingProgress.status == "completed"
    ).count()
    emp.training_completion = round((completed / total_courses) * 100, 1) if total_courses else 0
    
    # Check level up
    emp.level = max(emp.level, 1 + emp.xp // 500)
    rank_map = {1: "Bronze Associate", 2: "Bronze Associate", 3: "Bronze Associate",
                4: "Silver Associate", 5: "Silver Associate", 6: "Silver Associate",
                7: "Gold Associate", 8: "Gold Associate", 9: "Gold Associate", 10: "Platinum Associate"}
    emp.rank = rank_map.get(emp.level, "Platinum Associate")
    
    db.commit()

    # Check for auto-earned badges
    new_badges = check_auto_badges(db, emp.id)

    return {"status": "ok", "xp_earned": 50, "total_xp": emp.xp, "level": emp.level, "newly_earned_badges": new_badges}


# ─── QUIZ ENDPOINTS ───
@router.get("/quiz/{quiz_id}")
def get_quiz(quiz_id: int, language: str = "en", user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    questions = db.query(Question).filter(Question.quiz_id == quiz_id).all()
    
    q_list = []
    for q in questions:
        text = q.text
        exp = q.explanation
        if language == "hi":
            text = q.text_hi or q.text
            exp = q.explanation_hi or q.explanation
        elif language == "or":
            text = q.text_or or q.text
            exp = q.explanation_or or q.explanation
        
        q_list.append({
            "id": q.id,
            "text": text,
            "options": {
                "a": q.option_a,
                "b": q.option_b,
                "c": q.option_c,
                "d": q.option_d,
            },
        })
    
    title = quiz.title
    if language == "hi":
        title = quiz.title_hi or quiz.title
    elif language == "or":
        title = quiz.title_or or quiz.title
    
    return {
        "id": quiz.id,
        "title": title,
        "questions": q_list,
        "passing_score": quiz.passing_score,
    }


@router.post("/quiz/{quiz_id}/submit")
def submit_quiz(quiz_id: int, answers: dict, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.user_id == user.id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    questions = db.query(Question).filter(Question.quiz_id == quiz_id).all()
    
    correct = 0
    total = len(questions)
    details = []
    
    for q in questions:
        user_answer = answers.get(str(q.id), "")
        is_correct = user_answer == q.correct_answer
        if is_correct:
            correct += 1
        details.append({
            "question_id": q.id,
            "user_answer": user_answer,
            "correct_answer": q.correct_answer,
            "is_correct": is_correct,
            "explanation": q.explanation,
        })
    
    score = round((correct / total) * 100) if total else 0
    
    attempt = QuizAttempt(
        employee_id=emp.id,
        quiz_id=quiz_id,
        score=score,
        answers=json.dumps(answers),
    )
    db.add(attempt)
    
    # Award XP if passed
    xp_earned = 0
    if score >= quiz.passing_score:
        xp_earned = 50
        emp.xp += 50
    
    # Update skill score based on quiz
    course = db.query(Course).filter(Course.id == quiz.course_id).first()
    if course:
        skill = db.query(SkillScore).filter(
            SkillScore.employee_id == emp.id,
            SkillScore.skill_name == course.skill_category,
            SkillScore.assessment_type == "current"
        ).first()
        if skill:
            skill.score = min(100, max(skill.score, score))
        else:
            skill = SkillScore(
                employee_id=emp.id,
                skill_name=course.skill_category,
                score=score,
                assessment_type="current",
            )
            db.add(skill)
    
    db.commit()

    # Check for auto-earned badges
    new_badges = check_auto_badges(db, emp.id)

    return {
        "score": score,
        "correct": correct,
        "total": total,
        "passed": score >= quiz.passing_score,
        "passing_score": quiz.passing_score,
        "xp_earned": xp_earned,
        "details": details,
        "newly_earned_badges": new_badges,
    }
