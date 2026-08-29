"""
Hierarchical Manager Dashboard endpoints.
Organization → Store → Employee drill-down.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
import json

from ..database import get_db
from ..models import *
from ..auth import get_current_user

router = APIRouter(prefix="/api/manager/h", tags=["manager-hierarchical"])


def require_manager(user: User):
    if user.role not in ("manager", "admin"):
        raise HTTPException(status_code=403, detail="Manager access required")


def calc_store_health(product_knowledge, pos_proficiency, training_completion, customer_experience, employee_engagement):
    """Centralized Store Health Score calculation."""
    return round(
        product_knowledge * 0.30 +
        pos_proficiency * 0.25 +
        training_completion * 0.20 +
        customer_experience * 0.15 +
        employee_engagement * 0.10, 1
    )


def store_health_status(score):
    if score >= 90:
        return "healthy"
    elif score >= 75:
        return "warning"
    else:
        return "critical"


def get_store_metrics(store_id, db):
    """Calculate all metrics for a store from its employees."""
    employees = db.query(Employee).filter(Employee.store_id == store_id).all()
    if not employees:
        return None

    count = len(employees)

    # Skill averages
    pk_scores = []
    pos_scores = []
    comm_scores = []
    oh_scores = []
    up_scores = []
    ni_scores = []

    for emp in employees:
        skills = db.query(SkillScore).filter(
            SkillScore.employee_id == emp.id,
            SkillScore.assessment_type == "current"
        ).all()
        skill_map = {s.skill_name: s.score for s in skills}
        pk_scores.append(skill_map.get("product_knowledge", emp.overall_skill_score))
        pos_scores.append(skill_map.get("pos_skills", emp.pos_adoption))
        comm_scores.append(skill_map.get("communication", emp.engagement_score))
        oh_scores.append(skill_map.get("objection_handling", 50))
        up_scores.append(skill_map.get("upselling", emp.upsell_conversion))
        ni_scores.append(skill_map.get("need_identification", 50))

    avg_pk = round(sum(pk_scores) / count, 1) if pk_scores else 0
    avg_pos = round(sum(pos_scores) / count, 1) if pos_scores else 0
    avg_comm = round(sum(comm_scores) / count, 1) if comm_scores else 0
    avg_oh = round(sum(oh_scores) / count, 1) if oh_scores else 0
    avg_up = round(sum(up_scores) / count, 1) if up_scores else 0
    avg_ni = round(sum(ni_scores) / count, 1) if ni_scores else 0

    # Training & engagement
    avg_training = round(sum(e.training_completion for e in employees) / count, 1)
    avg_engagement = round(sum(e.engagement_score for e in employees) / count, 1)
    avg_overall = round(sum(e.overall_skill_score for e in employees) / count, 1)

    # Customer experience = communication (proxy)
    customer_experience = avg_comm

    # Store Health Score
    health = calc_store_health(avg_pk, avg_pos, avg_training, customer_experience, avg_engagement)
    status = store_health_status(health)

    # Training stats
    total_courses = db.query(Course).filter(Course.is_active == True).count()
    trained = 0
    total_badges = 0
    for emp in employees:
        tp = db.query(TrainingProgress).filter(
            TrainingProgress.employee_id == emp.id,
            TrainingProgress.status == "completed"
        ).count()
        if tp > 0:
            trained += 1
        eb = db.query(EmployeeBadge).filter(EmployeeBadge.employee_id == emp.id).count()
        total_badges += eb

    # Challenges
    active_challenges = db.query(Challenge).filter(Challenge.is_active == True).count()

    return {
        "employee_count": count,
        "avg_product_knowledge": avg_pk,
        "avg_pos_proficiency": avg_pos,
        "avg_communication": avg_comm,
        "avg_objection_handling": avg_oh,
        "avg_upselling": avg_up,
        "avg_need_identification": avg_ni,
        "avg_training_completion": avg_training,
        "avg_employee_engagement": avg_engagement,
        "avg_overall_skill": avg_overall,
        "customer_experience": customer_experience,
        "store_health_score": health,
        "store_health_status": status,
        "trained_employees": trained,
        "pending_employees": count - trained,
        "total_badges": total_badges,
        "active_challenges": active_challenges,
        "skills": {
            "product_knowledge": avg_pk,
            "pos_proficiency": avg_pos,
            "communication": avg_comm,
            "objection_handling": avg_oh,
            "upselling": avg_up,
            "need_identification": avg_ni,
        },
        "employees": employees,
    }


# ─── LEVEL 1: ORGANIZATION OVERVIEW ───
@router.get("/organization")
def get_organization_overview(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_manager(user)

    if user.role == "admin":
        stores = db.query(Store).all()
    else:
        stores = db.query(Store).filter(Store.manager_id == user.id).all()

    store_data = []
    healthy_count = 0
    warning_count = 0
    critical_count = 0
    total_employees = 0

    for store in stores:
        metrics = get_store_metrics(store.id, db)
        if not metrics:
            continue

        total_employees += metrics["employee_count"]

        if metrics["store_health_status"] == "healthy":
            healthy_count += 1
        elif metrics["store_health_status"] == "warning":
            warning_count += 1
        else:
            critical_count += 1

        store_data.append({
            "id": store.id,
            "name": store.name,
            "code": store.code,
            "city": store.city,
            "region": store.region,
            "employee_count": metrics["employee_count"],
            "store_health_score": metrics["store_health_score"],
            "store_health_status": metrics["store_health_status"],
            "avg_product_knowledge": metrics["avg_product_knowledge"],
            "avg_pos_proficiency": metrics["avg_pos_proficiency"],
            "avg_training_completion": metrics["avg_training_completion"],
            "avg_employee_engagement": metrics["avg_employee_engagement"],
            "customer_experience": metrics["customer_experience"],
            "avg_overall_skill": metrics["avg_overall_skill"],
            "trained_employees": metrics["trained_employees"],
            "pending_employees": metrics["pending_employees"],
            "total_badges": metrics["total_badges"],
        })

    store_count = len(store_data)
    avg_health = round(sum(s["store_health_score"] for s in store_data) / store_count, 1) if store_count else 0
    avg_training_all = round(sum(s["avg_training_completion"] for s in store_data) / store_count, 1) if store_count else 0
    avg_pos_all = round(sum(s["avg_pos_proficiency"] for s in store_data) / store_count, 1) if store_count else 0
    avg_cx_all = round(sum(s["customer_experience"] for s in store_data) / store_count, 1) if store_count else 0

    # Rankings
    sorted_by_health = sorted(store_data, key=lambda s: s["store_health_score"], reverse=True)
    top5 = sorted_by_health[:5]
    bottom5 = sorted_by_health[-5:]

    # Chart data
    health_distribution = {"healthy": healthy_count, "warning": warning_count, "critical": critical_count}
    performance_chart = [{"name": s["name"].replace("Store ", "S"), "health": s["store_health_score"],
                          "training": s["avg_training_completion"], "pos": s["avg_pos_proficiency"],
                          "cx": s["customer_experience"], "engagement": s["avg_employee_engagement"]}
                         for s in sorted(store_data, key=lambda x: x["store_health_score"])]

    return {
        "summary": {
            "total_stores": store_count,
            "total_employees": total_employees,
            "healthy_stores": healthy_count,
            "warning_stores": warning_count,
            "critical_stores": critical_count,
            "avg_store_health": avg_health,
            "avg_training_completion": avg_training_all,
            "avg_pos_proficiency": avg_pos_all,
            "avg_customer_experience": avg_cx_all,
        },
        "stores": store_data,
        "top_5_stores": top5,
        "bottom_5_stores": list(reversed(bottom5)),
        "health_distribution": health_distribution,
        "performance_chart": performance_chart,
        "ai_insights": _generate_org_insights(store_data, avg_health, healthy_count, warning_count, critical_count),
    }


# ─── LEVEL 2: STORE DASHBOARD ───
@router.get("/store/{store_id}")
def get_store_dashboard(store_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_manager(user)

    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    metrics = get_store_metrics(store_id, db)
    if not metrics:
        raise HTTPException(status_code=404, detail="No employees in this store")

    employees = metrics["employees"]

    # Employee details with skills
    emp_details = []
    for emp in employees:
        skills = db.query(SkillScore).filter(
            SkillScore.employee_id == emp.id,
            SkillScore.assessment_type == "current"
        ).all()
        skill_map = {s.skill_name: s.score for s in skills}

        badge_count = db.query(EmployeeBadge).filter(EmployeeBadge.employee_id == emp.id).count()
        rec_count = db.query(Recognition).filter(Recognition.employee_id == emp.id).count()

        # Determine weakest skill
        weakest_skill = min(skill_map.items(), key=lambda x: x[1]) if skill_map else ("unknown", 0)

        # Find recommended training
        rec_map = {
            "product_knowledge": "Product Knowledge Basics",
            "pos_skills": "Digital POS Mastery",
            "communication": "Customer Communication",
            "objection_handling": "Objection Handling Mastery",
            "upselling": "Upselling & Cross-selling",
            "need_identification": "Customer Need Identification",
        }
        suggested_training = rec_map.get(weakest_skill[0], "General Skills Improvement")

        emp_details.append({
            "id": emp.id,
            "name": emp.name,
            "store_name": store.name,
            "level": emp.level,
            "rank": emp.rank,
            "xp": emp.xp,
            "streak_days": emp.streak_days,
            "overall_skill_score": emp.overall_skill_score,
            "product_knowledge": skill_map.get("product_knowledge", 50),
            "pos_proficiency": skill_map.get("pos_skills", emp.pos_adoption),
            "communication": skill_map.get("communication", 50),
            "objection_handling": skill_map.get("objection_handling", 50),
            "upselling": skill_map.get("upselling", 50),
            "need_identification": skill_map.get("need_identification", 50),
            "training_completion": emp.training_completion,
            "engagement_score": emp.engagement_score,
            "pos_adoption": emp.pos_adoption,
            "badge_count": badge_count,
            "recognition_count": rec_count,
            "weakest_skill": weakest_skill[0],
            "weakest_skill_score": weakest_skill[1],
            "suggested_training": suggested_training,
            "preferred_language": emp.preferred_language,
        })

    # Top 5 and Bottom 5
    sorted_emps = sorted(emp_details, key=lambda e: e["overall_skill_score"], reverse=True)
    top5_emps = sorted_emps[:5]
    bottom5_emps = sorted_emps[-5:]

    # AI Insights for store
    insights = _generate_store_insights(metrics, store.name, emp_details)

    return {
        "store": {
            "id": store.id,
            "name": store.name,
            "code": store.code,
            "city": store.city,
            "region": store.region,
        },
        "metrics": {
            "store_health_score": metrics["store_health_score"],
            "store_health_status": metrics["store_health_status"],
            "product_knowledge": metrics["avg_product_knowledge"],
            "pos_proficiency": metrics["avg_pos_proficiency"],
            "training_completion": metrics["avg_training_completion"],
            "employee_engagement": metrics["avg_employee_engagement"],
            "customer_experience": metrics["customer_experience"],
            "avg_overall_skill": metrics["avg_overall_skill"],
            "employee_count": metrics["employee_count"],
            "trained_employees": metrics["trained_employees"],
            "pending_employees": metrics["pending_employees"],
            "total_badges": metrics["total_badges"],
            "active_challenges": metrics["active_challenges"],
        },
        "skills": metrics["skills"],
        "employees": emp_details,
        "top_5_employees": top5_emps,
        "bottom_5_employees": bottom5_emps,
        "ai_insights": insights,
    }


# ─── LEVEL 3: EMPLOYEE DETAIL ───
@router.get("/employee/{employee_id}")
def get_employee_detail(employee_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_manager(user)

    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    store = emp.store

    # Skill scores
    skills = db.query(SkillScore).filter(
        SkillScore.employee_id == emp.id,
        SkillScore.assessment_type == "current"
    ).all()
    skill_map = {s.skill_name: s.score for s in skills}

    # Training progress
    progress = db.query(TrainingProgress).filter(TrainingProgress.employee_id == emp.id).all()
    completed_courses = [p for p in progress if p.status == "completed"]
    in_progress_courses = [p for p in progress if p.status == "in_progress"]

    # Get course details
    completed_course_details = []
    for p in completed_courses:
        course = db.query(Course).filter(Course.id == p.course_id).first()
        if course:
            completed_course_details.append({
                "id": course.id, "title": course.title,
                "duration": course.duration_minutes,
                "skill_category": course.skill_category,
                "completed_at": p.completed_at.isoformat() if p.completed_at else None,
            })

    pending_courses = db.query(Course).filter(
        Course.is_active == True,
        ~Course.id.in_([p.course_id for p in progress if p.status == "completed"])
    ).all()
    pending_course_details = [{"id": c.id, "title": c.title, "duration": c.duration_minutes,
                               "skill_category": c.skill_category} for c in pending_courses]

    total_courses = db.query(Course).filter(Course.is_active == True).count()

    # Badges
    badge_records = db.query(EmployeeBadge).filter(EmployeeBadge.employee_id == emp.id).all()
    badge_ids = [eb.badge_id for eb in badge_records]
    badges = db.query(Badge).filter(Badge.id.in_(badge_ids)).all() if badge_ids else []

    # Recognitions
    recs = db.query(Recognition).filter(Recognition.employee_id == emp.id).order_by(
        Recognition.created_at.desc()).limit(10).all()

    # Simulation sessions
    sim_sessions = db.query(SimulationSession).filter(
        SimulationSession.employee_id == emp.id,
        SimulationSession.status == "completed"
    ).order_by(SimulationSession.created_at.desc()).limit(5).all()

    sim_data = []
    for s in sim_sessions:
        sim_data.append({
            "id": s.id,
            "assessment_type": s.assessment_type,
            "overall_score": s.overall_score,
            "product_knowledge": s.product_knowledge_score,
            "communication": s.communication_score,
            "objection_handling": s.objection_handling_score,
            "upselling": s.upselling_score,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        })

    # Pre/Post comparison
    pre_sessions = [s for s in sim_sessions if s.assessment_type == "pre"]
    post_sessions = [s for s in sim_sessions if s.assessment_type == "post"]
    pre_score = pre_sessions[0].overall_score if pre_sessions else None
    post_score = post_sessions[0].overall_score if post_sessions else None

    # Quiz attempts
    quiz_attempts = db.query(QuizAttempt).filter(QuizAttempt.employee_id == emp.id).order_by(
        QuizAttempt.completed_at.desc()).limit(5).all()

    # Recent activity
    recent_activity = []
    for p in completed_courses[-3:]:
        course = db.query(Course).filter(Course.id == p.course_id).first()
        if course:
            recent_activity.append({
                "type": "training_completed",
                "title": "Completed " + course.title,
                "date": p.completed_at.isoformat() if p.completed_at else None,
            })
    for r in recs[:3]:
        recent_activity.append({
            "type": "recognition",
            "title": "Received " + r.recognition_type.replace("_", " ").title(),
            "date": r.created_at.isoformat() if r.created_at else None,
        })
    for s in sim_sessions[:2]:
        recent_activity.append({
            "type": "simulation",
            "title": s.assessment_type.title() + " Assessment: " + str(s.overall_score) + "%",
            "date": s.created_at.isoformat() if s.created_at else None,
        })

    recent_activity.sort(key=lambda x: x.get("date") or "", reverse=True)

    # Next Best Action
    weakest = min(skill_map.items(), key=lambda x: x[1]) if skill_map else ("general", 0)
    rec_map = {
        "product_knowledge": ("Complete Product Knowledge Basics", "Your product knowledge needs improvement"),
        "pos_skills": ("Complete Digital POS Mastery", "Your POS proficiency is below target"),
        "communication": ("Complete Customer Communication", "Practice clear customer interactions"),
        "objection_handling": ("Practice Objection Handling", "Your objection handling needs strengthening"),
        "upselling": ("Complete Upselling & Cross-selling", "Improve your upselling techniques"),
        "need_identification": ("Complete Customer Need Identification", "Practice identifying customer needs"),
    }
    nba_title, nba_desc = rec_map.get(weakest[0], ("Try a customer simulation", "Practice with AI customers"))

    return {
        "employee": {
            "id": emp.id,
            "name": emp.name,
            "store_id": emp.store_id,
            "store_name": store.name if store else "",
            "store_city": store.city if store else "",
            "level": emp.level,
            "rank": emp.rank,
            "xp": emp.xp,
            "streak_days": emp.streak_days,
            "preferred_language": emp.preferred_language,
            "overall_skill_score": emp.overall_skill_score,
            "training_completion": emp.training_completion,
            "engagement_score": emp.engagement_score,
            "pos_adoption": emp.pos_adoption,
            "has_completed_pre_assessment": emp.has_completed_pre_assessment,
            "has_completed_post_assessment": emp.has_completed_post_assessment,
        },
        "skills": skill_map,
        "training": {
            "total_courses": total_courses,
            "completed": len(completed_courses),
            "in_progress": len(in_progress_courses),
            "completion_pct": emp.training_completion,
            "completed_courses": completed_course_details,
            "pending_courses": pending_course_details,
        },
        "badges": [{"id": b.id, "name": b.name, "icon": b.icon, "description": b.description} for b in badges],
        "recognitions": [{"type": r.recognition_type, "message": r.message,
                          "xp_awarded": r.xp_awarded,
                          "date": r.created_at.isoformat() if r.created_at else None} for r in recs],
        "simulations": sim_data,
        "pre_assessment_score": pre_score,
        "post_assessment_score": post_score,
        "quiz_attempts": [{"quiz_id": qa.quiz_id, "score": qa.score,
                           "date": qa.completed_at.isoformat() if qa.completed_at else None} for qa in quiz_attempts],
        "recent_activity": recent_activity,
        "next_best_action": {
            "title": nba_title,
            "description": nba_desc,
            "skill": weakest[0],
            "score": weakest[1],
        },
    }


def _generate_org_insights(stores, avg_health, healthy, warning, critical):
    """Generate organization-level AI insights."""
    insights = []

    if critical > 0:
        crit_stores = [s["name"] for s in stores if s["store_health_status"] == "critical"]
        insights.append({
            "type": "alert",
            "title": "Critical Store Attention Required",
            "detail": f"{critical} store(s) have health scores below 75: {', '.join(crit_stores[:3])}. Immediate intervention recommended.",
            "action": "Review store-level dashboards and assign targeted training."
        })

    if warning > 0:
        insights.append({
            "type": "warning",
            "title": "Stores Needing Improvement",
            "detail": f"{warning} store(s) have health scores between 75-89. Proactive coaching can prevent decline.",
            "action": "Schedule team challenges and assign missing training modules."
        })

    # Find lowest POS store
    lowest_pos = min(stores, key=lambda s: s["avg_pos_proficiency"])
    if lowest_pos["avg_pos_proficiency"] < 60:
        insights.append({
            "type": "insight",
            "title": "POS Proficiency Gap",
            "detail": f"{lowest_pos['name']} has the lowest POS proficiency at {lowest_pos['avg_pos_proficiency']}%. {lowest_pos['pending_employees']} employees need POS training.",
            "action": "Assign Digital POS Mastery training to underperforming employees."
        })

    # Find best store
    best = max(stores, key=lambda s: s["store_health_score"])
    insights.append({
        "type": "positive",
        "title": "Top Performing Store",
        "detail": f"{best['name']} leads with a health score of {best['store_health_score']}. Training completion at {best['avg_training_completion']}%.",
        "action": "Consider recognizing the team and replicating their practices."
    })

    if avg_health < 75:
        insights.append({
            "type": "alert",
            "title": "Organization Health Below Target",
            "detail": f"Average store health is {avg_health} (target: 75+). Focus on the weakest metrics across all stores.",
            "action": "Launch organization-wide learning challenge targeting weakest skill areas."
        })
    elif avg_health >= 85:
        insights.append({
            "type": "positive",
            "title": "Strong Organization Performance",
            "detail": f"Average store health is {avg_health}. The workforce is performing well across locations.",
            "action": "Maintain momentum with advanced challenges and recognition programs."
        })

    return insights


def _generate_store_insights(metrics, store_name, emp_details):
    """Generate store-level AI insights."""
    insights = []
    health = metrics["store_health_score"]
    status = metrics["store_health_status"]

    # POS insight
    if metrics["avg_pos_proficiency"] < 60:
        low_pos_emps = [e["name"] for e in emp_details if e["pos_proficiency"] < 60]
        insights.append({
            "type": "alert",
            "title": "POS Proficiency Below Target",
            "detail": f"{store_name} POS proficiency is {metrics['avg_pos_proficiency']}% (target: 60%). {len(low_pos_emps)} employees need POS training.",
            "action": "Assign Digital POS Mastery to: " + ", ".join(low_pos_emps[:3]) + ("..." if len(low_pos_emps) > 3 else "")
        })

    # Training insight
    if metrics["avg_training_completion"] < 60:
        insights.append({
            "type": "warning",
            "title": "Low Training Completion",
            "detail": f"Training completion is {metrics['avg_training_completion']}%. {metrics['pending_employees']} employees have not completed any training.",
            "action": "Launch a store learning challenge with XP rewards."
        })

    # Upselling insight
    if metrics["avg_upselling"] < 55:
        insights.append({
            "type": "insight",
            "title": "Upselling Opportunity Gap",
            "detail": f"Average upselling score is {metrics['avg_upselling']}%. This directly impacts store revenue.",
            "action": "Assign Upselling & Cross-selling training and run a sales challenge."
        })

    # Positive insight
    if status == "healthy":
        insights.append({
            "type": "positive",
            "title": "Store Health is Strong",
            "detail": f"{store_name} health score is {health}. Employees are performing well across all metrics.",
            "action": "Recognize top performers and maintain engagement with advanced challenges."
        })
    elif status == "warning":
        low_skills = []
        if metrics["avg_pos_proficiency"] < 65:
            low_skills.append("POS proficiency")
        if metrics["avg_upselling"] < 55:
            low_skills.append("upselling")
        if metrics["avg_training_completion"] < 65:
            low_skills.append("training completion")
        skill_text = " and ".join(low_skills) if low_skills else "specific metrics"
        insights.append({
            "type": "warning",
            "title": "Store Needs Attention",
            "detail": f"{store_name} health score is {health} (target: 90+). Focus areas: {skill_text}.",
            "action": f"Create a targeted improvement plan focusing on {skill_text}."
        })

    # Bottom employee insight
    if emp_details:
        bottom = min(emp_details, key=lambda e: e["overall_skill_score"])
        if bottom["overall_skill_score"] < 50:
            insights.append({
                "type": "alert",
                "title": "Low-Performing Employee",
                "detail": f"{bottom['name']} has an overall score of {bottom['overall_skill_score']}%. Weakest area: {bottom['weakest_skill'].replace('_', ' ')}.",
                "action": f"Schedule a 1-on-1 coaching session and assign {bottom['suggested_training']}."
            })

    # Engagement insight
    if metrics["avg_employee_engagement"] < 60:
        insights.append({
            "type": "warning",
            "title": "Low Employee Engagement",
            "detail": f"Average engagement is {metrics['avg_employee_engagement']}%. Low engagement affects retention and performance.",
            "action": "Increase recognition activity and launch team-building challenges."
        })

    # Customer experience insight
    if metrics["customer_experience"] >= 75:
        insights.append({
            "type": "positive",
            "title": "Strong Customer Experience",
            "detail": f"Customer experience score is {metrics['customer_experience']}%. Communication skills are a strength.",
            "action": "Leverage this strength by pairing strong communicators with new hires."
        })

    return insights
