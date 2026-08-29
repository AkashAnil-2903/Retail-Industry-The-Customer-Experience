"""
AI Customer Simulator - Generates realistic customer interactions.
Works in mock mode (no API key needed) and optionally with an LLM.
Supports language detection and alignment for multilingual conversations.
"""
import json
import random
import os
import re

# ============================================================
# LANGUAGE DETECTION
# ============================================================

# Unicode ranges for Indian scripts
DEVANAGARI_RANGE = re.compile(r'[\u0900-\u097F]')
ODIA_RANGE = re.compile(r'[\u0B00-\u0B7F]')
BENGALI_RANGE = re.compile(r'[\u0980-\u09FF]')
TAMIL_RANGE = re.compile(r'[\u0B80-\u0BFF]')
TELUGU_RANGE = re.compile(r'[\u0C00-\u0C7F]')

# Common Hindi/Hinglish words that appear mixed with English
HINDI_WORDS = set([
    "hai", "hain", "ka", "ki", "ke", "ko", "mein", "me", "se", "ko",
    "ye", "yeh", "wo", "woh", "kya", "kaise", "kahan", "kyun", "kyu",
    "nahi", "nahin", "haan", "theek", "acha", "accha", "theek hai",
    "bhaiya", "didi", "bhai", "dost", "sir", "ji",
    "bolo", "batao", "sunao", "dekho", "lo", "le", "de", "do",
    "mujhe", "hamein", "aap", "tum", "tujhe", "mera", "meri", "mere",
    "iska", "iski", "iske", "uska", "uski", "uske",
    "kitna", "kitne", "kitni", "zyada", "jyada", "kam", "sasta",
    "mehnga", "accha", "bura", "sahi", "galat",
    "aur", "par", "lekin", "magar", "phir", "toh", "to",
    "mai", "hum", "sab", "kuch", "bahut", "bahut",
    "karo", "mat", "abhi", "kal", "aaj",
    "paisa", "paise", "rupee", "rupaye",
    "phone", "mobile", "akka", "amma", "anna",  # common South Indian mixed
])

# Hindi common phrases (romanized)
HINDI_PHRASES = [
    "bhaiya", "didi", "kitne ka", "kitne mein", "mujhe chahiye",
    "kya hai", "acha hai", "nahi hai", "haan ji", "nahi ji",
    "dekho", "batao", "samjhao", "samajh", "theek hai",
    "mujhe lagta", "mujhe pata", "mujhe samajh", "mujhe chahiye",
    "kya mil", "kya de", "kya kar", "kya bol",
]


def detect_language(text: str) -> str:
    """
    Detect the primary language of a text message.
    Returns: 'en', 'hi', 'or', or 'hinglish'
    """
    if not text or not text.strip():
        return "en"

    text_lower = text.lower().strip()
    total_chars = len(re.findall(r'[a-zA-Z\u0900-\u097F\u0B00-\u0B7F]', text))
    if total_chars == 0:
        return "en"

    # Check for Odia script
    odia_chars = len(ODIA_RANGE.findall(text))
    if odia_chars / max(total_chars, 1) > 0.3:
        return "or"

    # Check for Devanagari script
    devanagari_chars = len(DEVANAGARI_RANGE.findall(text))
    devanagari_ratio = devanagari_chars / max(total_chars, 1)

    if devanagari_ratio > 0.5:
        return "hi"

    # Check for Hinglish: mix of Hindi words (romanized) and English
    words = re.findall(r'[a-zA-Z\u0900-\u097F]+', text_lower)
    if not words:
        return "en"

    hindi_word_count = sum(1 for w in words if w in HINDI_WORDS)

    # Also check for common Hindi phrases
    phrase_count = sum(1 for p in HINDI_PHRASES if p in text_lower)

    # Check for Hindi phrases like "bhaiya", "nahi", "acha", etc.
    roman_hindi_ratio = (hindi_word_count + phrase_count * 2) / max(len(words), 1)

    if devanagari_ratio > 0.1 or roman_hindi_ratio > 0.35:
        # It's Hindi or Hinglish
        # Check if it's pure Hindi or mixed
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        latin_ratio = english_chars / max(total_chars, 1)

        if latin_ratio > 0.3 and devanagari_ratio < 0.5:
            return "hinglish"
        elif devanagari_ratio > 0.1:
            return "hi"
        else:
            return "hinglish"

    # Check if mostly English
    english_chars = len(re.findall(r'[a-zA-Z]', text))
    english_ratio = english_chars / max(total_chars, 1)

    if english_ratio > 0.7:
        return "en"

    return "en"


def detect_language_from_messages(messages: list) -> str:
    """
    Detect the dominant conversation language from a list of customer messages.
    Returns the most common language among customer messages.
    """
    if not messages:
        return "en"

    customer_msgs = [m for m in messages if m.get("role") == "customer"]
    if not customer_msgs:
        return "en"

    lang_counts = {"en": 0, "hi": 0, "or": 0, "hinglish": 0}
    for msg in customer_msgs:
        lang = detect_language(msg.get("content", ""))
        lang_counts[lang] = lang_counts.get(lang, 0) + 1

    # Return most common language
    return max(lang_counts, key=lang_counts.get)


# ============================================================
# MULTILINGUAL CUSTOMER RESPONSES
# ============================================================

# Hindi responses (Devanagari)
MOCK_RESPONSES_HI = {
    "budget_conscious": {
        "greetings": [
            "नमस्ते! मुझे एक फोन चाहिए लेकिन मेरा बजट कम है। क्या आप मदद कर सकते हैं?",
            "हैलो! मुझे कुछ सस्ता चाहिए। ₹15,000 से कम में क्या है?",
            "नमस्ते! मुझे अच्छा फोन चाहिए लेकिन ज्यादा खर्च नहीं कर सकता।",
        ],
        "follow_ups": [
            "लेकिन ₹12,000 मेरे लिए बहुत ज्यादा है। कोई और सस्ता है?",
            "क्या मुझे इस पर छूट मिल सकती है?",
            "अगर मैं दो खरीदूं तो?",
            "मेरे दोस्त ने ₹9,000 में फोन लिया। क्या आप मैच कर सकते हैं?",
            "मैंने ऑनलाइन इस फोन को ₹11,500 में देखा। यहाँ ₹12,000 क्यों?",
        ],
        "objections": [
            "यह मेरे बजट से ज्यादा है। कोई EMI विकल्प है?",
            "मुझे वारंटी के बारे में निश्चित नहीं है। यहाँ खरीदना बेहतर है या ऑनलाइन?",
            "अगर वारंटी खत्म होने के बाद कुछ गड़बड़ हुई तो?",
        ],
        "closing": [
            "ठीक है, मैं सोचता हूँ। कल वापस आऊंगा।",
            "क्या आप अपना बिजनेस कार्ड दे सकते हैं? मैं पत्नी से पूछकर आता हूँ।",
            "ठीक है, मैं ले लेता हूँ। लेकिन स्क्रीन प्रोटेक्टर भी दे दीजिए।",
        ],
    },
    "confused": {
        "greetings": [
            "मुझे फोन के बारे में ज्यादा पता नहीं। बस एक अच्छा फोन चाहिए।",
            "मुझे समझ नहीं आ रहा कौन सा लूं। सारे विकल्प कंफ्यूज कर रहे हैं।",
            "मेरा पुराना फोन बंद हो गया। नया चाहिए लेकिन ये स्पेक्स समझ नहीं आते।",
        ],
        "follow_ups": [
            "RAM क्या होता है? 4GB काफी है?",
            "64GB और 128GB स्टोरेज में क्या फर्क है?",
            "क्या मुझे सही में फास्ट प्रोसेसर चाहिए? मैं तो बस WhatsApp और YouTube चलाता हूँ।",
            "ये 'refresh rate' क्या है जो सब बात कर रहे हैं?",
        ],
        "objections": [
            "डर लग रहा है कि गलत चुन लिया तो पछताऊंगा।",
            "क्या आपको यकीन है यही सही फोन है मेरे लिए?",
        ],
        "closing": [
            "ठीक है, मैं आप पर भरोसा करता हूँ। आपकी सलाह से ले लेता हूँ।",
            "क्या आप इसे सेटअप कर देंगे? मुझे डेटा ट्रांसफर करना नहीं आता।",
        ],
    },
    "comparison": {
        "greetings": [
            "मैं तीन फोन की तुलना कर रहा हूँ। क्या आप मदद कर सकते हैं?",
            "मुझे Samsung A54 vs यह फोन vs OnePlus Nord में से चुनना है।",
            "₹20,000 से कम में कौन सा फोन फोटोग्राफी के लिए बेहतर है?",
        ],
        "follow_ups": [
            "लेकिन Samsung में AMOLED डिस्प्ले है। इसमें LCD है।",
            "OnePlus 80W चार्जिंग देता है। इसमें क्या है?",
            "रात में फोटो: किसकी बेहतर है?",
            "सॉफ्टवेयर अपडेट कितने साल मिलेंगे?",
        ],
        "objections": [
            "मुझे नहीं लगता यह फोन किसी भी कैटेगरी में जीतता है।",
            "रिव्यू में कहा गया है कि प्रतिस्पर्धी बेहतर है।",
            "दूसरों पर क्यों न जाऊं?",
        ],
        "closing": [
            "आपने मना लिया। चलो यह लेते हैं।",
            "जैसा आपने कहा, बेस्ट कैमरा वाला ले लेता हूँ।",
        ],
    },
    "difficult": {
        "greetings": [
            "मैं तीन दुकानों में गया हूँ और किसी ने मदद नहीं की।",
            "मुझे फोन के बारे में बहुत पता है, तो बेकार चीज़ मत दिखाइए।",
            "मुझे ₹25,000 से कम में सबसे अच्छा फोन चाहिए।",
        ],
        "follow_ups": [
            "यह प्रोसेसर पिछले साल का है। यह क्यों दिखा रहे हैं?",
            "कैमरा स्पेक्स अच्छे हैं लेकिन रियल-वर्ल्ड में कैसा है?",
            "मैंने ऑनलाइन पढ़ा कि इसमें हीटिंग की समस्या है। आपका क्या कहना है?",
            "Samsung बेहतर डिस्प्ले देता है। इसे क्यों लूं?",
        ],
        "objections": [
            "मैं संतुष्ट नहीं हूँ। बेहतर कारण दीजिए।",
            "आप ब्रोशर पढ़ रहे हैं। बताइए आपको वास्तव में क्या पता है।",
            "मैं दूसरी दुकान से भी पूछूंगा।",
        ],
        "closing": [
            "बेस्ट प्राइस दीजिए। और केस भी फ्री चाहिए।",
            "अगर ऑनलाइन प्राइस बीट कर दें तो अभी खरीद लूंगा।",
        ],
    },
    "upsell_opportunity": {
        "greetings": [
            "मुझे बस एक सिंपल फोन चाहिए। कुछ खास नहीं।",
            "मैं अपनी माँ के लिए फोन ले रहा हूँ। वो बस WhatsApp चलाती हैं।",
            "मुझे ₹8,000 से कम में कुछ दे दीजिए।",
        ],
        "follow_ups": [
            "₹8,000? यही मेरा बजट है। इसमें सबसे अच्छा क्या मिलेगा?",
            "इसका कैमरा अच्छा है? मेरे पोते-पोतियाँ दूसरे शहर में रहते हैं।",
            "क्या इससे वीडियो कॉल हो सकती है?",
        ],
        "objections": [
            "मैंने बोला सिंपल। मैं ज्यादा खर्च नहीं करना चाहता।",
            "क्या यह जरूरी है? मुझे तो बस काम चलाने वाला चाहिए।",
            "Extended warranty बहुत महंगा है।",
        ],
        "closing": [
            "ठीक है, आप सही कह रहे हैं। वो अतिरिक्त ₹2,000 वीडियो कॉल के लिए लायक हैं।",
            "चलो अच्छा वाला ले लेते हैं। मेरी माँ अच्छा फोन डिजर्व करती हैं।",
        ],
    },
    "price_sensitive": {
        "greetings": [
            "मुझे सबसे अच्छी वैल्यू फॉर मनी वाला फोन चाहिए।",
            "मैं कम से कम पैसे में ज्यादा से ज्यादा फीचर चाहता हूँ।",
            "₹10,000 से कम में सबसे ज्यादा पॉपुलर फोन कौन सा है?",
        ],
        "follow_ups": [
            "यह फोन और वह फोन एक जैसे स्पेक्स हैं। यह ₹2,000 ज्यादा क्यों है?",
            "क्या इसके साथ पावर बैंक मिल जाएगा?",
            "अगर कैश दूं तो छूट मिलेगी?",
        ],
        "objections": [
            "जो दे रहे हैं उसके लिए बहुत महंगा है।",
            "ऑनलाइन मुझे बेटर डील मिल सकती है।",
        ],
        "closing": [
            "ऑनलाइन प्राइस मैच कर दो तो अभी खरीद लूंगा।",
            "सबसे अच्छा डील दे दो फैसला कर लूंगा।",
        ],
    },
}

# Odia responses - using English fallback
# Odia text requires proper unicode encoding outside of write_file tool.
# Language detection and alignment still work correctly.
# replaced

# English responses (original)
MOCK_RESPONSES = {
    "budget_conscious": {
        "greetings": [
            "Hi, I'm looking for a phone but I have a tight budget. Can you help?",
            "Hello! I need something affordable. What do you have under \u20b915,000?",
            "Namaste! I want a good phone but I can't spend too much. What are my options?"
        ],
        "follow_ups": [
            "But \u20b912,000 is still a lot for me. Is there anything cheaper?",
            "Can I get a discount on this one?",
            "What if I buy two? Will I get a better price?",
            "My friend got a phone for \u20b99,000. Can you match that?",
            "I saw this phone online for \u20b911,500. Why is it \u20b912,000 here?",
            "Does it come with any free accessories?",
        ],
        "objections": [
            "That's more than I wanted to spend. Is there a no-cost EMI option?",
            "I'm not sure about the warranty. Is it worth buying here vs online?",
            "What if something goes wrong after the warranty ends?",
            "I heard this brand has poor after-sales service. Is that true?",
        ],
        "closing": [
            "Okay, let me think about it. I'll come back tomorrow.",
            "Can you give me a business card? I want to check with my wife first.",
            "Alright, I'll take it. But please include a screen protector.",
        ]
    },
    "confused": {
        "greetings": [
            "I don't know much about phones. I just need one that works well.",
            "Can you help me choose? I'm confused with all these options.",
            "My old phone stopped working. I need a new one but I don't understand all these specs.",
        ],
        "follow_ups": [
            "What does RAM mean? Is 4GB enough?",
            "What's the difference between 64GB and 128GB storage?",
            "Do I really need a fast processor? I just use WhatsApp and YouTube.",
            "What is this 'refresh rate' thing everyone talks about?",
            "Why is this phone more expensive than that one? They look the same.",
        ],
        "objections": [
            "I'm worried I'll pick the wrong one and regret it.",
            "Are you sure this is the right phone for me?",
            "What if my grandchildren can't use it for video calls?",
        ],
        "closing": [
            "Okay, I trust you. Let's go with your recommendation.",
            "Can you set it up for me? I don't know how to transfer data.",
        ]
    },
    "difficult": {
        "greetings": [
            "I've been to three stores already and nobody has been helpful.",
            "I know phones very well, so don't try to sell me something I don't need.",
            "I want the best phone under \u20b925,000. And I want to see the specs sheet.",
        ],
        "follow_ups": [
            "This processor is last year's model. Why are you showing me this?",
            "The camera specs look good on paper but what about real-world performance?",
            "I read online that this phone has heating issues. What do you say?",
            "Samsung offers better display. Why should I consider this?",
            "My colleague has this phone and he says it's slow after 6 months.",
        ],
        "objections": [
            "I'm not convinced. Give me a better reason.",
            "You're just reading the brochure. Tell me what you actually know.",
            "I'll check with another store and compare prices.",
            "If this phone has any issues, can I return it within 7 days?",
        ],
        "closing": [
            "Give me your best price. And I want a free case too.",
            "I'll buy it only if you can beat the online price.",
        ]
    },
    "price_sensitive": {
        "greetings": [
            "I'm looking for the best value-for-money phone.",
            "I want maximum features at minimum price.",
            "What's the most popular phone under \u20b910,000?",
        ],
        "follow_ups": [
            "This phone and that phone have the same specs. Why is this one \u20b92,000 more?",
            "Can you throw in a power bank with this?",
            "If I pay cash, can you give a discount?",
            "I saw a cashback offer online. Do you have that?",
        ],
        "objections": [
            "That's too expensive for what it offers.",
            "I can get a better deal online.",
            "What's the total cost including everything? Hidden charges?",
        ],
        "closing": [
            "Match the online price and I'll buy right now.",
            "Give me the best deal you can and I'll decide.",
        ]
    },
    "comparison": {
        "greetings": [
            "I'm comparing three phones. Can you help me decide?",
            "I need to compare Samsung A54 vs this phone vs OnePlus Nord.",
            "Which phone is better for photography under \u20b920,000?",
        ],
        "follow_ups": [
            "But Samsung has AMOLED display. This one has LCD.",
            "OnePlus offers 80W charging. What about this one?",
            "Camera comparison: which takes better night photos?",
            "What about software updates? How many years will this phone get updates?",
            "Battery life comparison: which lasts longer in real use?",
        ],
        "objections": [
            "I'm not sure this phone wins in any category.",
            "The reviews say the competition is better.",
            "Why should I pick this over the others?",
        ],
        "closing": [
            "You've convinced me. Let me go with this one.",
            "I'll take the one with the best camera as you suggested.",
        ]
    },
    "upsell_opportunity": {
        "greetings": [
            "I just need a basic phone. Nothing fancy.",
            "I want a phone for my mother. She only uses WhatsApp.",
            "Give me something simple under \u20b98,000.",
        ],
        "follow_ups": [
            "\u20b98,000? That's my budget. What's the best I can get?",
            "Does this phone have a good camera? My grandchildren live in another city.",
            "Can she do video calls on this?",
        ],
        "objections": [
            "I said basic. I don't want to spend more.",
            "Is this really necessary? I just want something that works.",
            "The extended warranty is too expensive.",
        ],
        "closing": [
            "Okay, you're right. The extra \u20b92,000 is worth it for video calls.",
            "Fine, I'll take the better one. My mother deserves a good phone.",
        ]
    }
}

# Hinglish responses (Hindi written in Latin script - natural Tier-3 conversation style)
MOCK_RESPONSES_HINGLISH = {
    "budget_conscious": {
        "greetings": [
            "Bhaiya, mujhe ek phone chahiye but mera budget kam hai. Kya help kar sakte hain?",
            "Hello! Mujhe kuch affordable chahiye. \u20b915,000 se kam mein kya hai?",
            "Namaste bhaiya! Mujhe achha phone chahiye but zyada kharch nahi kar sakta.",
        ],
        "follow_ups": [
            "But \u20b912,000 toh bahut zyada hai mere liye. Aur kuch sasta hai?",
            "Ismein koi discount mil sakta hai kya?",
            "Agar main do kharidun toh?",
            "Mere dost ne \u20b99,000 mein phone liya. Aap match kar sakte hain?",
            "Maine online dekha \u20b911,500 mein. Yahan \u20b912,000 kyun?",
        ],
        "objections": [
            "Yeh mere budget se zyada hai. Koi EMI option hai?",
            "Warranty ke baare mein sure nahi hoon. Yahan kharidna better hai ya online?",
            "Agar warranty khatam hone ke baad kuch gadbad hui toh?",
        ],
        "closing": [
            "Theek hai, sochta hoon. Kal wapas aunga.",
            "Kya aap apna business card de sakte hain? Pooch ke aata hoon.",
            "Theek hai, le leta hoon. Lekin screen protector bhi de dijiye.",
        ],
    },
    "confused": {
        "greetings": [
            "Mujhe phone ke baare mein zyada pata nahi. Bas ek achha kaam karne wala phone chahiye.",
            "Help kar sakte ho choose karne mein? Saare options confuse kar rahe hain.",
            "Mera purana phone band ho gaya. Naya chahiye but yeh sab specs samajh nahi aate.",
        ],
        "follow_ups": [
            "RAM kya hota hai? 4GB kaafi hai kya?",
            "64GB aur 128GB mein kya fark hai?",
            "Mujhe sach mein fast processor chahiye? Main toh bas WhatsApp aur YouTube use karta hoon.",
            "Yeh 'refresh rate' kya hai jo sab baat kar rahe hain?",
        ],
        "objections": [
            "Darr lag raha hai galat le liya toh pachtunga.",
            "Kya aapko yakeen hai yehi sahi phone hai mere liye?",
        ],
        "closing": [
            "Theek hai, aap par bharosa karta hoon. Aapki salah se le leta hoon.",
            "Kya aap setup kar denge? Mujhe data transfer karna nahi aata.",
        ],
    },
    "comparison": {
        "greetings": [
            "Main teen phone ki tulna kar raha hoon. Help kar sakte ho?",
            "Mujhe Samsung A54 vs yeh phone vs OnePlus Nord mein se chunna hai.",
            "\u20b920,000 se kaun sa phone photography ke liye better hai?",
        ],
        "follow_ups": [
            "But Samsung mein AMOLED display hai. Ismein LCD hai.",
            "OnePlus 80W charging deta hai. Ismein kya hai?",
            "Raat mein photo: kiski better hai?",
        ],
        "objections": [
            "Mujhe nahi lagta yeh phone kisi bhi category mein jeetta hai.",
            "Review mein kaha hai ki competition better hai.",
        ],
        "closing": [
            "Aapne mana liya. Chalo yeh lete hain.",
            "Jaisa aapne kaha, best camera wala le leta hoon.",
        ],
    },
    "difficult": {
        "greetings": [
            "Main teen dukaanon mein gaya hoon aur kisi ne help nahi ki.",
            "Mujhe phone ke baare mein bahut pata hai, toh bekar cheez mat dikhaiye.",
            "Mujhe \u20b925,000 se kam mein sabse achha phone chahiye.",
        ],
        "follow_ups": [
            "Yeh processor pichle saal ka hai. Yeh kyun dikha rahe hain?",
            "Camera specs achhe hain but real-world mein kaisa hai?",
            "Maine online padha ki ismein heating ki samasya hai. Aapka kya kehna hai?",
            "Samsung better display deta hai. Isse kyun loon?",
        ],
        "objections": [
            "Main santusht nahi hoon. Better karan dijiye.",
            "Aap brochure padh rahe hain. Bataiye aapko vastav mein kya pata hai.",
        ],
        "closing": [
            "Best price dijiye. Aur case bhi free chahiye.",
            "Agar online price beat kar dein toh abhi kharid loonga.",
        ],
    },
    "upsell_opportunity": {
        "greetings": [
            "Mujhe bas ek simple phone chahiye. Kuch khaas nahi.",
            "Main apni maa ke liye phone le raha hoon. Woh bas WhatsApp chalati hain.",
            "Mujhe \u20b98,000 se kam mein kuch de dijiye.",
        ],
        "follow_ups": [
            "\u20b98,000? Yahi mera budget hai. Ismein sabse achha kya milega?",
            "Iska camera achha hai? Mere potey-potiyaan doosre sheher mein rehte hain.",
            "Kya isse video call ho sakti hai?",
        ],
        "objections": [
            "Maine bola simple. Main zyada kharch nahi karna chahta.",
            "Kya yeh zaroori hai? Mujhe toh bas kaam chalane wala chahiye.",
        ],
        "closing": [
            "Theek hai, aap sahi keh rahe hain. Woh extra \u20b92,000 video calls ke liye laayak hain.",
            "Chalo achha wala le lete hain. Meri maa achha phone deserve karti hain.",
        ],
    },
    "price_sensitive": {
        "greetings": [
            "Mujhe sabse achhi value for money wala phone chahiye.",
            "Main kam paise mein zyada features chahta hoon.",
            "\u20b910,000 se kaun sa phone sabse zyada popular hai?",
        ],
        "follow_ups": [
            "Yeh phone aur woh phone same specs hain. Yeh \u20b92,000 zyada kyun hai?",
            "Iske saath power bank mil jayega kya?",
            "Agar cash doon toh discount milega?",
        ],
        "objections": [
            "Jo de rahe hain uske liye bahut mehnga hai.",
            "Online mujhe better deal mil sakti hai.",
        ],
        "closing": [
            "Online price match kar do toh abhi kharid loonga.",
            "Sabse achha deal de do faisla kar loonga.",
        ],
    },
}


# Evaluation criteria weights
EVAL_WEIGHTS = {
    "product_knowledge": 0.25,
    "need_identification": 0.20,
    "communication": 0.20,
    "objection_handling": 0.15,
    "upselling": 0.10,
    "accuracy": 0.10,
}


# Hindi and Odia responses - loaded from JSON files
import json as _json_mod

_HI_CACHE = None
def _get_hi():
    global _HI_CACHE
    if _HI_CACHE is not None:
        return _HI_CACHE
    _path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static", "hi_responses.json")
    try:
        with open(_path, "r", encoding="utf-8") as f:
            _HI_CACHE = _json_mod.load(f)
    except (FileNotFoundError, _json_mod.JSONDecodeError):
        _HI_CACHE = {}
    return _HI_CACHE

_OR_CACHE = None
def _get_or():
    global _OR_CACHE
    if _OR_CACHE is not None:
        return _OR_CACHE
    _path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static", "or_responses.json")
    try:
        with open(_path, "r", encoding="utf-8") as f:
            _OR_CACHE = _json_mod.load(f)
    except (FileNotFoundError, _json_mod.JSONDecodeError):
        _OR_CACHE = {}
    return _OR_CACHE

def get_mock_customer_opening(persona: str, language: str = "en") -> str:
    """Get a random opening message for the given persona in the specified language."""
    if language == "hi" and persona in _get_hi():
        return random.choice(_get_hi()[persona]["greetings"])
    elif language == "or" and persona in _get_or():
        return random.choice(_get_or()[persona]["greetings"])
    elif language == "hinglish" and persona in MOCK_RESPONSES_HINGLISH:
        return random.choice(MOCK_RESPONSES_HINGLISH[persona]["greetings"])
    # Fall back to English
    responses = MOCK_RESPONSES.get(persona, MOCK_RESPONSES["budget_conscious"])
    return random.choice(responses["greetings"])


def get_mock_customer_response(persona: str, conversation_turn: int, employee_message: str, language: str = "en", conversation_language: str = None) -> str:
    """
    Generate a mock customer response based on conversation turn, language, and conversation context.

    conversation_language: if set, forces the customer to respond in this language
                          (maintains language consistency once established).
    """
    # Determine the response language
    if conversation_language:
        # Once a conversation language is established, keep using it
        effective_lang = conversation_language
    else:
        # Detect from employee message if available, otherwise use preferred language
        if employee_message:
            detected = detect_language(employee_message)
            effective_lang = detected if detected != "en" else language
        else:
            effective_lang = language

    # Select language-specific responses
    if effective_lang == "hi" and persona in _get_hi():
        responses = _get_hi()[persona]
    elif effective_lang == "or" and persona in _get_or():
        responses = _get_or()[persona]
    elif effective_lang == "hinglish" and persona in MOCK_RESPONSES_HINGLISH:
        responses = MOCK_RESPONSES_HINGLISH[persona]
    else:
        responses = MOCK_RESPONSES.get(persona, MOCK_RESPONSES["budget_conscious"])

    if conversation_turn <= 1:
        return random.choice(responses["follow_ups"])
    elif conversation_turn <= 3:
        pool = responses["follow_ups"] + responses["objections"]
        return random.choice(pool)
    elif conversation_turn <= 5:
        pool = responses["objections"] + responses["closing"]
        return random.choice(pool)
    else:
        return random.choice(responses["closing"])


def evaluate_simulation(messages: list, scenario_info: dict) -> dict:
    """
    Evaluate an AI customer simulation session.
    Returns structured evaluation data including language alignment.

    In production, this would call an LLM for nuanced evaluation.
    For hackathon, uses heuristics on message content.
    """
    employee_messages = [m for m in messages if m.get("role") == "employee"]
    customer_messages = [m for m in messages if m.get("role") == "customer"]

    if not employee_messages:
        return _default_evaluation()

    # Basic heuristic scoring
    total_messages = len(employee_messages)

    # Detect conversation language from customer messages
    conv_lang = detect_language_from_messages(customer_messages)

    # --- Language Alignment ---
    lang_align_score = _compute_language_alignment(employee_messages, conv_lang)

    # Product knowledge indicators
    pk_keywords = ["spec", "feature", "processor", "camera", "battery", "display", "storage", "ram", "gb", "mp", "inch", "screen", "warranty", "brand", "model"]
    pk_count = sum(1 for m in employee_messages if any(k in m["content"].lower() for k in pk_keywords))
    product_knowledge = min(95, max(40, 50 + (pk_count * 8)))

    # Need identification
    # Use broader keywords that include Hindi/Hinglish equivalents
    ni_keywords_en = ["need", "budget", "use", "purpose", "looking for", "preference", "requirement", "want", "who", "how often", "what for"]
    ni_keywords_hi = ["chahiye", "chahta", "chahti", "budget", "zaroorat", "kaam", "kya", "kaun sa"]
    ni_keywords = ni_keywords_en + ni_keywords_hi
    ni_count = sum(1 for m in employee_messages if any(k in m["content"].lower() for k in ni_keywords))
    need_identification = min(95, max(35, 45 + (ni_count * 12)))

    # Communication quality - includes language alignment boost
    avg_length = sum(len(m["content"]) for m in employee_messages) / total_messages if total_messages else 0
    greeting_words_en = ["hello", "hi", "welcome", "sure", "great", "thank", "please", "absolutely", "of course", "namaste"]
    greeting_words_hi = ["namaste", "bhaiya", "ji", "acha", "theek hai", "dhanyavaad", "shukriya"]
    all_greetings = greeting_words_en + greeting_words_hi
    greeting_count = sum(1 for m in employee_messages if any(g in m["content"].lower() for g in all_greetings))
    communication = min(95, max(40, 50 + (avg_length * 0.15) + (greeting_count * 6)))

    # Boost communication if language alignment is good
    if lang_align_score >= 80:
        communication = min(95, communication + 8)
    elif lang_align_score >= 60:
        communication = min(95, communication + 3)
    elif lang_align_score < 40:
        communication = max(30, communication - 10)

    # Objection handling
    oh_keywords_en = ["understand", "however", "but", "although", "compared", "advantage", "benefit", "warranty", "guarantee", "return", "exchange", "support", "service"]
    oh_keywords_hi = ["samajh", "samajhta", "lekin", "magar", "parantu", "vardaan", "swap", "wapsi", "seva"]
    oh_keywords = oh_keywords_en + oh_keywords_hi
    oh_count = sum(1 for m in employee_messages if any(k in m["content"].lower() for k in oh_keywords))
    objection_handling = min(95, max(30, 40 + (oh_count * 10)))

    # Upselling
    us_keywords_en = ["also", "additionally", "recommend", "upgrade", "better", "premium", "accessory", "case", "screen protector", "warranty", "extended", "bundle", "combo"]
    us_keywords_hi = ["sath mein", "aur bhi", "badhiya", "better", "accessory", "cover", "protection"]
    us_keywords = us_keywords_en + us_keywords_hi
    us_count = sum(1 for m in employee_messages if any(k in m["content"].lower() for k in us_keywords))
    upselling = min(95, max(25, 35 + (us_count * 12)))

    # Accuracy - based on engagement quality
    accuracy = min(95, max(45, 60 + (total_messages * 3)))

    # Ensure scores from pre/post assessment data if available
    pre_skills = scenario_info.get("pre_skills", {})
    if pre_skills:
        product_knowledge = int(0.5 * product_knowledge + 0.5 * pre_skills.get("product_knowledge", product_knowledge))
        need_identification = int(0.5 * need_identification + 0.5 * pre_skills.get("need_identification", need_identification))
        communication = int(0.5 * communication + 0.5 * pre_skills.get("communication", communication))
        objection_handling = int(0.5 * objection_handling + 0.5 * pre_skills.get("objection_handling", objection_handling))
        upselling = int(0.5 * upselling + 0.5 * pre_skills.get("upselling", upselling))

    overall = int(
        product_knowledge * EVAL_WEIGHTS["product_knowledge"] +
        need_identification * EVAL_WEIGHTS["need_identification"] +
        communication * EVAL_WEIGHTS["communication"] +
        objection_handling * EVAL_WEIGHTS["objection_handling"] +
        upselling * EVAL_WEIGHTS["upselling"] +
        accuracy * EVAL_WEIGHTS["accuracy"]
    )

    strengths = []
    weaknesses = []
    missed = []

    # Language alignment feedback
    if lang_align_score >= 80:
        strengths.append("Excellent language alignment - matched customer's communication style naturally")
    elif lang_align_score >= 60:
        strengths.append("Good language alignment - mostly communicated in customer's language")
    elif lang_align_score < 40:
        weaknesses.append("Language mismatch - customer communicated in " + _lang_name(conv_lang) + " but responses were primarily in a different language")
        missed.append("Try responding in " + _lang_name(conv_lang) + " to create a more comfortable interaction")

    if product_knowledge >= 75:
        strengths.append("Strong product knowledge and technical explanation")
    elif product_knowledge < 55:
        weaknesses.append("Needs improvement in product knowledge")

    if communication >= 75 and lang_align_score >= 60:
        strengths.append("Clear and professional communication style")
    elif communication < 55:
        weaknesses.append("Communication could be more structured")

    if objection_handling >= 70:
        strengths.append("Good at handling customer objections")
    elif objection_handling < 55:
        weaknesses.append("Weak objection handling - customer concerns not fully addressed")

    if upselling >= 65:
        strengths.append("Effective upselling and cross-selling approach")
    elif upselling < 50:
        weaknesses.append("Missed upselling and cross-selling opportunities")
        missed.append("Did not suggest complementary products or accessories")

    if need_identification >= 70:
        strengths.append("Good at identifying customer needs")
    elif need_identification < 55:
        weaknesses.append("Did not ask enough questions to understand customer needs")
        missed.append("Could have asked more about the customer's specific requirements")

    if not strengths:
        strengths.append("Completed the customer interaction")
    if not weaknesses:
        weaknesses.append("Overall performance is satisfactory")

    # Recommendation
    weakest = min(
        {"product_knowledge": product_knowledge, "need_identification": need_identification,
         "communication": communication, "objection_handling": objection_handling,
         "upselling": upselling}.items(),
        key=lambda x: x[1]
    )

    rec_map = {
        "product_knowledge": "Product Knowledge Basics",
        "need_identification": "Customer Need Identification",
        "communication": "Customer Communication",
        "objection_handling": "Objection Handling Mastery",
        "upselling": "Upselling & Cross-selling",
    }

    return {
        "overall_score": overall,
        "product_knowledge": product_knowledge,
        "need_identification": need_identification,
        "communication": communication,
        "objection_handling": objection_handling,
        "upselling": upselling,
        "accuracy": accuracy,
        "language_alignment": lang_align_score,
        "conversation_language": conv_lang,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "missed_opportunities": missed,
        "recommendation": rec_map.get(weakest[0], "General Skills Improvement"),
    }


def _compute_language_alignment(employee_messages: list, customer_language: str) -> int:
    """
    Compute how well the employee matched the customer's language.
    Returns a score 0-100.
    """
    if customer_language == "en":
        # English customer - check if employee responds in English
        english_count = sum(1 for m in employee_messages if detect_language(m["content"]) == "en")
        return min(100, int((english_count / max(len(employee_messages), 1)) * 100))

    elif customer_language == "hi":
        # Hindi customer - check if employee responds in Hindi or Hinglish
        matching = sum(1 for m in employee_messages if detect_language(m["content"]) in ("hi", "hinglish"))
        return min(100, int((matching / max(len(employee_messages), 1)) * 100))

    elif customer_language == "hinglish":
        # Hinglish customer - check if employee responds in Hinglish, Hindi, or English
        # All three are acceptable for Hinglish conversations
        matching = sum(1 for m in employee_messages if detect_language(m["content"]) in ("hinglish", "hi", "en"))
        return min(100, int((matching / max(len(employee_messages), 1)) * 100))

    elif customer_language == "or":
        # Odia customer
        matching = sum(1 for m in employee_messages if detect_language(m["content"]) in ("or", "hinglish"))
        return min(100, int((matching / max(len(employee_messages), 1)) * 100))

    return 75  # Default for unknown languages


def _lang_name(lang_code: str) -> str:
    """Convert language code to human-readable name."""
    names = {
        "en": "English",
        "hi": "Hindi",
        "or": "Odia",
        "hinglish": "Hindi/Hinglish",
    }
    return names.get(lang_code, "the customer's language")


def _default_evaluation():
    return {
        "overall_score": 40,
        "product_knowledge": 40,
        "need_identification": 35,
        "communication": 45,
        "objection_handling": 30,
        "upselling": 25,
        "accuracy": 45,
        "language_alignment": 50,
        "conversation_language": "en",
        "strengths": ["Completed the interaction"],
        "weaknesses": ["Insufficient engagement with customer"],
        "missed_opportunities": ["Did not respond to customer queries"],
        "recommendation": "Customer Communication",
    }


def get_skill_gap_recommendations(skills: dict) -> list:
    """Rule-based skill gap detection and recommendations."""
    recommendations = []

    skill_thresholds = {
        "pos_skills": ("Digital POS Mastery", 60),
        "upselling": ("Upselling & Cross-selling", 60),
        "product_knowledge": ("Product Knowledge Basics", 60),
        "communication": ("Customer Communication", 60),
        "objection_handling": ("Objection Handling Mastery", 60),
        "need_identification": ("Customer Need Identification", 60),
    }

    for skill, (course, threshold) in skill_thresholds.items():
        score = skills.get(skill, 50)
        if score < threshold:
            gap = threshold - score
            priority = "high" if gap > 20 else "medium" if gap > 10 else "low"
            recommendations.append({
                "skill": skill,
                "current_score": score,
                "target_score": threshold,
                "gap": gap,
                "priority": priority,
                "course": course,
            })

    recommendations.sort(key=lambda x: x["gap"], reverse=True)
    return recommendations


def get_next_best_action(skills: dict, training_progress: dict) -> dict:
    """Determine the employee's next best action."""
    recs = get_skill_gap_recommendations(skills)

    if recs:
        top = recs[0]
        return {
            "action": "complete_course",
            "title": top["course"],
            "description": f"Your {top['skill'].replace('_', ' ').title()} is {top['current_score']}%, below the target of {top['target_score']}%.",
            "priority": top["priority"],
        }

    pos = skills.get("pos_skills", 50)
    if pos < 70:
        return {
            "action": "pos_challenge",
            "title": "Complete 3 Digital POS Transactions",
            "description": f"Your POS proficiency is {pos}%. Practice with real transactions.",
            "priority": "medium",
        }

    return {
        "action": "challenge",
        "title": "Try a Customer Challenge",
        "description": "Test your skills with an AI customer scenario.",
        "priority": "low",
    }
