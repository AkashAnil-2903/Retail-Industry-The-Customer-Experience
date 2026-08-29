from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from ..database import Base


class UserRole(str, enum.Enum):
    EMPLOYEE = "employee"
    MANAGER = "manager"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="employee")
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)


class Store(Base):
    __tablename__ = "stores"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False)
    region = Column(String, default="North")
    city = Column(String, default="")
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)


class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    name = Column(String, nullable=False)
    preferred_language = Column(String, default="en")
    xp = Column(Integer, default=0)
    level = Column(Integer, default=1)
    rank = Column(String, default="Bronze Associate")
    streak_days = Column(Integer, default=0)
    pos_adoption = Column(Float, default=50.0)
    engagement_score = Column(Float, default=50.0)
    overall_skill_score = Column(Float, default=50.0)
    training_completion = Column(Float, default=0.0)
    upsell_conversion = Column(Float, default=10.0)
    has_completed_pre_assessment = Column(Boolean, default=False)
    has_completed_post_assessment = Column(Boolean, default=False)
    last_activity_date = Column(DateTime, nullable=True)

    user = relationship("User", backref="employee_profile")
    store = relationship("Store", backref="employees")


class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    title_hi = Column(String, default="")
    title_or = Column(String, default="")
    description = Column(Text, default="")
    description_hi = Column(Text, default="")
    description_or = Column(Text, default="")
    content = Column(Text, default="")
    content_hi = Column(Text, default="")
    content_or = Column(Text, default="")
    duration_minutes = Column(Integer, default=5)
    difficulty = Column(String, default="beginner")
    skill_category = Column(String, default="general")
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)


class Quiz(Base):
    __tablename__ = "quizzes"
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String, nullable=False)
    title_hi = Column(String, default="")
    title_or = Column(String, default="")
    passing_score = Column(Integer, default=60)

    course = relationship("Course", backref="quizzes")


class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    text = Column(Text, nullable=False)
    text_hi = Column(Text, default="")
    text_or = Column(Text, default="")
    option_a = Column(String, nullable=False)
    option_b = Column(String, nullable=False)
    option_c = Column(String, nullable=False)
    option_d = Column(String, nullable=False)
    correct_answer = Column(String, nullable=False)
    explanation = Column(Text, default="")
    explanation_hi = Column(Text, default="")
    explanation_or = Column(Text, default="")

    quiz = relationship("Quiz", backref="questions")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    score = Column(Float, nullable=False)
    answers = Column(Text, default="{}")
    completed_at = Column(DateTime, default=datetime.utcnow)


class TrainingProgress(Base):
    __tablename__ = "training_progress"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    status = Column(String, default="not_started")  # not_started, in_progress, completed
    progress_percent = Column(Float, default=0.0)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)


class SkillScore(Base):
    __tablename__ = "skill_scores"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    skill_name = Column(String, nullable=False)
    score = Column(Float, default=50.0)
    assessment_type = Column(String, default="current")  # pre, post, current
    updated_at = Column(DateTime, default=datetime.utcnow)


class SimulationSession(Base):
    __tablename__ = "simulation_sessions"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    scenario_id = Column(Integer, ForeignKey("customer_scenarios.id"), nullable=False)
    assessment_type = Column(String, default="pre")  # pre, post
    status = Column(String, default="active")  # active, completed
    overall_score = Column(Float, nullable=True)
    product_knowledge_score = Column(Float, nullable=True)
    need_identification_score = Column(Float, nullable=True)
    communication_score = Column(Float, nullable=True)
    objection_handling_score = Column(Float, nullable=True)
    upselling_score = Column(Float, nullable=True)
    accuracy_score = Column(Float, nullable=True)
    strengths = Column(Text, default="[]")
    weaknesses = Column(Text, default="[]")
    missed_opportunities = Column(Text, default="[]")
    recommendation = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class CustomerScenario(Base):
    __tablename__ = "customer_scenarios"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    persona = Column(String, nullable=False)
    persona_hi = Column(String, default="")
    persona_or = Column(String, default="")
    customer_goal = Column(Text, nullable=False)
    customer_goal_hi = Column(Text, default="")
    customer_goal_or = Column(Text, default="")
    budget = Column(String, default="")
    personality = Column(String, default="neutral")
    difficulty = Column(String, default="medium")
    hidden_objections = Column(Text, default="[]")
    opening_message = Column(Text, nullable=False)
    opening_message_hi = Column(Text, default="")
    opening_message_or = Column(Text, default="")
    skill_category = Column(String, default="general")
    is_active = Column(Boolean, default=True)


class SimulationMessage(Base):
    __tablename__ = "simulation_messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("simulation_sessions.id"), nullable=False)
    role = Column(String, nullable=False)  # customer, employee
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Challenge(Base):
    __tablename__ = "challenges"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    title_hi = Column(String, default="")
    title_or = Column(String, default="")
    description = Column(Text, default="")
    description_hi = Column(Text, default="")
    description_or = Column(Text, default="")
    challenge_type = Column(String, default="daily")  # daily, weekly, pos, customer, skill
    xp_reward = Column(Integer, default=50)
    target_value = Column(Integer, default=1)
    skill_category = Column(String, default="general")
    is_active = Column(Boolean, default=True)


class EmployeeChallenge(Base):
    __tablename__ = "employee_challenges"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), nullable=False)
    progress = Column(Integer, default=0)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)


class Badge(Base):
    __tablename__ = "badges"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    name_hi = Column(String, default="")
    name_or = Column(String, default="")
    description = Column(Text, default="")
    description_hi = Column(Text, default="")
    description_or = Column(Text, default="")
    icon = Column(String, default="🏆")
    skill_category = Column(String, default="general")


class EmployeeBadge(Base):
    __tablename__ = "employee_badges"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    badge_id = Column(Integer, ForeignKey("badges.id"), nullable=False)
    earned_at = Column(DateTime, default=datetime.utcnow)


class Recognition(Base):
    __tablename__ = "recognitions"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recognition_type = Column(String, nullable=False)  # customer_hero, product_expert, digital_champion, great_team_player, most_improved
    message = Column(Text, default="")
    xp_awarded = Column(Integer, default=100)
    created_at = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", backref="recognitions_given")


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    title = Column(String, nullable=False)
    title_hi = Column(String, default="")
    title_or = Column(String, default="")
    message = Column(Text, default="")
    message_hi = Column(Text, default="")
    message_or = Column(Text, default="")
    is_read = Column(Boolean, default=False)
    notification_type = Column(String, default="info")
    created_at = Column(DateTime, default=datetime.utcnow)
