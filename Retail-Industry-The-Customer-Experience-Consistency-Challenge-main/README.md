# AI Workforce Coach — Vernacular AI-Powered Retail Employee Learning & Customer Simulation Platform

An AI-powered Vernacular Workforce Coach for Tier-3 Retail. This platform doesn't just train retail employees — it simulates **real human-like customer interactions** powered by LLM (Groq/Gemini), measures employee skills before and after training, identifies skill gaps, provides personalized learning, and proves measurable improvement.

## Core Product Loop

**LEARN → PRACTICE → IMPROVE → EARN → GET RECOGNIZED → TRACK PERFORMANCE → RECEIVE AI RECOMMENDATION → TAKE ACTION**

---

## Features

### AI Customer Companion (LLM-Powered) 🧠
- **Real-time human-like conversations** powered by Groq (Llama 3 / GPT-OSS 120B) or Google Gemini
- **6 realistic customer personas**: Budget-conscious, Confused, Difficult, Price-sensitive, Comparison, Upsell
- **Natural negotiation**: Customers haggle, compare with online prices, ask for discounts
- **Gibberish detection**: Catches keyboard mashes and random characters with polite responses
- **Off-topic detection**: Redirects conversations back to phone shopping
- **Conversation memory**: Customer remembers context throughout the conversation
- **Multilingual support**: English, Hindi, Hinglish, Odia — with automatic language matching
- **Language alignment scoring**: Measures how well employee matches customer's language
- **Graceful fallback**: Works with mock responses if no API key is set

### Before/After Skill Assessment
- Pre-training AI customer simulation
- Post-training AI customer simulation
- Before vs After comparison with improvement tracking
- Skill-wise breakdown across 6 dimensions (Product Knowledge, Communication, Objection Handling, Upselling, Need Identification, Accuracy)

### Skill-Gap Detection & Recommendations
- AI-powered skill-gap engine
- Personalized Next Best Action
- Course recommendations based on weakest skills
- Store-level and employee-level insights

### Micro-Learning
- 7 short courses (2-5 minutes each)
- Quizzes with explanations
- Course completion tracking
- Multilingual course content (English, Hindi, Odia)

### Gamification
- XP system (courses: +50, quizzes: +50, simulations: +75, recognition: +100)
- Badges (Product Expert, POS Champion, Customer Hero, Fast Learner, Most Improved, etc.)
- Levels (Bronze → Silver → Gold → Platinum Associate)
- Learning streaks
- Daily/weekly challenges
- **FairScore Leaderboard**: 40% Performance + 30% Improvement + 20% Learning + 10% Recognition

### Recognition System
- Manager recognition (Customer Hero, Product Expert, Digital Champion, Great Team Player, Most Improved)
- XP and badge awards on recognition
- Notification system

### Manager Dashboard
- **Hierarchical navigation**: Organization → Store → Employee
- Store health scores with color-coded status (Healthy ≥90, Warning 75-89, Critical <75)
- Top 5 / Bottom 5 employees and stores
- AI-powered store insights with actionable recommendations
- Skill heatmap across stores
- Business impact tracking (simulated)

### Store Health Analytics
- **Store Health Score** = PK×30% + POS×25% + Training×20% + CX×15% + Engagement×10%
- Healthy/Warning/Critical status indicators
- Average store health score
- Store performance comparison

### Organization Dashboard
- Total stores, total associates, overall engagement
- Store comparison and analytics
- Top-performing and bottom-performing stores
- AI-generated organization insights

### Employee Management
- Employee list by store with all metrics
- Detailed employee profiles with skill scores
- Training progress tracking
- Badge and recognition history
- Simulation history with pre/post comparison

### Multilingual Support
- English, Hindi, and Odia
- Full UI translation (300+ translated strings)
- AI customer conversations in employee's preferred language
- Language mismatch detection during simulations

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | FastAPI + SQLite + Python |
| **Frontend** | Vanilla JavaScript SPA + Tailwind CSS CDN + Chart.js |
| **AI Engine** | Groq (GPT-OSS 120B) / Google Gemini 3.6 Flash |
| **Authentication** | JWT-based role-based access |
| **Database** | SQLite with SQLAlchemy ORM |
| **Build** | No build step required |

---

## Demo Accounts

| Role | Email | Password | Access |
|------|-------|----------|--------|
| Employee | employee@demo.com | employee123 | Dashboard, Courses, AI Simulation, Challenges, Leaderboard |
| Manager | manager@demo.com | manager123 | Organization Dashboard, Store/Employee drill-down, Recognition |
| Admin | admin@demo.com | admin123 | Admin Dashboard, Employee/Store/Course management |

---

## Quick Start

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. (Optional) Set AI API Key for Human-Like Conversations
```bash
# Option A: Groq (Recommended - Free, 30 req/min)
export GROQ_API_KEY="gsk_your_key_here"
# Get free key at https://console.groq.com

# Option B: Google Gemini (Free, 20 req/day)
export GEMINI_API_KEY="your_key_here"
# Get free key at https://aistudio.google.com
```

> **Without an API key**, the simulation falls back to mock responses automatically.

### 3. Start the Server
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. Open in Browser
```
http://localhost:8000
```

---

## Project Structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI app setup & routing
│   ├── auth.py                  # JWT authentication
│   ├── database.py              # SQLite database config
│   ├── models/
│   │   └── __init__.py          # SQLAlchemy models (User, Employee, Course, etc.)
│   ├── routers/
│   │   ├── auth.py              # Login/register endpoints
│   │   ├── employee.py          # Employee dashboard API
│   │   ├── courses.py           # Courses, quizzes & progress API
│   │   ├── simulation.py        # AI customer simulation API
│   │   ├── manager.py           # Manager dashboard API
│   │   ├── manager_hierarchical.py  # Org → Store → Employee drill-down API
│   │   ├── challenges.py        # Gamification & leaderboard API
│   │   └── admin.py             # Admin management API
│   ├── services/
│   │   ├── ai_simulator.py      # Mock AI simulator + language detection + evaluation
│   │   └── llm_customer.py      # LLM-powered customer (Groq/Gemini) + gibberish detection
│   └── seed/
│       └── seed_data.py         # 10 stores, 127+ associates, courses, badges
├── static/
│   ├── index.html               # HTML shell
│   ├── app.js                   # SPA (~1800 lines) - all UI components
│   ├── i18n.json                # English/Hindi/Odia translations
│   ├── hi_responses.json        # Hindi AI customer responses (mock fallback)
│   └── or_responses.json        # Odia AI customer responses (mock fallback)
└── requirements.txt
```

---

## AI Customer Companion — How It Works

### Conversation Flow
```
Employee types message
        ↓
   Gibberish detected? → "Sorry, I didn't understand. Can you say again?"
        ↓ No
   Off-topic detected? → "I'm here to buy a phone. Let's focus on that."
        ↓ No
   Groq API available? → Generate human-like response (GPT-OSS 120B)
        ↓ No
   Gemini API available? → Generate human-like response (Gemini 3.6 Flash)
        ↓ No
   Mock response → Pre-canned response from JSON files
```

### Example Conversation
```
Customer: Hi, I'm looking for a phone under Rs 15,000. I mostly care about camera and battery.

Employee: Hello! Welcome to our store. What features are most important to you?

Customer: Camera aur battery life sabse important hai, aur mera budget ₹15,000 se thoda kam ka hai. 🙏

Employee: We have the Samsung Galaxy A15 with 50MP camera for Rs 13,999.

Customer: Acha lag raha hai, lekin kya aap thoda aur discount de sakte hain?
          Online price thoda kam mil raha tha. Aur warranty details bhi bata dijiye.

Employee: asjdkla!!!   (gibberish)

Customer: Sorry, can you say that clearly?

Employee: Did you watch the cricket match? India won!   (off-topic)

Customer: Sorry, but I'm here to buy a phone. Can we focus on that?
```

---

## Store Health Score Calculation

| Metric | Weight |
|--------|--------|
| Product Knowledge | 30% |
| POS Proficiency | 25% |
| Training Completion | 20% |
| Customer Experience | 15% |
| Employee Engagement | 10% |

| Status | Score Range |
|--------|------------|
| 🟢 Healthy | 90–100 |
| 🟡 Warning | 75–89 |
| 🔴 Critical | Below 75 |

---

## Prototype Scale

| Metric | Value |
|--------|-------|
| Stores | 10 (Bhubaneswar, Cuttack, Berhampur, Sambalpur, Rourkela, Puri, Jeypore, Balasore, Dhenkanal, Kendujhar) |
| Associates | 127+ (14 handcrafted + auto-generated) |
| Courses | 7 (Product Knowledge, POS, Communication, Objection Handling, Upselling, Need Identification, Recommendation) |
| Customer Personas | 6 (Budget, Confused, Difficult, Comparison, Upsell, Price-sensitive) |
| Languages | 3 (English, Hindi, Odia) |

**Designed to scale to 1,200+ Stores | 3,000+ Associates Monthly**

---

## Key Differentiators for Hackathon

1. **Real LLM-Powered AI Customer** — Not mock responses, actual human-like conversations
2. **Gibberish & Off-topic Detection** — Smart input validation
3. **Multilingual Vernacular Support** — Hindi/Hinglish/Odia for Tier-3 towns
4. **Language Alignment Scoring** — Measures if employee matches customer's language
5. **Before/After Skill Assessment** — Proves measurable improvement
6. **Store Health Analytics** — Weighted scoring with actionable insights
7. **FairScore Leaderboard** — Balanced ranking beyond just XP
8. **Zero Cost AI** — Groq free tier (30 req/min) or Gemini free tier

---

## License

MIT
