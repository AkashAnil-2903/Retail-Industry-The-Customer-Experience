"""
Engagement Features Service
- Peer Recognition (employee-to-employee)
- POS-Integrated Micro-Learning
- Dynamic Streak Tracking
- Automatic Badge Earning from Performance Metrics
"""
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)


# ─── PEER RECOGNITION ───

def give_peer_recognition(db: Session, from_employee_id: int, to_employee_id: int, recognition_type: str, message: str):
    """
    Employee-to-employee recognition.
    Awards 50 XP to recipient, 25 XP to giver (reciprocal engagement).
    """
    from ..models import Employee, Recognition, Notification, EmployeeBadge, Badge

    if from_employee_id == to_employee_id:
        return None, "You cannot recognize yourself"

    giver = db.query(Employee).filter(Employee.id == from_employee_id).first()
    receiver = db.query(Employee).filter(Employee.id == to_employee_id).first()

    if not giver or not receiver:
        return None, "Employee not found"

    if giver.store_id != receiver.store_id:
        return None, "You can only recognize colleagues in your store"

    # Create recognition record (manager_id = from_employee_id for peer)
    recognition = Recognition(
        employee_id=to_employee_id,
        manager_id=giver.user_id,
        recognition_type=recognition_type,
        message=f"[Peer] {giver.name}: {message}",
        xp_awarded=50,
    )
    db.add(recognition)

    # Award XP to receiver
    receiver.xp += 50
    receiver.level = max(receiver.level, 1 + receiver.xp // 500)

    # Award bonus XP to giver (reciprocal engagement)
    giver.xp += 25
    giver.level = max(giver.level, 1 + giver.xp // 500)

    # Check if receiver earns a peer-nominated badge
    peer_rec_count = db.query(Recognition).filter(
        Recognition.employee_id == to_employee_id,
        Recognition.message.like("[Peer]%")
    ).count() + 1  # +1 for the one we just added

    if peer_rec_count >= 3:
        badge = db.query(Badge).filter(Badge.name == "Team Favorite").first()
        if badge:
            existing = db.query(EmployeeBadge).filter(
                EmployeeBadge.employee_id == to_employee_id,
                EmployeeBadge.badge_id == badge.id
            ).first()
            if not existing:
                db.add(EmployeeBadge(employee_id=to_employee_id, badge_id=badge.id))

    # Notification to receiver
    type_labels = {
        "helpful_teammate": ("Helpful Teammate", "उपयोगी साथी", "ସାହାଯ୍ୟକାରୀ ସାଥୀ"),
        "great_collaboration": ("Great Collaboration", "बेहतरीन सहयोग", "ଉତ୍ତମ ସହଯୋଗ"),
        "product_knowledge_star": ("Product Knowledge Star", "उत्पादन ज्ञान स्टार", "ଉତ୍ପାଦ ଜ୍ଞାନ ଷ୍ଟାର"),
        "customer_first": ("Customer First", "ग्राहक पहले", "ଗ୍ରାହକ ପ୍ରଥମେ"),
        "pos_champion_peer": ("POS Champion", "POS चैंपियन", "POS ଚାମ୍ପିଅନ୍"),
    }
    labels = type_labels.get(recognition_type, ("Peer Recognition", "साथी मान्यता", "ସାଥୀ ସ୍ୱୀକୃତି"))

    db.add(Notification(
        employee_id=to_employee_id,
        title=f"{giver.name} recognized you as {labels[0]}!",
        title_hi=f"{giver.name} ने आपको {labels[1]} के रूप में मान्यता दी!",
        title_or=f"{giver.name} ଆପଣଙ୍କୁ {labels[2]} ଭାବରେ ସ୍ୱୀକୃତି ଦେଲେ!",
        message=message,
        notification_type="peer_recognition",
    ))

    # Notification to giver (thank you)
    db.add(Notification(
        employee_id=from_employee_id,
        title=f"You recognized {receiver.name} as {labels[0]}! +25 XP",
        title_hi=f"आपने {receiver.name} को {labels[1]} के रूप में मान्यता दी! +25 XP",
        title_or=f"ଆପଣ {receiver.name} ଙ୍କୁ {labels[2]} ଭାବରେ ସ୍ୱୀକୃତି ଦେଲେ! +25 XP",
        message="Thank you for recognizing your teammate!",
        notification_type="peer_recognition",
    ))

    db.commit()
    return {
        "status": "ok",
        "receiver_xp_earned": 50,
        "giver_xp_earned": 25,
        "receiver_new_xp": receiver.xp,
        "giver_new_xp": giver.xp,
    }, None


def get_peer_recognitions(db: Session, store_id: int):
    """Get all peer recognitions for a store."""
    from ..models import Recognition, Employee

    employees = db.query(Employee).filter(Employee.store_id == store_id).all()
    emp_ids = [e.id for e in employees]

    peer_recs = db.query(Recognition).filter(
        Recognition.employee_id.in_(emp_ids),
        Recognition.message.like("[Peer]%")
    ).order_by(Recognition.created_at.desc()).limit(20).all()

    emp_map = {e.id: e.name for e in employees}
    return [{
        "id": r.id,
        "from_name": r.message.split(":")[0].replace("[Peer] ", "") if "[Peer]" in r.message else "",
        "to_name": emp_map.get(r.employee_id, ""),
        "type": r.recognition_type,
        "message": r.message.split(": ", 1)[1] if ": " in r.message else r.message,
        "xp_awarded": r.xp_awarded,
        "date": r.created_at.isoformat() if r.created_at else "",
    } for r in peer_recs]


# ─── POS-INTEGRATED MICRO-LEARNING ───

POS_MICRO_LESSONS = [
    {
        "id": "pos_tip_1",
        "trigger": "after_sale",
        "title": "Upsell Opportunity: Phone Cases",
        "title_hi": "अपसेल अवसर: फोन केस",
        "title_or": "ଅପସେଲ୍ ସୁଯୋଗ: ଫୋନ୍ କେସ୍",
        "skill_category": "upselling",
        "content": "After every phone sale, offer a case and screen protector. Customers are 3x more likely to buy accessories right after purchase.",
        "content_hi": "हर फोन बिक्री के बाद, केस और स्क्रीन प्रोटेक्टर ऑफर करें। ग्राहक खरीदारी के तुरंत बाद एक्सेसरीज खरीदने की संभावना 3 गुना अधिक होती है।",
        "content_or": "ପ୍ରତ୍ୟେକ ଫୋନ୍ ବିକ୍ରି ପରେ, କେସ୍ ଏବଂ ସ୍କ୍ରିନ୍ ପ୍ରୋଟେକ୍ଟର୍ ଅଫର୍ କରନ୍ତୁ।",
        "xp_reward": 15,
    },
    {
        "id": "pos_tip_2",
        "trigger": "after_sale",
        "title": "Quick Tip: Extended Warranty",
        "title_hi": "त्वरित सुझाव: विस्तारित वारंटी",
        "title_or": "ଶୀଘ୍ର ଟିପ୍ପଣୀ: ବିସ୍ତାରିତ ୱାରେଣ୍ଟି",
        "skill_category": "upselling",
        "content": "Mention warranty before the customer asks. Proactive warranty talk increases attach rate by 40%.",
        "content_hi": "ग्राहक के पूछने से पहले वारंटी के बारे में बताएं। ग्राहक के पूछने से पहले वारंटी की बात करने से अटैच रेट 40% बढ़ जाता है।",
        "content_or": "ଗ୍ରାହକ ପଚାରିବା ପୂର୍ବରୁ ୱାରେଣ୍ଟି ବିଷୟରେ କୁହନ୍ତୁ।",
        "xp_reward": 15,
    },
    {
        "id": "pos_tip_3",
        "trigger": "idle",
        "title": "Quick Review: Samsung vs Redmi",
        "title_hi": "त्वरित समीक्षा: Samsung बनाम Redmi",
        "title_or": "ଶୀଘ୍ର ସମୀକ୍ଷା: Samsung vs Redmi",
        "skill_category": "product_knowledge",
        "content": "Samsung: Better after-sales service, brand trust. Redmi: Better specs at same price. Know both to guide customers effectively.",
        "content_hi": "Samsung: बेहतर आफ्टर-सेल्स सर्विस, ब्रांड ट्रस्ट। Redmi: उसी कीमत में बेहतर स्पेक्स। दोनों को जानें।",
        "content_or": "Samsung: ଭଲ ଆଫ୍ଟର-ସେଲ୍ସ ସେବା। Redmi: ସମାନ ମୂଲ୍ୟରେ ଭଲ ସ୍ପେକ୍ସ।",
        "xp_reward": 10,
    },
    {
        "id": "pos_tip_4",
        "trigger": "idle",
        "title": "Language Tip: Match the Customer",
        "title_hi": "भाषा सुझाव: ग्राहक से मेल खाएं",
        "title_or": "ଭାଷା ଟିପ୍ପଣୀ: ଗ୍ରାହକଙ୍କ ସହ ମେଳ ଖାଆନ୍ତୁ",
        "skill_category": "communication",
        "content": "If a customer speaks Hindi, respond in Hindi. Language matching builds trust and increases close rate by 25%.",
        "content_hi": "अगर ग्राहक हिंदी में बात करे, तो हिंदी में जवाब दें। भाषा मिलाने से भरोसा बढ़ता है।",
        "content_or": "ଯଦି ଗ୍ରାହକ ହିନ୍ଦୀରେ କଥା କୁହନ୍ତି, ତେବେ ହିନ୍ଦୀରେ ଉତ୍ତର ଦିଅନ୍ତୁ।",
        "xp_reward": 10,
    },
    {
        "id": "pos_tip_5",
        "trigger": "before_shift",
        "title": "Morning Motivation: Know Today's Offers",
        "title_hi": "सुबह की प्रेरणा: आज के ऑफर जानें",
        "title_or": "ସକାଳ ପ୍ରେରଣା: ଆଜିର ଅଫର୍ ଜାଣନ୍ତୁ",
        "skill_category": "product_knowledge",
        "content": "Check today's active offers before your shift starts. Being prepared with deal knowledge helps you close sales faster.",
        "content_hi": "शिफ्ट शुरू होने से पहले आज के एक्टिव ऑफर चेक करें। डील ज्ञान के साथ तैयार रहने से बिक्री तेज़ होती है।",
        "content_or": "ଶିଫ୍ଟ ଆରମ୍ଭ ହେବା ପୂର୍ବରୁ ଆଜିର ସକ୍ରିୟ ଅଫର୍ ଯାଞ୍ଚ କରନ୍ତୁ।",
        "xp_reward": 10,
    },
    {
        "id": "pos_tip_6",
        "trigger": "after_sale",
        "title": "Customer Follow-up: Ask for Referral",
        "title_hi": "ग्राहक फॉलो-अप: रेफरल मांगें",
        "title_or": "ଗ୍ରାହକ ଫଲୋ-ଅପ୍: ରେଫରାଲ୍ ମାଗନ୍ତୁ",
        "skill_category": "communication",
        "content": "After a successful sale, ask: 'Do you know anyone else looking for a phone?' Referrals convert at 3x higher rate than cold leads.",
        "content_hi": "सफल बिक्री के बाद पूछें: 'क्या आप किसी ऐसे व्यक्ति को जानते हैं जो फोन ढूंढ रहा है?' रेफरल 3 गुना बेहतर कन्वर्ट होते हैं।",
        "content_or": "ସଫଳ ବିକ୍ରି ପରେ ପଚାରନ୍ତୁ: 'ଆପଣ ଅନ୍ୟ କାହାକୁ ଜାଣନ୍ତି ଯିଏ ଫୋନ୍ ଖୋଜୁଛନ୍ତି?'",
        "xp_reward": 15,
    },
]


def get_pos_micro_lessons(trigger: str = "after_sale", language: str = "en"):
    """Get micro-lessons relevant to current POS context."""
    lessons = [l for l in POS_MICRO_LESSONS if l["trigger"] == trigger]
    result = []
    for lesson in lessons:
        result.append({
            "id": lesson["id"],
            "title": lesson.get(f"title_{language}") or lesson["title"],
            "content": lesson.get(f"content_{language}") or lesson["content"],
            "skill_category": lesson["skill_category"],
            "xp_reward": lesson["xp_reward"],
        })
    return result


def complete_pos_lesson(db: Session, employee_id: int, lesson_id: str):
    """Mark a POS micro-lesson as completed and award XP."""
    from ..models import Employee, SkillScore

    lesson = next((l for l in POS_MICRO_LESSONS if l["id"] == lesson_id), None)
    if not lesson:
        return None, "Lesson not found"

    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        return None, "Employee not found"

    # Award XP
    emp.xp += lesson["xp_reward"]
    emp.level = max(emp.level, 1 + emp.xp // 500)

    # Boost engagement score slightly
    emp.engagement_score = min(100, emp.engagement_score + 0.5)

    # Update relevant skill score
    skill = db.query(SkillScore).filter(
        SkillScore.employee_id == employee_id,
        SkillScore.skill_name == lesson["skill_category"],
        SkillScore.assessment_type == "current"
    ).first()
    if skill:
        skill.score = min(100, skill.score + 1)
    else:
        db.add(SkillScore(
            employee_id=employee_id,
            skill_name=lesson["skill_category"],
            score=51,
            assessment_type="current",
        ))

    db.commit()
    return {
        "xp_earned": lesson["xp_reward"],
        "total_xp": emp.xp,
        "level": emp.level,
    }, None


# ─── DYNAMIC STREAK TRACKING ───

def update_streak(db: Session, employee_id: int):
    """
    Update daily login/activity streak.
    Call this on every login or meaningful activity.
    Tracks consecutive days of engagement.
    """
    from ..models import Employee

    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        return

    today = date.today()
    last_activity = getattr(emp, 'last_activity_date', None)

    if last_activity == today:
        return  # Already counted today

    if last_activity == today - timedelta(days=1):
        # Consecutive day — extend streak
        emp.streak_days += 1
    else:
        # Streak broken — restart
        emp.streak_days = 1

    emp.last_activity_date = today

    # Streak milestones earn badges
    streak_badges = {
        7: "Week Warrior",
        14: "Fortnight Fighter",
        30: "Monthly Master",
    }

    if emp.streak_days in streak_badges:
        from ..models import EmployeeBadge, Badge, Notification
        badge_name = streak_badges[emp.streak_days]
        badge = db.query(Badge).filter(Badge.name == badge_name).first()
        if badge:
            existing = db.query(EmployeeBadge).filter(
                EmployeeBadge.employee_id == employee_id,
                EmployeeBadge.badge_id == badge.id
            ).first()
            if not existing:
                db.add(EmployeeBadge(employee_id=employee_id, badge_id=badge.id))
                db.add(Notification(
                    employee_id=employee_id,
                    title=f"🔥 {emp.streak_days}-day streak! You earned the {badge_name} badge!",
                    title_hi=f"🔥 {emp.streak_days}-दिन की स्ट्रीक! आपने {badge_name} बैज अर्जित किया!",
                    title_or=f"🔥 {emp.streak_days}-ଦିନ ସ୍ଟ୍ରିକ୍! ଆପଣ {badge_name} ବ୍ୟାଜ୍ ଅର୍ଜନ କଲେ!",
                    message=f"Amazing {emp.streak_days}-day learning streak!",
                    notification_type="streak_badge",
                ))

    # Streak XP bonus
    if emp.streak_days % 7 == 0 and emp.streak_days > 0:
        bonus = min(50, emp.streak_days * 2)
        emp.xp += bonus

    db.commit()


def check_and_update_last_activity(db: Session, employee_id: int):
    """Update last_activity_date without modifying streak logic."""
    from ..models import Employee
    from sqlalchemy import update

    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if emp:
        emp.last_activity_date = date.today()
        db.commit()


# ─── AUTOMATIC BADGE EARNING ───

def check_auto_badges(db: Session, employee_id: int):
    """
    Check if employee qualifies for any automatic badges based on performance.
    Called after quiz completion, simulation completion, or training completion.
    """
    from ..models import Employee, SkillScore, EmployeeBadge, Badge, Notification, TrainingProgress, SimulationSession

    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        return []

    earned_badges = []

    # Get all skill scores
    skills = {}
    for sr in db.query(SkillScore).filter(
        SkillScore.employee_id == employee_id,
        SkillScore.assessment_type == "current"
    ).all():
        skills[sr.skill_name] = sr.score

    # Get completed courses
    completed_courses = db.query(TrainingProgress).filter(
        TrainingProgress.employee_id == employee_id,
        TrainingProgress.status == "completed"
    ).count()

    # Get simulation count
    sim_count = db.query(SimulationSession).filter(
        SimulationSession.employee_id == employee_id,
        SimulationSession.status == "completed"
    ).count()

    # Badge rules
    badge_rules = [
        # (badge_name, condition_function, description)
        ("Product Master", lambda: skills.get("product_knowledge", 0) >= 85, "Score 85+ in Product Knowledge"),
        ("Communication Pro", lambda: skills.get("communication", 0) >= 85, "Score 85+ in Communication"),
        ("Upsell Expert", lambda: skills.get("upselling", 0) >= 75, "Score 75+ in Upselling"),
        ("Objection Handler", lambda: skills.get("objection_handling", 0) >= 80, "Score 80+ in Objection Handling"),
        ("Digital Champion", lambda: skills.get("pos_skills", 0) >= 80, "Score 80+ in POS Proficiency"),
        ("Learning Enthusiast", lambda: completed_courses >= 5, "Complete 5+ courses"),
        ("Practice Makes Perfect", lambda: sim_count >= 3, "Complete 3+ AI simulations"),
        ("Rising Star", lambda: emp.overall_skill_score >= 75 and emp.training_completion >= 60, "75+ skill score with 60%+ training"),
        ("Consistent Performer", lambda: emp.streak_days >= 14, "14+ day learning streak"),
        ("XP Collector", lambda: emp.xp >= 2000, "Earn 2000+ XP"),
    ]

    for badge_name, condition_fn, description in badge_rules:
        try:
            if condition_fn():
                badge = db.query(Badge).filter(Badge.name == badge_name).first()
                if badge:
                    existing = db.query(EmployeeBadge).filter(
                        EmployeeBadge.employee_id == employee_id,
                        EmployeeBadge.badge_id == badge.id
                    ).first()
                    if not existing:
                        db.add(EmployeeBadge(employee_id=employee_id, badge_id=badge.id))
                        db.add(Notification(
                            employee_id=employee_id,
                            title=f"🏆 New Badge: {badge_name}!",
                            title_hi=f"🏆 नया बैज: {badge_name}!",
                            title_or=f"🏆 ନୂତନ ବ୍ୟାଜ୍: {badge_name}!",
                            message=description,
                            notification_type="badge_earned",
                        ))
                        earned_badges.append(badge_name)
        except Exception as e:
            logger.warning(f"Badge check error for {badge_name}: {e}")

    if earned_badges:
        db.commit()

    return earned_badges
