"""Seed the database with 10 stores and 125+ associates for Tier-3 retail workforce engagement prototype."""
from datetime import datetime
from sqlalchemy.orm import Session
from ..models import *
from ..auth import get_password_hash
import random

MALE = ["Rahul","Amit","Deepak","Rajesh","Sanjay","Manoj","Vikram","Suresh","Prakash","Dinesh",
        "Ravi","Sunil","Ashok","Mahesh","Anil","Vinod","Ramesh","Naresh","Kiran","Ajay",
        "Vijay","Santosh","Mohan","Shankar","Bharat","Ganesh","Mukesh","Pankaj","Tarun","Arun",
        "Naveen","Subhash","Sanjeev","Rajendra","Biswajit","Jagdish","Hemant","Pradeep","Gopal",
        "Krishna","Bikash","Manas","Rakesh","Pranab","Atul","Jayanta","Sudhir","Tapas","Ranjan","Satish"]
FEMALE = ["Priya","Sunita","Neha","Kavita","Pooja","Anita","Saraswati","Meena","Suman","Rita",
          "Asha","Geeta","Rekha","Vandana","Nisha","Mamta","Seema","Kamla","Jyoti","Lata",
          "Usha","Gita","Anjali","Deepa","Shikha","Pallavi","Madhavi","Aparna","Manjula","Vidya",
          "Padma","Sujata","Swati","Pratibha","Kalpana","Veena","Shobha","Smita","Aruna","Bharati"]
LAST = ["Kumar","Patel","Singh","Devi","Mohapatra","Sahoo","Behera","Mohanty","Nayak","Rout",
        "Das","Jena","Tripathi","Panda","Mishra","Biswal","Barik","Lenka","Pradhan","Satapathy",
        "Dash","Panigrahi","Sethi","Swain","Gochhayat","Choudhury","Bhoi","Meher","Srichandan","Jali"]

STORES = [
    ("Store 101 - Bhubaneswar Hub","STR-101","East","Bhubaneswar"),
    ("Store 102 - Cuttack Main","STR-102","East","Cuttack"),
    ("Store 103 - Berhampur Express","STR-103","East","Berhampur"),
    ("Store 104 - Sambalpur Center","STR-104","East","Sambalpur"),
    ("Store 105 - Rourkela Plaza","STR-105","East","Rourkela"),
    ("Store 106 - Puri Beach Road","STR-106","East","Puri"),
    ("Store 107 - Jeypore Town","STR-107","East","Jeypore"),
    ("Store 108 - Balasore Market","STR-108","East","Balasore"),
    ("Store 109 - Dhenkanal Cross","STR-109","East","Dhenkanal"),
    ("Store 110 - Kendujhar Road","STR-110","East","Kendujhar"),
]

LANGS = ["en","hi","or"]
RANKS = ["Bronze Associate","Bronze Associate","Bronze Associate","Silver Associate",
         "Silver Associate","Silver Associate","Gold Associate","Platinum Associate"]
SKILLS = ["product_knowledge","pos_skills","communication","objection_handling","upselling","need_identification"]


def _profile():
    idx = random.choices([0,1,2], weights=[35,45,20])[0]
    if idx == 0:
        return dict(engagement=random.randint(80,98), overall_skill=random.randint(75,95),
                    training_comp=random.randint(80,100), xp=random.randint(1800,2800),
                    level=random.randint(6,10), streak=random.randint(10,20),
                    pos_adoption=random.randint(70,95), upsell=random.randint(60,85))
    elif idx == 1:
        return dict(engagement=random.randint(55,79), overall_skill=random.randint(45,74),
                    training_comp=random.randint(45,79), xp=random.randint(600,1700),
                    level=random.randint(2,5), streak=random.randint(2,9),
                    pos_adoption=random.randint(40,70), upsell=random.randint(25,55))
    else:
        return dict(engagement=random.randint(25,54), overall_skill=random.randint(25,44),
                    training_comp=random.randint(15,44), xp=random.randint(100,599),
                    level=random.randint(1,2), streak=random.randint(0,2),
                    pos_adoption=random.randint(15,39), upsell=random.randint(10,30))


def _skills(overall):
    return {s: max(15, min(98, overall + random.randint(-10, 10))) for s in SKILLS}


def seed_database(db: Session):
    if db.query(User).first():
        return

    # USERS
    users = {}
    for email, pwd, role in [("employee@demo.com","employee123","employee"),
                              ("manager@demo.com","manager123","manager"),
                              ("admin@demo.com","admin123","admin")]:
        u = User(email=email, password_hash=get_password_hash(pwd), role=role)
        db.add(u); db.flush()
        users[role] = u

    # STORES
    stores = []
    for name, code, region, city in STORES:
        s = Store(name=name, code=code, region=region, city=city, manager_id=users["manager"].id)
        db.add(s); db.flush()
        stores.append(s)

    # KEY EMPLOYEES (14 handcrafted)
    key = [
        dict(name="Rahul Kumar",si=0,lang="hi",xp=1240,lv=5,rank="Silver Associate",streak=5,pa=43,eng=84,sk=50,tc=78,up=35,pre=True,
             skills=dict(product_knowledge=52,pos_skills=43,communication=61,upselling=35,objection_handling=42,need_identification=48)),
        dict(name="Priya Patel",si=0,lang="en",xp=2100,lv=7,rank="Gold Associate",streak=12,pa=85,eng=91,sk=85,tc=95,up=72,
             skills=dict(product_knowledge=88,pos_skills=85,communication=90,upselling=72,objection_handling=80,need_identification=87)),
        dict(name="Amit Singh",si=1,lang="hi",xp=1800,lv=6,rank="Silver Associate",streak=8,pa=62,eng=76,sk=68,tc=82,up=55,
             skills=dict(product_knowledge=72,pos_skills=62,communication=74,upselling=55,objection_handling=65,need_identification=70)),
        dict(name="Sunita Devi",si=1,lang="or",xp=950,lv=4,rank="Bronze Associate",streak=3,pa=38,eng=62,sk=48,tc=55,up=30,
             skills=dict(product_knowledge=55,pos_skills=38,communication=58,upselling=30,objection_handling=40,need_identification=45)),
        dict(name="Deepak Mohapatra",si=2,lang="or",xp=1500,lv=5,rank="Silver Associate",streak=6,pa=58,eng=73,sk=62,tc=70,up=48,
             skills=dict(product_knowledge=65,pos_skills=58,communication=70,upselling=48,objection_handling=55,need_identification=62)),
        dict(name="Neha Sahoo",si=0,lang="hi",xp=2400,lv=8,rank="Gold Associate",streak=15,pa=90,eng=95,sk=88,tc=100,up=78,
             skills=dict(product_knowledge=90,pos_skills=90,communication=92,upselling=78,objection_handling=85,need_identification=88)),
        dict(name="Rajesh Behera",si=3,lang="hi",xp=1100,lv=4,rank="Bronze Associate",streak=4,pa=52,eng=68,sk=55,tc=62,up=42,
             skills=dict(product_knowledge=60,pos_skills=52,communication=62,upselling=42,objection_handling=50,need_identification=55)),
        dict(name="Kavita Mohanty",si=4,lang="en",xp=1900,lv=6,rank="Silver Associate",streak=9,pa=75,eng=82,sk=74,tc=88,up=62,
             skills=dict(product_knowledge=78,pos_skills=75,communication=80,upselling=62,objection_handling=70,need_identification=76)),
        dict(name="Sanjay Nayak",si=2,lang="or",xp=800,lv=3,rank="Bronze Associate",streak=2,pa=35,eng=55,sk=42,tc=45,up=28,
             skills=dict(product_knowledge=48,pos_skills=35,communication=52,upselling=28,objection_handling=38,need_identification=42)),
        dict(name="Pooja Rout",si=5,lang="hi",xp=1650,lv=6,rank="Silver Associate",streak=7,pa=70,eng=79,sk=71,tc=85,up=58,
             skills=dict(product_knowledge=75,pos_skills=70,communication=78,upselling=58,objection_handling=67,need_identification=73)),
        dict(name="Manoj Das",si=6,lang="or",xp=700,lv=3,rank="Bronze Associate",streak=1,pa=40,eng=50,sk=45,tc=40,up=32,
             skills=dict(product_knowledge=50,pos_skills=40,communication=55,upselling=32,objection_handling=42,need_identification=46)),
        dict(name="Anita Jena",si=7,lang="hi",xp=1300,lv=5,rank="Silver Associate",streak=5,pa=60,eng=74,sk=64,tc=75,up=50,
             skills=dict(product_knowledge=68,pos_skills=60,communication=72,upselling=50,objection_handling=58,need_identification=65)),
        dict(name="Vikram Tripathi",si=3,lang="hi",xp=2000,lv=7,rank="Gold Associate",streak=11,pa=82,eng=88,sk=82,tc=92,up=70,
             skills=dict(product_knowledge=85,pos_skills=82,communication=86,upselling=70,objection_handling=78,need_identification=83)),
        dict(name="Saraswati Panda",si=4,lang="or",xp=600,lv=2,rank="Bronze Associate",streak=0,pa=30,eng=45,sk=38,tc=30,up=25,
             skills=dict(product_knowledge=42,pos_skills=30,communication=48,upselling=25,objection_handling=35,need_identification=40)),
    ]

    employees = []
    used = set()
    for i, d in enumerate(key):
        e = Employee(user_id=users["employee"].id if i==0 else None,
                     store_id=stores[d["si"]].id, name=d["name"],
                     preferred_language=d["lang"], xp=d["xp"], level=d["lv"],
                     rank=d["rank"], streak_days=d["streak"], pos_adoption=d["pa"],
                     engagement_score=d["eng"], overall_skill_score=d["sk"],
                     training_completion=d["tc"], upsell_conversion=d["up"],
                     has_completed_pre_assessment=d.get("pre", False))
        db.add(e); db.flush(); employees.append(e); used.add(d["name"])
        for sn, sc in d["skills"].items():
            db.add(SkillScore(employee_id=e.id, skill_name=sn, score=sc, assessment_type="current"))

    # AUTO-GENERATED (fill to 125+)
    target = 125
    for si, store in enumerate(stores):
        base = (target - len(key)) // len(stores) + (1 if si < 3 else 0)
        for _ in range(base):
            for _ in range(200):
                f = random.choice(FEMALE if random.random() < 0.45 else MALE)
                name = f + " " + random.choice(LAST)
                if name not in used:
                    used.add(name); break
            p = _profile()
            ri = min(p["level"]//2 + (1 if p["level"]>=3 else 0), len(RANKS)-1)
            e = Employee(store_id=store.id, name=name, preferred_language=random.choice(LANGS),
                         xp=p["xp"], level=p["level"], rank=RANKS[ri],
                         streak_days=p["streak"], pos_adoption=p["pos_adoption"],
                         engagement_score=p["engagement"], overall_skill_score=p["overall_skill"],
                         training_completion=p["training_comp"], upsell_conversion=p["upsell"],
                         has_completed_pre_assessment=random.random()<0.3)
            db.add(e); db.flush(); employees.append(e)
            for sn, sc in _skills(p["overall_skill"]).items():
                db.add(SkillScore(employee_id=e.id, skill_name=sn, score=sc, assessment_type="current"))

    # COURSES (English only for content - I18N handles translations)
    courses_data = [
        ("Product Knowledge Basics","Master essential product features, specs, and comparison skills.",
         "## Product Knowledge Essentials\n\n### Key Topics:\n1. **Understanding Product Specifications**\n   - Processor, RAM, Storage, Display, Battery\n2. **Product Comparison**\n   - How to compare products within the same price range\n3. **Feature-Benefit Mapping**\n   - Don't just list features, explain benefits", 4, "beginner", "product_knowledge"),
        ("Digital POS Mastery","Learn to efficiently use the digital Point-of-Sale system.",
         "## Digital POS Mastery\n\n### Key Topics:\n1. **POS System Basics**\n2. **Transaction Flow**\n   - Scanning, discounts, UPI/card/cash\n3. **Handling Issues**", 3, "beginner", "pos_skills"),
        ("Customer Need Identification","Master the art of asking the right questions.",
         "## Customer Need Identification\n\n### Key Topics:\n1. The 5 Essential Questions\n2. Active Listening\n3. Need-Based Recommendation", 3, "beginner", "need_identification"),
        ("Objection Handling Mastery","Learn to confidently handle customer objections.",
         "## Objection Handling\n\n### The LAER Framework:\n1. Listen\n2. Acknowledge\n3. Explore\n4. Respond", 4, "intermediate", "objection_handling"),
        ("Upselling & Cross-selling","Master techniques to increase basket value.",
         "## Upselling & Cross-selling\n\n### Key Concepts:\n1. Upselling\n2. Cross-selling\n3. Bundle Selling", 5, "intermediate", "upselling"),
        ("Customer Communication","Improve your communication skills for better interactions.",
         "## Customer Communication\n\n### Key Topics:\n1. First Impression\n2. Clear Communication\n3. Building Rapport", 3, "beginner", "communication"),
        ("Product Recommendation Engine","Learn to recommend the right product to the right customer.",
         "## Product Recommendation\n\n### Steps:\n1. Understand use case\n2. Identify budget\n3. Recommend 2-3 options", 3, "beginner", "need_identification"),
    ]
    courses = []
    for i, (t, d, c, dur, diff, cat) in enumerate(courses_data):
        crs = Course(title=t, description=d, content=c, duration_minutes=dur,
                     difficulty=diff, skill_category=cat, sort_order=i)
        db.add(crs); db.flush(); courses.append(crs)

    # QUIZZES
    q_data = [
        (0, "Product Knowledge Quiz", [
            ("What does RAM primarily affect in a smartphone?",
             ["Battery life","Multitasking performance","Camera quality","Screen brightness"],
             "b","RAM allows more apps to run simultaneously."),
            ("A customer asks about 64GB vs 128GB. Best response?",
             ["128GB is bigger","128GB stores more photos, videos, and apps","Both are the same","Go with 64GB"],
             "b","Explain in terms of what the customer can DO with the storage."),
        ]),
        (1, "Digital POS Quiz", [
            ("What should you do first when a customer approaches?",
             ["Start scanning","Greet them and confirm items","Ask for payment","Print receipt"],
             "b","Always greet and confirm before processing."),
        ]),
        (3, "Objection Handling Quiz", [
            ("Customer says 'I can get this cheaper online'. Best response?",
             ["You're right, online is cheaper","Here you get instant delivery and local warranty support",
              "Online products are fake","I can't do anything about the price"],
             "b","Highlight the value of in-store shopping."),
        ]),
        (4, "Upselling Quiz", [
            ("When is the BEST time to suggest an extended warranty?",
             ["Before showing the product","After the customer decides to buy, but before payment",
              "After payment is complete","Never mention it"],
             "b","After commitment, add-on suggestions feel natural."),
        ]),
    ]
    for ci, title, qs in q_data:
        quiz = Quiz(course_id=courses[ci].id, title=title, passing_score=60)
        db.add(quiz); db.flush()
        for text, opts, correct, exp in qs:
            db.add(Question(quiz_id=quiz.id, text=text,
                           option_a=opts[0], option_b=opts[1], option_c=opts[2], option_d=opts[3],
                           correct_answer=correct, explanation=exp))

    # SCENARIOS
    for name, persona, budget, diff, opening, cat in [
        ("Budget Smartphone Seeker","budget_conscious","Under Rs 15,000","medium",
         "Hi, I'm looking for a phone under Rs 15,000. I mostly care about the camera and battery life.","product_knowledge"),
        ("Confused First-Time Buyer","confused","Rs 10,000 - Rs 18,000","easy",
         "Hello! I need a new phone but I'm confused with all these options.","need_identification"),
        ("Difficult Tech-Savvy Customer","difficult","Rs 20,000 - Rs 30,000","hard",
         "I've compared several phones. Tell me why I should buy from your store.","objection_handling"),
        ("Price Comparison Shopper","price_sensitive","Rs 8,000 - Rs 15,000","medium",
         "I'm looking for the best value-for-money phone. What's popular under Rs 10,000?","upselling"),
        ("Comparison Buyer","comparison","Rs 15,000 - Rs 25,000","hard",
         "I'm comparing three phones - can you help me decide which is best?","product_knowledge"),
        ("Gift Buyer for Elderly Mother","upsell_opportunity","Under Rs 8,000","easy",
         "I need a basic phone for my mother. She only uses WhatsApp.","upselling"),
    ]:
        db.add(CustomerScenario(name=name, persona=persona, customer_goal=opening,
               budget=budget, personality="retail", difficulty=diff,
               hidden_objections="[]", opening_message=opening, skill_category=cat))

    # BADGES
    for name, desc, icon, cat in [
        ("Product Expert","Score 80%+ on product knowledge","\U0001f3c5","product_knowledge"),
        ("POS Champion","Complete POS training with 80%+","\u2328\ufe0f","pos_skills"),
        ("Customer Hero","Exceptional customer service","\U0001f9b8","communication"),
        ("Fast Learner","Complete 3 courses in a week","\u26a1","general"),
        ("Most Improved","Biggest skill improvement","\U0001f4c8","general"),
        ("Sales Accelerator","Achieve 70%+ upselling score","\U0001f4b0","upselling"),
        ("Learning Champion","Complete all courses","\U0001f393","general"),
        ("Rising Star","Reach Level 5","\u2b50","general"),
    ]:
        b = Badge(name=name, description=desc, icon=icon, skill_category=cat)
        db.add(b); db.flush()
    badges = db.query(Badge).all()
    for idx in [1, 5, 12]:
        if idx < len(employees):
            for badge in random.sample(badges, min(4, len(badges))):
                db.add(EmployeeBadge(employee_id=employees[idx].id, badge_id=badge.id))
    db.add(EmployeeBadge(employee_id=employees[0].id, badge_id=badges[3].id))

    # CHALLENGES
    for t, ct, cat, xp, tgt in [
        ("Complete one learning module today","daily","general",50,1),
        ("Complete 3 digital POS transactions","pos","pos_skills",75,3),
        ("Handle 3 AI customer scenarios","customer","communication",100,3),
        ("Improve your weakest skill by 10%","skill","general",100,1),
        ("Complete 5 courses this week","weekly","general",150,5),
    ]:
        db.add(Challenge(title=t, challenge_type=ct, skill_category=cat, xp_reward=xp, target_value=tgt))

    # NOTIFICATIONS
    if employees:
        for title, msg, ntype in [
            ("New course recommended","Try Objection Handling Mastery - 4 min","info"),
            ("Challenge expires tomorrow","Complete your daily learning challenge!","warning"),
            ("You moved to #3 on leaderboard","Keep up the great work!","success"),
            ("POS score improved by 15%","Your POS proficiency is improving!","success"),
        ]:
            db.add(Notification(employee_id=employees[0].id, title=title, message=msg, notification_type=ntype))

    # RECOGNITIONS
    if len(employees) > 5:
        db.add(Recognition(employee_id=employees[1].id, manager_id=users["manager"].id,
                           recognition_type="customer_hero", message="Great customer service!", xp_awarded=100))
        db.add(Recognition(employee_id=employees[5].id, manager_id=users["manager"].id,
                           recognition_type="product_expert", message="Excellent product knowledge!", xp_awarded=100))

    db.commit()
    print(f"Database seeded: {len(stores)} stores, {len(employees)} associates")
