from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import json
import random

from ..database import get_db
from ..models import *
from ..auth import get_current_user
from ..services.engagement_features import check_auto_badges
from ..services.ai_simulator import (
    get_mock_customer_response, evaluate_simulation, get_mock_customer_opening,
    detect_language, detect_language_from_messages
)
from ..services.llm_customer import (
    get_llm_response, is_gibberish, get_gibberish_response,
    is_off_topic, get_off_topic_response
)

router = APIRouter(prefix="/api/simulation", tags=["simulation"])


@router.get("/scenarios")
def list_scenarios(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    scenarios = db.query(CustomerScenario).filter(CustomerScenario.is_active == True).all()
    return [{
        "id": s.id,
        "name": s.name,
        "persona": s.persona,
        "difficulty": s.difficulty,
        "skill_category": s.skill_category,
        "budget": s.budget,
    } for s in scenarios]


@router.post("/start")
def start_simulation(payload: dict, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.user_id == user.id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    assessment_type = payload.get("assessment_type", "pre")
    scenario_id = payload.get("scenario_id")

    # Auto-select scenario if not provided
    if not scenario_id:
        if assessment_type == "pre":
            scenario = db.query(CustomerScenario).filter(
                CustomerScenario.skill_category == "product_knowledge",
                CustomerScenario.is_active == True
            ).first()
        else:
            scenario = db.query(CustomerScenario).filter(
                CustomerScenario.skill_category.in_(["objection_handling", "upselling"]),
                CustomerScenario.is_active == True
            ).first()
        if not scenario:
            scenario = db.query(CustomerScenario).filter(CustomerScenario.is_active == True).first()
    else:
        scenario = db.query(CustomerScenario).filter(CustomerScenario.id == scenario_id).first()

    if not scenario:
        raise HTTPException(status_code=404, detail="No scenarios available")

    # Get language - use employee's preferred language
    lang = emp.preferred_language or "en"

    # Get opening message based on language
    opening = scenario.opening_message
    if lang == "hi":
        opening = scenario.opening_message_hi or scenario.opening_message
    elif lang == "or":
        opening = scenario.opening_message_or or scenario.opening_message

    # Detect the conversation language from the opening message
    conversation_lang = detect_language(opening)

    # Create session
    session = SimulationSession(
        employee_id=emp.id,
        scenario_id=scenario.id,
        assessment_type=assessment_type,
        status="active",
    )
    db.add(session)
    db.flush()

    # Add opening message
    msg = SimulationMessage(session_id=session.id, role="customer", content=opening)
    db.add(msg)
    db.commit()

    return {
        "session_id": session.id,
        "scenario": {
            "id": scenario.id,
            "name": scenario.name,
            "persona": scenario.persona,
            "budget": scenario.budget,
            "difficulty": scenario.difficulty,
        },
        "opening_message": opening,
        "assessment_type": assessment_type,
        "conversation_language": conversation_lang,
        "language_hint": _get_language_hint(conversation_lang),
    }


@router.post("/{session_id}/respond")
def customer_respond(session_id: int, payload: dict, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.user_id == user.id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    session = db.query(SimulationSession).filter(SimulationSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != "active":
        raise HTTPException(status_code=400, detail="Session is not active")

    employee_message = payload.get("message", "").strip()
    if not employee_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Save employee message
    emp_msg = SimulationMessage(session_id=session_id, role="employee", content=employee_message)
    db.add(emp_msg)
    db.flush()

    # Get scenario
    scenario = db.query(CustomerScenario).filter(CustomerScenario.id == session.scenario_id).first()

    # Get all messages for this session
    all_messages = db.query(SimulationMessage).filter(
        SimulationMessage.session_id == session_id
    ).order_by(SimulationMessage.created_at).all()

    employee_turn_count = sum(1 for m in all_messages if m.role == "employee")

    # Determine the conversation language
    customer_msgs_list = [{"role": m.role, "content": m.content} for m in all_messages if m.role == "customer"]
    detected_conv_lang = detect_language_from_messages(customer_msgs_list)

    # Detect employee message language
    emp_lang = detect_language(employee_message)

    # Check for language mismatch
    lang_mismatch = False
    lang_hint = None

    if detected_conv_lang in ("hi", "hinglish", "or") and emp_lang == "en":
        lang_mismatch = True
        lang_hint = _get_mismatch_hint(detected_conv_lang)

    # ─── GIBBERISH DETECTION ───
    if is_gibberish(employee_message):
        response = get_gibberish_response(detected_conv_lang)
        gibberish_msg = SimulationMessage(session_id=session_id, role="customer", content=response)
        db.add(gibberish_msg)
        db.commit()
        return {
            "customer_response": response,
            "turn_count": employee_turn_count,
            "should_end": False,
            "conversation_language": detected_conv_lang,
            "language_mismatch": lang_mismatch,
            "language_hint": lang_hint,
        }

    # ─── OFF-TOPIC DETECTION ───
    if is_off_topic(employee_message):
        response = get_off_topic_response(detected_conv_lang)
        off_topic_msg = SimulationMessage(session_id=session_id, role="customer", content=response)
        db.add(off_topic_msg)
        db.commit()
        return {
            "customer_response": response,
            "turn_count": employee_turn_count,
            "should_end": False,
            "conversation_language": detected_conv_lang,
            "language_mismatch": lang_mismatch,
            "language_hint": lang_hint,
        }

    # ─── LLM-POWERED RESPONSE (with mock fallback) ───
    lang = emp.preferred_language or "en"
    conversation_history = [{"role": m.role, "content": m.content} for m in all_messages]

    # Try LLM first (Groq → Gemini → None)
    response = get_llm_response(
        persona=scenario.persona,
        conversation_history=conversation_history,
        employee_message=employee_message,
        language=lang,
        conversation_language=detected_conv_lang,
    )

    # Fallback to mock if LLM not available
    if not response:
        response = get_mock_customer_response(
            persona=scenario.persona,
            conversation_turn=employee_turn_count,
            employee_message=employee_message,
            language=lang,
            conversation_language=detected_conv_lang,
        )

    # Save customer response
    cust_msg = SimulationMessage(session_id=session_id, role="customer", content=response)
    db.add(cust_msg)
    db.flush()

    # Check if conversation should end (after ~6 turns or closing message)
    closing_indicators = ["okay, let me think", "i'll come back", "i'll take it", "i'll buy",
                          "let's go with", "you've convinced", "i trust you", "alright",
                          "theek hai", "sochta hoon", "kal wapas", "le leta hoon",
                          "le lete hain", "kar dete hain"]
    should_end = employee_turn_count >= 6 or any(ind in response.lower() for ind in closing_indicators)

    db.commit()

    return {
        "customer_response": response,
        "turn_count": employee_turn_count,
        "should_end": should_end,
        "conversation_language": detected_conv_lang,
        "language_mismatch": lang_mismatch,
        "language_hint": lang_hint,
    }


@router.post("/{session_id}/evaluate")
def evaluate_session(session_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.user_id == user.id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    session = db.query(SimulationSession).filter(SimulationSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get all messages
    messages = db.query(SimulationMessage).filter(
        SimulationMessage.session_id == session_id
    ).order_by(SimulationMessage.created_at).all()

    # Get current skills for evaluation context
    skill_records = db.query(SkillScore).filter(
        SkillScore.employee_id == emp.id,
        SkillScore.assessment_type == "current"
    ).all()
    pre_skills = {sr.skill_name: sr.score for sr in skill_records}

    scenario = db.query(CustomerScenario).filter(CustomerScenario.id == session.scenario_id).first()
    scenario_info = {"pre_skills": pre_skills if session.assessment_type == "pre" else {}}

    # Evaluate
    evaluation = evaluate_simulation(
        [{"role": m.role, "content": m.content} for m in messages],
        scenario_info,
    )

    # Update session with scores
    session.overall_score = evaluation["overall_score"]
    session.product_knowledge_score = evaluation["product_knowledge"]
    session.need_identification_score = evaluation["need_identification"]
    session.communication_score = evaluation["communication"]
    session.objection_handling_score = evaluation["objection_handling"]
    session.upselling_score = evaluation["upselling"]
    session.accuracy_score = evaluation["accuracy"]
    session.strengths = json.dumps(evaluation["strengths"])
    session.weaknesses = json.dumps(evaluation["weaknesses"])
    session.missed_opportunities = json.dumps(evaluation["missed_opportunities"])
    session.recommendation = evaluation["recommendation"]
    session.status = "completed"
    session.completed_at = datetime.utcnow()

    # Update employee skill scores
    if session.assessment_type == "pre":
        emp.has_completed_pre_assessment = True
    else:
        emp.has_completed_post_assessment = True

    skill_updates = {
        "product_knowledge": evaluation["product_knowledge"],
        "communication": evaluation["communication"],
        "objection_handling": evaluation["objection_handling"],
        "upselling": evaluation["upselling"],
        "need_identification": evaluation["need_identification"],
    }

    for skill_name, score in skill_updates.items():
        existing = db.query(SkillScore).filter(
            SkillScore.employee_id == emp.id,
            SkillScore.skill_name == skill_name,
            SkillScore.assessment_type == "current"
        ).first()
        if existing:
            if session.assessment_type == "pre":
                existing.score = score
            else:
                existing.score = min(100, max(existing.score, score))
        else:
            db.add(SkillScore(
                employee_id=emp.id,
                skill_name=skill_name,
                score=score,
                assessment_type="current",
            ))

    # Award XP
    emp.xp += 75

    # Update overall skill score
    all_current = db.query(SkillScore).filter(
        SkillScore.employee_id == emp.id,
        SkillScore.assessment_type == "current"
    ).all()
    if all_current:
        emp.overall_skill_score = round(sum(s.score for s in all_current) / len(all_current), 1)

    db.commit()

    # Check for auto-earned badges
    new_badges = check_auto_badges(db, emp.id)

    # Get pre-assessment comparison if this is post
    pre_comparison = None
    if session.assessment_type == "post":
        pre_session = db.query(SimulationSession).filter(
            SimulationSession.employee_id == emp.id,
            SimulationSession.assessment_type == "pre",
            SimulationSession.status == "completed"
        ).order_by(SimulationSession.created_at.desc()).first()

        if pre_session:
            pre_comparison = {
                "pre_overall": pre_session.overall_score,
                "post_overall": evaluation["overall_score"],
                "improvement": evaluation["overall_score"] - (pre_session.overall_score or 0),
                "pre_skills": {
                    "product_knowledge": pre_session.product_knowledge_score,
                    "need_identification": pre_session.need_identification_score,
                    "communication": pre_session.communication_score,
                    "objection_handling": pre_session.objection_handling_score,
                    "upselling": pre_session.upselling_score,
                },
                "post_skills": {
                    "product_knowledge": evaluation["product_knowledge"],
                    "need_identification": evaluation["need_identification"],
                    "communication": evaluation["communication"],
                    "objection_handling": evaluation["objection_handling"],
                    "upselling": evaluation["upselling"],
                },
            }

    return {
        "evaluation": evaluation,
        "assessment_type": session.assessment_type,
        "pre_comparison": pre_comparison,
        "xp_earned": 75,
    }


@router.get("/{session_id}/messages")
def get_messages(session_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    messages = db.query(SimulationMessage).filter(
        SimulationMessage.session_id == session_id
    ).order_by(SimulationMessage.created_at).all()

    return [{"role": m.role, "content": m.content} for m in messages]


def _get_language_hint(lang: str) -> str:
    """Get a hint message about the conversation language."""
    hints = {
        "hi": "This customer prefers to communicate in Hindi.",
        "hinglish": "This customer speaks in Hinglish (Hindi-English mix).",
        "or": "This customer prefers to communicate in Odia.",
        "en": None,  # No hint needed for English
    }
    return hints.get(lang)


def _get_mismatch_hint(customer_lang: str) -> str:
    """Get a hint when there's a language mismatch."""
    hints = {
        "hi": "Language mismatch detected. Try responding in Hindi to match the customer.",
        "hinglish": "Language mismatch detected. Try responding in Hindi/Hinglish to match the customer.",
        "or": "Language mismatch detected. Try responding in Odia to match the customer.",
    }
    return hints.get(customer_lang, "Try matching the customer's language for better communication.")
