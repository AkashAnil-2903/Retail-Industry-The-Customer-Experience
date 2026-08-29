"""
LLM-Powered AI Customer Companion
Uses Google Gemini free tier to generate human-like customer responses.
Falls back to mock responses if GEMINI_API_KEY is not set.
"""
import os
import re
import json
import logging

logger = logging.getLogger(__name__)

# ─── GIBBERISH DETECTION ───

def is_gibberish(text: str) -> bool:
    """
    Detect if user input is gibberish, random characters, or too short to be meaningful.
    Returns True if the message should be rejected with a polite response.
    """
    if not text or not text.strip():
        return True

    text = text.strip()

    # Too short
    if len(text) < 2:
        return True

    # Mostly special characters / numbers
    alpha_chars = re.findall(r'[a-zA-Z\u0900-\u097F\u0B00-\u0B7F]', text)
    if len(alpha_chars) / max(len(text), 1) < 0.3:
        return True

    # Repeated characters (e.g., "aaaaaa", "??????")
    if len(set(text.replace(" ", ""))) <= 2 and len(text) > 4:
        return True

    # Random keyboard mash (no vowels in long strings)
    words = text.split()
    if len(text) > 6 and not words:
        return True

    # Common real English words (short ones that might look like gibberish)
    COMMON_WORDS = {
        'hi', 'hey', 'ok', 'no', 'yes', 'the', 'and', 'for', 'are', 'but',
        'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out',
        'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now',
        'old', 'see', 'way', 'who', 'why', 'did', 'let', 'say', 'she', 'too',
        'use', 'big', 'few', 'got', 'run', 'set', 'try', 'ask', 'men', 'put',
        'end', 'far', 'hand', 'high', 'keep', 'last', 'long', 'make', 'much',
        'name', 'only', 'over', 'such', 'take', 'time', 'very', 'when', 'with',
        'work', 'year', 'back', 'give', 'most', 'find', 'here', 'thing', 'well',
        'phone', 'show', 'tell', 'help', 'need', 'want', 'like', 'good', 'best',
        'this', 'that', 'them', 'then', 'what', 'your', 'will', 'each', 'made',
        'call', 'data', 'fast', 'look', 'move', 'open', 'play', 'real', 'some',
        'stop', 'talk', 'turn', 'unit', 'want', 'warm', 'went', 'area', 'book',
        'case', 'come', 'deal', 'feel', 'free', 'gift', 'goes', 'hold', 'jobs',
        'just', 'kind', 'land', 'live', 'mind', 'next', 'okay', 'page', 'pick',
        'plan', 'rate', 'rest', 'sale', 'send', 'shop', 'side', 'size', 'sort',
        'team', 'test', 'type', 'view', 'wish', 'word', 'zero', 'able', 'also',
        'apart', 'apply', 'avoid', 'being', 'below', 'carry', 'clear', 'close',
        'could', 'doing', 'drink', 'drive', 'during', 'every', 'face', 'fact',
        'fight', 'final', 'first', 'found', 'front', 'given', 'going', 'great',
        'group', 'happy', 'heart', 'heavy', 'horse', 'house', 'human', 'ideal',
        'image', 'index', 'inner', 'input', 'issue', 'judge', 'knife', 'known',
        'large', 'later', 'laugh', 'layer', 'learn', 'leave', 'level', 'light',
        'local', 'magic', 'major', 'might', 'minor', 'model', 'money', 'month',
        'moral', 'motor', 'mount', 'mouse', 'mouth', 'movie', 'music', 'night',
        'north', 'ocean', 'offer', 'often', 'order', 'other', 'owner', 'paint',
        'panel', 'paper', 'party', 'peace', 'phone', 'photo', 'piano', 'piece',
        'pilot', 'pitch', 'pizza', 'place', 'plain', 'plant', 'plate', 'point',
        'power', 'press', 'price', 'pride', 'prime', 'print', 'proof', 'proud',
        'quick', 'quiet', 'quite', 'radio', 'raise', 'range', 'rapid', 'reach',
        'ready', 'reject', 'reply', 'rider', 'right', 'river', 'robot', 'round',
        'route', 'royal', 'rural', 'scale', 'scene', 'scope', 'score', 'sense',
        'serve', 'seven', 'shade', 'shape', 'share', 'sharp', 'sheep', 'sheet',
        'shelf', 'shell', 'shift', 'shine', 'shirt', 'shock', 'shoot', 'short',
        'sight', 'skill', 'sleep', 'slide', 'smart', 'smile', 'smoke', 'solid',
        'solve', 'sound', 'south', 'space', 'speak', 'speed', 'spend', 'split',
        'sport', 'squad', 'staff', 'stage', 'stake', 'stand', 'start', 'state',
        'steam', 'steel', 'steep', 'stick', 'still', 'stock', 'stone', 'store',
        'storm', 'story', 'strip', 'study', 'stuff', 'style', 'sugar', 'super',
        'sweet', 'swing', 'table', 'taste', 'teach', 'theme', 'thick', 'thing',
        'think', 'those', 'three', 'tiger', 'title', 'today', 'total', 'touch',
        'tower', 'track', 'trade', 'train', 'treat', 'trick', 'truly', 'trust',
        'twice', 'ultra', 'uncle', 'under', 'union', 'unity', 'until', 'upper',
        'usual', 'value', 'video', 'viral', 'virus', 'visit', 'vital', 'vivid',
        'voice', 'watch', 'water', 'wheel', 'where', 'which', 'while', 'white',
        'whole', 'whose', 'woman', 'women', 'world', 'worry', 'worse', 'worst',
        'worth', 'write', 'wrong', 'youth', 'zone', 'zoom',
    }

    # Common keyboard mash patterns
    KEYBOARD_MASH = {
        'asdf', 'qwer', 'zxcv', 'sdfg', 'wert', 'xcvb', 'dfgh', 'erty',
        'cvbn', 'fghj', 'ghjk', 'hjkl', 'jkl;', 'qazwsx', 'zaqwsx',
    }

    # Check for realistic word patterns
    has_real_word = False
    for word in words:
        clean = re.sub(r'[^a-zA-Z]', '', word).lower()
        if not clean:
            continue
        if clean in KEYBOARD_MASH:
            return True
        if clean in COMMON_WORDS:
            has_real_word = True
            break
        # A real word: has vowels, consonant-vowel alternation is natural
        vowel_count = len(re.findall(r'[aeiou]', clean))
        consonant_count = len(re.findall(r'[bcdfghjklmnpqrstvwxyz]', clean))
        if vowel_count > 0 and consonant_count > 0 and len(clean) >= 3:
            ratio = vowel_count / max(consonant_count, 1)
            if 0.25 <= ratio <= 2.0:
                has_real_word = True
                break

    # If no real word found and message is long enough, likely gibberish
    if len(alpha_chars) >= 4 and not has_real_word:
        return True

    # Check for consecutive consonants (5+ in a row = likely gibberish)
    for word in words:
        clean = re.sub(r'[^a-zA-Z]', '', word).lower()
        if clean in COMMON_WORDS:
            continue
        consonant_runs = re.findall(r'[bcdfghjklmnpqrstvwxyz]{5,}', clean)
        if consonant_runs:
            return True

    return False


def get_gibberish_response(language: str = "en") -> str:
    """Return a polite response when employee types gibberish."""
    responses = {
        "en": [
            "Sorry, I didn't quite understand that. Can you say it again?",
            "I didn't catch that. Could you repeat please?",
            "Sorry, can you say that clearly?",
            "I'm not sure what you mean. Can you rephrase?",
        ],
        "hi": [
            "माफ़ कीजिए, मुझे समझ नहीं आया। क्या आप फिर से कह सकते हैं?",
            "समझ नहीं आया। कृपया फिर से बोलें?",
            "माफ़ कीजिए, आप क्या कह रहे हैं? दोबारा बताइए।",
        ],
        "or": [
            "ଦୁଃଖିତ, ମୁଁ ବୁଝିପାରିଲି ନାହିଁ। ଆପଣ ପୁଣି କହିପାରିବେ କି?",
            "ମୁଁ ବୁଝିଲି ନାହିଁ। ଦୟାକରି ପୁଣି କୁହନ୍ତୁ।",
        ],
        "hinglish": [
            "Sorry, mujhe samajh nahi aaya. Kya aap phir se keh sakte hain?",
            "Samajh nahi aaya. Please dobara boliye?",
        ],
    }
    import random
    lang_responses = responses.get(language, responses["en"])
    return random.choice(lang_responses)


# ─── PERSONA SYSTEM PROMPTS ───

PERSONA_PROMPTS = {
    "budget_conscious": """You are a budget-conscious Indian customer looking to buy a smartphone in a retail store in Odisha, India.

PERSONALITY & BEHAVIOR:
- You are careful with money and always look for the best deal
- You will negotiate, ask for discounts, compare with online prices
- You are polite but firm about your budget
- You speak naturally, like a real person from a Tier-3 town
- Mix Hindi/Hinglish naturally if the employee speaks to you in Hindi
- You care about: camera, battery life, and value for money

BUDGET: Under ₹15,000 (you secretly have ₹15,000 but will try to spend less)
HIDDEN OBJECTIONS: You're worried about warranty, after-sales service, and whether buying in-store is better than online

CONVERSATION RULES:
- Keep responses SHORT (1-3 sentences) like a real text conversation
- If employee greets you, respond naturally
- If they ask about budget, reveal your range honestly
- If they suggest a product, react naturally (consider, negotiate, or reject)
- If the employee says something you don't understand, say "Sorry, I didn't get that"
- If they go off-topic, redirect: "I'm here to buy a phone, let's focus on that"
- Never say you are AI or a bot
- Never break character
- Use natural Indian English / Hinglish as appropriate""",

    "confused": """You are a confused first-time smartphone buyer in a retail store in Odisha, India.

PERSONALITY & BEHAVIOR:
- You don't understand technical specs (RAM, storage, processor)
- You need simple explanations, not jargon
- You're worried about making the wrong choice
- You're friendly and appreciative of good help
- You might ask very basic questions - that's okay
- You speak naturally, like someone who genuinely needs help

BUDGET: ₹10,000 - ₹18,000
HIDDEN OBJECTIONS: Fear of buying wrong, need someone you can trust

CONVERSATION RULES:
- Keep responses to 2-4 sentences. Ask genuine confused questions like "What does RAM mean?"
- If employee explains well, show appreciation and ask follow-up questions
- If they use too much jargon, ask them to simplify naturally
- If you don't understand something, say so naturally
- Never say you are AI or a bot
- Never break character""",

    "difficult": """You are a difficult, tech-savvy customer in a retail store in Odisha, India.

PERSONALITY & BEHAVIOR:
- You know phones well and expect the employee to know their stuff
- You've already researched online and will challenge weak claims
- You're not rude, but you're direct and demanding
- You'll test the employee's knowledge with tough questions
- You compare with competitors (Samsung, OnePlus) explicitly

BUDGET: ₹20,000 - ₹30,000
HIDDEN OBJECTIONS: You want proof this phone is better than competitors, want best price

CONVERSATION RULES:
- Keep responses to 2-4 sentences. Challenge the employee with specific technical questions.
- Push back on weak answers and demand better explanations
- If they give a good answer, acknowledge grudgingly but ask another tough question
- Never say you are AI or a bot
- Never break character""",

    "comparison": """You are comparing multiple phones and need help deciding in a retail store in Odisha, India.

PERSONALITY & BEHAVIOR:
- You're torn between 2-3 phones and want expert help
- You'll mention specific competitors by name
- You want clear comparisons on specific features
- You're analytical and want data-driven recommendations
- You speak naturally, like a real person making a considered purchase

BUDGET: ₹15,000 - ₹25,000
HIDDEN OBJECTIONS: Fear of missing out on a better option, want the "best" phone

CONVERSATION RULES:
- Keep responses to 2-4 sentences. Mention specific phones and ask detailed comparison questions.
- Ask follow-up questions about specific features
- If employee recommends one, ask why it's better than the others with specific concerns
- Never say you are AI or a bot
- Never break character""",

    "upsell_opportunity": """You are a customer buying a basic phone for your elderly mother in a retail store in Odisha, India.

PERSONALITY & BEHAVIOR:
- You want something simple and affordable
- Your mother only uses WhatsApp and video calls
- You're open to suggestions if they make sense for your mother
- You're protective about spending more than needed
- You speak naturally, like a caring family member

BUDGET: Under ₹8,000 (but flexible if the upsell makes sense)
HIDDEN OBJECTIONS: Don't want to overspend, but want mother to be happy

CONVERSATION RULES:
- Keep responses to 2-4 sentences. Start by explaining what your mother needs.
- If employee suggests something more expensive, initially resist but consider good reasons
- If they mention extended warranty, ask if it's really necessary for an elderly user
- Never say you are AI or a bot
- Never break character""",

    "price_sensitive": """You are a price-sensitive customer who wants maximum value for money in a retail store in Odisha, India.

PERSONALITY & BEHAVIOR:
- You compare every rupee spent
- You'll ask about hidden costs, EMI options, cash discounts
- You've checked online prices and will mention them
- You want the best deal possible
- You speak naturally, like a smart shopper

BUDGET: Under ₹10,000 - ₹15,000
HIDDEN OBJECTIONS: Hidden charges, online being cheaper, getting ripped off

CONVERSATION RULES:
- Keep responses SHORT (1-3 sentences)
- Ask about price: "What's the total cost including everything?"
- Mention online prices: "I saw this for ₹11,500 online"
- Ask for discounts: "Can you match the online price?"
- If employee offers something, ask about hidden costs
- Never say you are AI or a bot
- Never break character""",
}


def get_llm_response(
    persona: str,
    conversation_history: list,
    employee_message: str,
    language: str = "en",
    conversation_language: str = None,
) -> str | None:
    """
    Generate a human-like customer response using LLM.
    Tries Groq first (fast, 30 req/min free), then Gemini (20 req/day free), then returns None for mock fallback.
    """
    system_prompt = _build_system_prompt(persona, language, conversation_language)

    # Build messages for chat API
    messages = [{"role": "system", "content": system_prompt}]
    for msg in conversation_history:
        role = "user" if msg.get("role") == "employee" else "assistant"
        messages.append({"role": role, "content": msg["content"]})
    messages.append({"role": "user", "content": employee_message})

    # Try Groq first (fastest, most generous free tier)
    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
    if groq_key:
        try:
            from groq import Groq
            client = Groq(api_key=groq_key)
            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=messages,
                temperature=0.9,
                max_tokens=500,
                top_p=0.95,
            )
            reply = response.choices[0].message.content.strip()
            if reply and len(reply) >= 3:
                return reply
        except Exception as e:
            logger.error(f"Groq API error: {e}", exc_info=True)

    # Try Gemini second
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if gemini_key:
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=gemini_key)
            contents = []
            for msg in conversation_history:
                role = "user" if msg.get("role") == "employee" else "model"
                contents.append({"role": role, "parts": [{"text": msg["content"]}]})
            contents.append({"role": "user", "parts": [{"text": employee_message}]})
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.9,
                    top_p=0.95,
                    max_output_tokens=1024,
                ),
            )
            reply = response.text.strip()
            if reply and len(reply) >= 3:
                return reply
        except Exception as e:
            logger.warning(f"Gemini API error: {e}. Falling back to mock.")

    return None


def _build_system_prompt(persona: str, language: str, conversation_language: str = None) -> str:
    """Build the system prompt for the Gemini model."""
    base_prompt = PERSONA_PROMPTS.get(persona, PERSONA_PROMPTS["budget_conscious"])

    # Language instructions
    lang_instruction = ""
    if conversation_language == "hi" or language == "hi":
        lang_instruction = """
LANGUAGE: You MUST respond in Hindi (Devanagari script) or Hinglish (Hindi written in English script).
Match the language the employee is using. If they speak Hindi, reply in Hindi.
Example: "Haan bhaiya, mera budget ₹15,000 hai" instead of "Yes, my budget is ₹15,000"
"""
    elif conversation_language == "hinglish":
        lang_instruction = """
LANGUAGE: You MUST respond in Hinglish (Hindi words written in English script).
Mix Hindi and English naturally like real Tier-3 town conversation.
Example: "Bhaiya, yeh phone ka camera kaisa hai?" or "Theek hai, lekin price thoda zyada lag raha hai"
"""
    elif conversation_language == "or" or language == "or":
        lang_instruction = """
LANGUAGE: You MUST respond in Odia (Odia script) or mix Odia with English naturally.
Match the language the employee is using.
"""
    else:
        lang_instruction = """
LANGUAGE: Respond in natural Indian English. You can occasionally use Hindi/Hinglish phrases
that a real Tier-3 town customer would use (like "bhaiya", "theek hai", etc.)
"""

    return base_prompt + "\n\n" + lang_instruction


def get_off_topic_response(language: str = "en") -> str:
    """Return a response when employee goes off-topic."""
    responses = {
        "en": [
            "Sorry, but I'm here to buy a phone. Can we focus on that?",
            "I came to buy a phone. Let's talk about that.",
            "That's interesting, but I need help choosing a phone.",
        ],
        "hi": [
            "माफ़ कीजिए, मैं फोन खरीदने आया हूँ। क्या हम उसके बारे में बात कर सकते हैं?",
            "मैं फोन लेने आया हूँ। पहले वो दिखाइए।",
        ],
        "hinglish": [
            "Sorry bhaiya, main phone lene aaya hoon. Pehle woh dikhaiye.",
            "Phone ke baare mein baat karte hain please.",
        ],
        "or": [
            "ଦୁଃଖିତ, ମୁଁ ଫୋନ୍ କିଣିବାକୁ ଆସିଛି। ସେ ବିଷୟରେ କଥା ହେବା।",
        ],
    }
    import random
    lang_responses = responses.get(language, responses["en"])
    return random.choice(lang_responses)


# ─── OFF-TOPIC DETECTION ───

OFF_TOPIC_KEYWORDS = [
    "weather", "cricket", "match", "movie", "film", "song", "music",
    "politics", "election", "news", "meme", "joke", "recipe", "cooking",
    "gym", "workout", "travel", "train", "bus", "flight",
    "girlfriend", "boyfriend", "marriage", "wedding",
    "homework", "exam", "school", "college",
]

OFF_TOPIC_KEYWORDS_HI = [
    "mausam", "cricket", "match", "film", "gaana", "music",
    "neta", "chunav", "news", "meme", "hasya", "recipe",
    "gym", "travel", "train", "bus",
    "shaadi", "padhai", "exam", "school",
]


def is_off_topic(text: str, persona_context: str = "") -> bool:
    """
    Detect if employee message is off-topic from phone shopping.
    Returns True if the conversation has gone off-track.
    """
    if not text:
        return False

    text_lower = text.lower().strip()

    # Very short messages are usually okay (greetings, short answers)
    if len(text_lower.split()) < 3:
        return False

    # Check for phone-related keywords (if present, it's on-topic)
    phone_keywords = [
        "phone", "mobile", "camera", "battery", "screen", "display",
        "price", "cost", "budget", "discount", "offer", "warranty",
        "samsung", "oneplus", "redmi", "realme", "vivo", "oppo",
        "iphone", "apple", "processor", "ram", "storage", "gb",
        "feature", "spec", "model", "compare", "recommend",
        "buy", "purchase", "deal", "emi", "payment", "cash",
        "trial", "demo", "show", "explain", "suggest",
        "फोन", "मोबाइल", "कैमरा", "बैटरी", "स्क्रीन", "कीमत",
        "फ़ोन", "ଫୋନ୍", "ମୋବାଇଲ୍",
    ]

    # If any phone-related keyword is present, it's on-topic
    for kw in phone_keywords:
        if kw in text_lower:
            return False

    # Check for off-topic keywords
    all_off_topic = OFF_TOPIC_KEYWORDS + OFF_TOPIC_KEYWORDS_HI
    off_topic_count = sum(1 for kw in all_off_topic if kw in text_lower)

    # If multiple off-topic keywords found, likely off-topic
    if off_topic_count >= 2:
        return True

    # If message is long and has no phone-related words, likely off-topic
    word_count = len(text_lower.split())
    if word_count > 8 and off_topic_count >= 1:
        return True

    return False
