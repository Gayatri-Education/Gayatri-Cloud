"""Authoritative i18n Translation Registry & Subsystem.
Supports the 8 source platform languages: English, Hindi, Sanskrit, Tamil, Telugu, Kannada, Marathi, Bengali.
Implements English fallback, parameter interpolation, user preference management,
and decoupled AI prompt language instructions (RQ-029, DEC-C32).
"""

from __future__ import annotations

import logging
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class LanguageCode(StrEnum):
    """Supported 8 UI and pedagogical languages."""

    EN = "en"  # English (Default)
    HI = "hi"  # Hindi (हिन्दी)
    SA = "sa"  # Sanskrit (संस्कृतम्)
    TA = "ta"  # Tamil (தமிழ்)
    TE = "te"  # Telugu (తెలుగు)
    KN = "kn"  # Kannada (ಕನ್ನಡ)
    MR = "mr"  # Marathi (मराठी)
    BN = "bn"  # Bengali (বাংলা)


LANGUAGE_METADATA: dict[str, dict[str, str]] = {
    "en": {"code": "en", "native_label": "English", "english_name": "English", "script": "Latin"},
    "hi": {"code": "hi", "native_label": "हिन्दी", "english_name": "Hindi", "script": "Devanagari"},
    "sa": {
        "code": "sa",
        "native_label": "संस्कृतम्",
        "english_name": "Sanskrit",
        "script": "Devanagari",
    },
    "ta": {"code": "ta", "native_label": "தமிழ்", "english_name": "Tamil", "script": "Tamil"},
    "te": {"code": "te", "native_label": "తెలుగు", "english_name": "Telugu", "script": "Telugu"},
    "kn": {"code": "kn", "native_label": "ಕನ್ನಡ", "english_name": "Kannada", "script": "Kannada"},
    "mr": {
        "code": "mr",
        "native_label": "मराठी",
        "english_name": "Marathi",
        "script": "Devanagari",
    },
    "bn": {"code": "bn", "native_label": "বাংলা", "english_name": "Bengali", "script": "Bengali"},
}

TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        "app_title": "Gayatri Cloud",
        "welcome": "Welcome back, {name}",
        "dashboard": "Dashboard",
        "courses": "Courses",
        "tutor": "AI Tutor",
        "assessments": "Assessments",
        "mastery": "Mastery",
        "billing": "Billing",
        "settings": "Settings",
        "offline_library": "Offline Library",
        "offline_cached_notice": "Offline reading mode: Viewing locally cached lesson material.",
        "offline_live_disabled": "Cloud tutoring, exams, and payments are disabled while offline.",
        "stale_version_warning": "A newer course version is published online. Please reconnect to update.",
        "search_placeholder": "Search topics, concepts, or courses...",
        "ask_tutor_placeholder": "Ask Gayatri AI tutor a question...",
        "language_selector": "Select Language",
        "high_contrast_toggle": "Toggle High Contrast",
        "font_scale": "Text Size",
    },
    "hi": {
        "app_title": "गायत्री क्लाउड",
        "welcome": "पुनः स्वागत है, {name}",
        "dashboard": "डैशबोर्ड",
        "courses": "पाठ्यक्रम",
        "tutor": "एआई ट्यूटर",
        "assessments": "मूल्यांकन",
        "mastery": "महारत",
        "billing": "बिलिंग और शुल्क",
        "settings": "सेटिंग्स",
        "offline_library": "ऑफ़लाइन पुस्तकालय",
        "offline_cached_notice": "ऑफ़लाइन पठन मोड: स्थानीय रूप से सहेजी गई सामग्री देख रहे हैं।",
        "offline_live_disabled": "ऑफ़लाइन होने पर क्लाउड ट्यूटर, परीक्षा और भुगतान अक्षम हैं।",
        "stale_version_warning": "नया पाठ्यक्रम संस्करण ऑनलाइन उपलब्ध है। कृपया अद्यतन करने के लिए पुनः कनेक्ट करें।",
        "search_placeholder": "विषय, अवधारणाएं या पाठ्यक्रम खोजें...",
        "ask_tutor_placeholder": "गायत्री एआई ट्यूटर से प्रश्न पूछें...",
        "language_selector": "भाषा चुनें",
        "high_contrast_toggle": "उच्च कंट्रास्ट बदलें",
        "font_scale": "अक्षर आकार",
    },
    "sa": {
        "app_title": "गायत्री क्लाउड्",
        "welcome": "पुनरागमनं शुभम्, {name}",
        "dashboard": "नियन्त्रणपट्टिका",
        "courses": "पाठ्यक्रमाः",
        "tutor": "एआई गुरुः",
        "assessments": "मूल्याङ्कनम्",
        "mastery": "प्रावीण्यम्",
        "billing": "शुल्कव्यवस्था",
        "settings": "व्यवस्थापनानि",
        "offline_library": "सङ्ग्रहालयः (ऑफलाइन)",
        "offline_cached_notice": "ऑफलाइन पठनक्रमः: सुरक्षितपाठनसामग्री दृश्यते।",
        "offline_live_disabled": "जालसम्पर्कं विना परीक्षा शुल्कदानं च न सिध्यति।",
        "stale_version_warning": "नूतनसंस्करणम् उपलब्धम् अस्ति। अद्यतनीकर्तुं पुनः सञ्चारं कुरुत।",
        "search_placeholder": "विषयान् अन्वेषयन्तु...",
        "ask_tutor_placeholder": "गुरुं प्रश्नं पृच्छन्तु...",
        "language_selector": "भाषां चिनुत",
        "high_contrast_toggle": "वर्णवैषम्यम्",
        "font_scale": "अक्षराकारः",
    },
    "ta": {
        "app_title": "காயத்ரி கிளவுட்",
        "welcome": "மீண்டும் வருக, {name}",
        "dashboard": "முகப்புப்பலகை",
        "courses": "பாடநெறிகள்",
        "tutor": "AI ஆசிரியர்",
        "assessments": "மதிப்பீடுகள்",
        "mastery": "தேர்ச்சி",
        "billing": "கட்டணங்கள்",
        "settings": "அமைப்புகள்",
        "offline_library": "ஆஃப்லைன் நூலகம்",
        "offline_cached_notice": "ஆஃப்லைன் வாசிப்பு முறை: பதிவிறக்கம் செய்த பாடம்.",
        "offline_live_disabled": "ஆஃப்லைனில் உள்ள போது தேர்வுகள் மற்றும் பணம் செலுத்துதல் முடக்கப்பட்டுள்ளன.",
        "stale_version_warning": "புதிய பதிப்பு கிடைக்கிறது. புதுப்பிக்க இணையத்துடன் இணையவும்.",
        "search_placeholder": "தலைப்புகளைத் தேடுங்கள்...",
        "ask_tutor_placeholder": "AI ஆசிரியரிடம் கேள்வி கேளுங்கள்...",
        "language_selector": "மொழியைத் தேர்ந்தெடுக்கவும்",
        "high_contrast_toggle": "மாறுபட்ட நிற முறை",
        "font_scale": "எழுத்து அளவு",
    },
    "te": {
        "app_title": "గాయత్రి క్లౌడ్",
        "welcome": "స్వాగతం, {name}",
        "dashboard": "డాష్‌బోర్డ్",
        "courses": "కోర్సులు",
        "tutor": "AI ట్యూటర్",
        "assessments": "మూల్యాంకనాలు",
        "mastery": "నైపుణ్యం",
        "billing": "ఫీజులు మరియు చెల్లింపులు",
        "settings": "సెట్టింగ్‌లు",
        "offline_library": "ఆఫ్‌లైన్ లైబ్రరీ",
        "offline_cached_notice": "ఆఫ్‌లైన్ మోడ్: స్థానికంగా సేవ్ చేసిన పాఠ్య సామగ్రిని వీక్షిస్తున్నారు.",
        "offline_live_disabled": "ఆఫ్‌లైన్‌లో ఉన్నప్పుడు పరీక్షలు మరియు చెల్లింపులు సాధ్యం కాదు.",
        "stale_version_warning": "కొత్త కోర్సు వెర్షన్ అందుబాటులో ఉంది. నవీకరించడానికి రీకనెక్ట్ అవ్వండి.",
        "search_placeholder": "విషయాలు లేదా కోర్సులను శోధించండి...",
        "ask_tutor_placeholder": "AI ట్యూటర్‌ని ప్రశ్న అడగండి...",
        "language_selector": "భాషను ఎంచుకోండి",
        "high_contrast_toggle": "హై కాంట్రాస్ట్",
        "font_scale": "టెక్స్ట్ సైజు",
    },
    "kn": {
        "app_title": "ಗಾಯತ್ರಿ ಕ್ಲೌಡ್",
        "welcome": "ಮತ್ತೆ ಸುಸ್ವಾಗತ, {name}",
        "dashboard": "ಡ್ಯಾಶ್‌ಬೋರ್ಡ್",
        "courses": "ಕೋರ್ಸ್‌ಗಳು",
        "tutor": "AI ಬೋಧಕ",
        "assessments": "ಮೌಲ್ಯಮಾಪನಗಳು",
        "mastery": "ಪ್ರಾವೀಣ್ಯತೆ",
        "billing": "ಶುಲ್ಕಗಳು",
        "settings": "ಸೆಟ್ಟಿಂಗ್‌ಗಳು",
        "offline_library": "ಆಫ್‌ಲೈನ್ ಲೈಬ್ರರಿ",
        "offline_cached_notice": "ಆಫ್‌ಲೈನ್ ಮೋಡ್: ಡೌನ್‌ಲೋಡ್ ಮಾಡಿದ ಪಾಠ ಸಾಮಗ್ರಿ ವೀಕ್ಷಿಸಲಾಗುತ್ತಿದೆ.",
        "offline_live_disabled": "ಆಫ್‌ಲೈನ್‌ನಲ್ಲಿರುವಾಗ ಪರೀಕ್ಷೆಗಳು ಮತ್ತು ಪಾವತಿಗಳು ಲಭ್ಯವಿಲ್ಲ.",
        "stale_version_warning": "ಹೊಸ ಆವೃತ್ತಿ ಲಭ್ಯವಿದೆ. ಅಪ್‌ಡೇಟ್ ಮಾಡಲು ಮರುಸಂಪರ್ಕಿಸಿ.",
        "search_placeholder": "ವಿಷಯಗಳನ್ನು ಹುಡುಕಿ...",
        "ask_tutor_placeholder": "AI ಶಿಕ್ಷಕರನ್ನು ಪ್ರಶ್ನಿಸಿ...",
        "language_selector": "ಭಾಷೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ",
        "high_contrast_toggle": "ಹೆಚ್ಚಿನ ಕಾಂಟ್ರಾಸ್ಟ್",
        "font_scale": "ಅಕ್ಷರದ ಗಾತ್ರ",
    },
    "mr": {
        "app_title": "गायत्री क्लाउड",
        "welcome": "पुन्हा स्वागत आहे, {name}",
        "dashboard": "डॅशबोर्ड",
        "courses": "अभ्यासक्रम",
        "tutor": "एआय शिक्षक",
        "assessments": "मूल्यमापन",
        "mastery": "प्रवीणता",
        "billing": "फी आणि देयके",
        "settings": "सेटिंग्ज",
        "offline_library": "ऑफलाइन ग्रंथालय",
        "offline_cached_notice": "ऑफलाइन वाचन मोड: जतन केलेले धडे पाहत आहात.",
        "offline_live_disabled": "ऑफलाइन असताना थेट परीक्षा आणि देयके बंद आहेत.",
        "stale_version_warning": "नवीन आवृत्ती उपलब्ध आहे. कृपया अपडेट करण्यासाठी पुन्हा कनेक्ट करा.",
        "search_placeholder": "विषय किंवा अभ्यासक्रम शोधा...",
        "ask_tutor_placeholder": "गायत्री शिक्षकांना प्रश्न विचारा...",
        "language_selector": "भाषा निवडा",
        "high_contrast_toggle": "उच्च तीव्रता",
        "font_scale": "फॉन्ट आकार",
    },
    "bn": {
        "app_title": "গায়ত্রী ক্লাউড",
        "welcome": "স্বাগতম, {name}",
        "dashboard": "ড্যাশবোর্ড",
        "courses": "কোর্সসমূহ",
        "tutor": "এআই টিউটর",
        "assessments": "মূল্যায়ন",
        "mastery": "দক্ষতা",
        "billing": "ফি ও পেমেন্ট",
        "settings": "সেটিংস",
        "offline_library": "অফলাইন লাইব্রেরি",
        "offline_cached_notice": "অফলাইন পঠন মোড: সংরক্ষিত পাঠ্যক্রম দেখা হচ্ছে।",
        "offline_live_disabled": "অফলাইনে থাকাকালীন পরীক্ষা ও পেমেন্ট নিষ্ক্রিয় থাকে।",
        "stale_version_warning": "নতুন সংস্করণ উপলব্ধ। আপডেট করতে পুনরায় সংযুক্ত হোন।",
        "search_placeholder": "বিষয় বা কোর্স অনুসন্ধান করুন...",
        "ask_tutor_placeholder": "এআই শিক্ষককে প্রশ্ন করুন...",
        "language_selector": "ভাষা নির্বাচন করুন",
        "high_contrast_toggle": "উচ্চ বৈসাদৃশ্য",
        "font_scale": "অক্ষরের আকার",
    },
}

# User preference storage (mock in-memory for testing, DB-backed in user account)
USER_LANGUAGE_PREFERENCES: dict[str, str] = {}


class TranslationRegistry:
    """Authoritative i18n Translation Resolver with English fallback and separate AI directives."""

    @classmethod
    def get_supported_languages(cls) -> list[dict[str, str]]:
        """List all 8 supported languages with native labels and scripts."""
        return list(LANGUAGE_METADATA.values())

    @classmethod
    def get_catalog(cls, lang: str) -> dict[str, str]:
        """Get full translation dictionary for a language code, falling back to English."""
        code = lang.strip().lower()
        base_en = TRANSLATIONS["en"].copy()
        target_dict = TRANSLATIONS.get(code, {})
        base_en.update(target_dict)
        return base_en

    @classmethod
    def get_text(cls, key: str, lang: str = "en", **kwargs: Any) -> str:
        """Resolve translation key with English fallback and parameter interpolation."""
        code = lang.strip().lower()
        target_dict = TRANSLATIONS.get(code, TRANSLATIONS["en"])

        text_template = target_dict.get(key)
        if text_template is None:
            # Fallback to English
            text_template = TRANSLATIONS["en"].get(key, key)

        if kwargs:
            try:
                return text_template.format(**kwargs)
            except (KeyError, ValueError):
                return text_template
        return text_template

    @classmethod
    def get_user_language(cls, user_id: str) -> str:
        """Retrieve user language preference, default English ('en')."""
        return USER_LANGUAGE_PREFERENCES.get(user_id, LanguageCode.EN.value)

    @classmethod
    def set_user_language(cls, user_id: str, lang: str) -> str:
        """Set user language preference."""
        code = lang.strip().lower()
        if code not in TRANSLATIONS:
            code = LanguageCode.EN.value
        USER_LANGUAGE_PREFERENCES[user_id] = code
        return code

    @classmethod
    def get_ai_language_prompt_instruction(cls, lang: str = "en") -> str:
        """Generate isolated system prompt directive for AI responses (decoupled from UI language)."""
        code = lang.strip().lower()
        if code == LanguageCode.HI.value:
            return (
                "SYSTEM LANGUAGE DIRECTIVE: Please respond primarily in Hindi (हिन्दी) using Devanagari script. "
                "Keep scientific and mathematical terms easily understandable, using Hindi terminology alongside standard English in parentheses where beneficial."
            )
        elif code == LanguageCode.SA.value:
            return "SYSTEM LANGUAGE DIRECTIVE: Please respond in simple, grammatically clear Sanskrit (संस्कृतम्) with English transliteration where helpful."
        elif code == LanguageCode.TA.value:
            return "SYSTEM LANGUAGE DIRECTIVE: Please respond in Tamil (தமிழ்)."
        elif code == LanguageCode.TE.value:
            return "SYSTEM LANGUAGE DIRECTIVE: Please respond in Telugu (తెలుగు)."
        elif code == LanguageCode.KN.value:
            return "SYSTEM LANGUAGE DIRECTIVE: Please respond in Kannada (ಕನ್ನಡ)."
        elif code == LanguageCode.MR.value:
            return "SYSTEM LANGUAGE DIRECTIVE: Please respond in Marathi (मराठी)."
        elif code == LanguageCode.BN.value:
            return "SYSTEM LANGUAGE DIRECTIVE: Please respond in Bengali (বাংলা)."
        else:
            return "SYSTEM LANGUAGE DIRECTIVE: Please respond in English."
