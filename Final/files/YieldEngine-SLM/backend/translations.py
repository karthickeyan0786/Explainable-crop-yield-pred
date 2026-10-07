"""
translations.py
------------------
Multilingual phrase dictionaries. English + Tamil fully implemented (Tamil
per your request), Hindi also fully implemented as a second demonstration
language. Structured so any new language can be added by adding one more
dict entry per phrase-key -- no code changes needed elsewhere.
"""

SUPPORTED_LANGUAGES = {
    "en": "English",
    "ta": "தமிழ் (Tamil)",
    "hi": "हिन्दी (Hindi)",
}

FEATURE_LABELS_I18N = {
    "Area": {"en": "Land utilization", "ta": "நில பயன்பாடு", "hi": "भूमि उपयोग"},
    "Season_Encoded": {"en": "Sowing season", "ta": "விதைப்பு பருவம்", "hi": "बुवाई का मौसम"},
    "Crop_Encoded": {"en": "Crop suitability", "ta": "பயிர் பொருத்தம்", "hi": "फसल उपयुक्तता"},
    "pH Level": {"en": "Soil pH balance", "ta": "மண் அமிலத்தன்மை சமநிலை", "hi": "मिट्टी का पीएच संतुलन"},
    "Organic Matter (%)": {"en": "Soil organic matter", "ta": "மண் கரிமப்பொருள்", "hi": "मिट्टी में जैविक पदार्थ"},
    "Nitrogen Content (kg/ha)": {"en": "Nitrogen availability", "ta": "நைட்ரஜன் கிடைப்பு", "hi": "नाइट्रोजन उपलब्धता"},
    "Potassium Content (kg/ha)": {"en": "Potassium availability", "ta": "பொட்டாசியம் கிடைப்பு", "hi": "पोटेशियम उपलब्धता"},
    "Soil_Fertility_Index": {"en": "Soil fertility", "ta": "மண் வளம்", "hi": "मिट्टी की उर्वरता"},
    "Soil_Type_Encoded": {"en": "Soil type suitability", "ta": "மண் வகை பொருத்தம்", "hi": "मिट्टी के प्रकार की उपयुक्तता"},
    "Fertilizer_Consumption": {"en": "Fertilizer usage", "ta": "உரம் பயன்பாடு", "hi": "उर्वरक उपयोग"},
    "Pesticide_Consumption": {"en": "Pesticide usage", "ta": "பூச்சிக்கொல்லி பயன்பாடு", "hi": "कीटनाशक उपयोग"},
    "Annual_Rainfall": {"en": "Rainfall", "ta": "மழைப்பொழிவு", "hi": "वर्षा"},
    "Average_Rainfall": {"en": "Rainfall", "ta": "மழைப்பொழிவு", "hi": "वर्षा"},
    "Rainy_Months_Count": {"en": "Rainfall", "ta": "மழைப்பொழிவு", "hi": "वर्षा"},
    "Average_Temperature": {"en": "Temperature", "ta": "வெப்பநிலை", "hi": "तापमान"},
    "Temperature_Range": {"en": "Temperature stability", "ta": "வெப்பநிலை சீரான தன்மை", "hi": "तापमान स्थिरता"},
    "Weather_Index": {"en": "Weather favourability", "ta": "வானிலை சாதகம்", "hi": "मौसम अनुकूलता"},
    "Climate_Index": {"en": "Climate suitability", "ta": "காலநிலை பொருத்தம்", "hi": "जलवायु उपयुक्तता"},
    "Input_Intensity": {"en": "Input intensity", "ta": "உள்ளீடு அளவு", "hi": "इनपुट तीव्रता"},
    "Agricultural_Intensity": {"en": "Farming intensity", "ta": "விவசாய தீவிரம்", "hi": "कृषि तीव्रता"},
}

RECOMMENDATIONS_I18N = {
    "nitrogen": {"low": {"en": "Apply nitrogen fertilizer in split doses", "ta": "நைட்ரஜன் உரத்தை பிரித்து பல முறை இடவும்", "hi": "नाइट्रोजन उर्वरक को कई बार बांटकर डालें"}},
    "potassium": {"low": {"en": "Apply potash fertilizer to boost potassium levels", "ta": "பொட்டாசியம் அளவை அதிகரிக்க பொட்டாஷ் உரம் இடவும்", "hi": "पोटेशियम स्तर बढ़ाने के लिए पोटाश उर्वरक डालें"}},
    "organic_matter": {"low": {"en": "Add compost or farmyard manure", "ta": "மக்கும் உரம் அல்லது தொழுவ உரத்தை சேர்க்கவும்", "hi": "खाद या गोबर की खाद डालें"}},
    "soil_fertility": {"low": {"en": "Improve fertility using crop rotation and green manure", "ta": "பயிர் சுழற்சி மற்றும் பசுந்தாள் உரம் மூலம் மண் வளத்தை மேம்படுத்தவும்", "hi": "फसल चक्र और हरी खाद से मिट्टी की उर्वरता सुधारें"}},
    "soil_ph": {
        "low": {"en": "Apply agricultural lime to raise soil pH", "ta": "மண்ணின் அமிலத்தன்மையை குறைக்க விவசாய சுண்ணாம்பு இடவும்", "hi": "मिट्टी का पीएच बढ़ाने के लिए कृषि चूना डालें"},
        "high": {"en": "Apply gypsum or organic matter to lower soil pH", "ta": "மண்ணின் காரத்தன்மையை குறைக்க ஜிப்சம் அல்லது கரிமப்பொருள் சேர்க்கவும்", "hi": "मिट्टी का पीएच कम करने के लिए जिप्सम या जैविक पदार्थ डालें"},
    },
    "fertilizer": {"low": {"en": "Apply fertilizer according to soil test recommendations", "ta": "மண் பரிசோதனை பரிந்துரையின்படி உரம் இடவும்", "hi": "मिट्टी परीक्षण सिफारिशों के अनुसार उर्वरक डालें"}},
    "pesticide": {
        "low": {"en": "Apply need-based pesticide protection to control losses", "ta": "இழப்புகளை கட்டுப்படுத்த தேவைக்கேற்ப பூச்சிக்கொல்லி பயன்படுத்தவும்", "hi": "नुकसान रोकने के लिए आवश्यकतानुसार कीटनाशक का प्रयोग करें"},
        "high": {"en": "Reduce pesticide use and adopt integrated pest management", "ta": "பூச்சிக்கொல்லி பயன்பாட்டை குறைத்து ஒருங்கிணைந்த பூச்சி மேலாண்மையை பின்பற்றவும்", "hi": "कीटनाशक का उपयोग कम करें और समेकित कीट प्रबंधन अपनाएं"},
    },
    "rainfall": {"low": {"en": "Use supplemental irrigation during dry periods", "ta": "வறட்சி காலங்களில் கூடுதல் நீர்ப்பாசனம் செய்யவும்", "hi": "सूखे के समय पूरक सिंचाई का उपयोग करें"}},
    "temperature": {
        "low": {"en": "Use row covers or greenhouses to retain warmth", "ta": "வெப்பத்தை தக்கவைக்க பயிர் மூடிகள் அல்லது பாலிஹவுஸ் பயன்படுத்தவும்", "hi": "गर्मी बनाए रखने के लिए रो कवर या पॉलीहाउस का उपयोग करें"},
        "high": {"en": "Use mulching and shade nets to reduce heat stress", "ta": "வெப்ப அழுத்தத்தை குறைக்க மல்ச்சிங் மற்றும் நிழல் வலைகளை பயன்படுத்தவும்", "hi": "गर्मी का तनाव कम करने के लिए मल्चिंग और शेड नेट का उपयोग करें"},
    },
    "weather": {"low": {"en": "Adjust sowing schedule using weather forecasts", "ta": "வானிலை முன்னறிவிப்பை பயன்படுத்தி விதைப்பு நேரத்தை சரிசெய்யவும்", "hi": "मौसम पूर्वानुमान के आधार पर बुवाई का समय समायोजित करें"}},
    "climate": {"low": {"en": "Choose climate-resilient crop varieties", "ta": "காலநிலையை தாங்கும் பயிர் வகைகளை தேர்ந்தெடுக்கவும்", "hi": "जलवायु-सहनशील फसल किस्में चुनें"}},
    "input_intensity": {"low": {"en": "Increase balanced use of fertilizer, water, and inputs", "ta": "உரம், நீர் மற்றும் பிற உள்ளீடுகளின் சீரான பயன்பாட்டை அதிகரிக்கவும்", "hi": "उर्वरक, पानी और अन्य इनपुट का संतुलित उपयोग बढ़ाएं"}},
    "farming_intensity": {"low": {"en": "Adopt improved agronomic practices to raise farming intensity", "ta": "விவசாய தீவிரத்தை அதிகரிக்க மேம்பட்ட விவசாய முறைகளை பின்பற்றவும்", "hi": "कृषि तीव्रता बढ़ाने के लिए बेहतर कृषि पद्धतियां अपनाएं"}},
    "land_utilization": {"low": {"en": "Optimize field spacing and land utilization", "ta": "வயல் இடைவெளி மற்றும் நில பயன்பாட்டை உகந்ததாக்கவும்", "hi": "खेत की दूरी और भूमि उपयोग को अनुकूलित करें"}},
    "soil_type": {"low": {"en": "Adapt farming practices to your soil type", "ta": "உங்கள் மண் வகைக்கேற்ப விவசாய முறைகளை மாற்றிக்கொள்ளவும்", "hi": "अपनी मिट्टी के प्रकार के अनुसार खेती के तरीके अपनाएं"}},
    "crop_choice": {"low": {"en": "Select a crop suitable for local climate and soil", "ta": "உள்ளூர் காலநிலை மற்றும் மண்ணுக்கு ஏற்ற பயிரை தேர்ந்தெடுக்கவும்", "hi": "स्थानीय जलवायु और मिट्टी के अनुकूल फसल चुनें"}},
    "season_choice": {"low": {"en": "Adjust sowing period according to rainfall pattern", "ta": "மழைப்பொழிவு முறைக்கேற்ப விதைப்பு காலத்தை சரிசெய்யவும்", "hi": "वर्षा पैटर्न के अनुसार बुवाई की अवधि समायोजित करें"}},
}

POSITIVE_PHRASES_I18N = {
    "fertilizer": {"en": "Good fertilizer usage", "ta": "நல்ல உரம் பயன்பாடு", "hi": "अच्छा उर्वरक उपयोग"},
    "pesticide": {"en": "Balanced pesticide usage", "ta": "சீரான பூச்சிக்கொல்லி பயன்பாடு", "hi": "संतुलित कीटनाशक उपयोग"},
    "rainfall": {"en": "Suitable rainfall", "ta": "ஏற்ற மழைப்பொழிவு", "hi": "उपयुक्त वर्षा"},
    "soil_ph": {"en": "Healthy soil pH", "ta": "ஆரோக்கியமான மண் அமிலத்தன்மை", "hi": "स्वस्थ मिट्टी पीएच"},
    "organic_matter": {"en": "Healthy soil organic matter", "ta": "ஆரோக்கியமான மண் கரிமப்பொருள்", "hi": "स्वस्थ मिट्टी जैविक पदार्थ"},
    "nitrogen": {"en": "Balanced nitrogen availability", "ta": "சீரான நைட்ரஜன் கிடைப்பு", "hi": "संतुलित नाइट्रोजन उपलब्धता"},
    "potassium": {"en": "Balanced nutrient availability", "ta": "சீரான ஊட்டச்சத்து கிடைப்பு", "hi": "संतुलित पोषक तत्व उपलब्धता"},
    "soil_fertility": {"en": "Healthy soil fertility", "ta": "ஆரோக்கியமான மண் வளம்", "hi": "स्वस्थ मिट्टी उर्वरता"},
    "temperature": {"en": "Suitable temperature", "ta": "ஏற்ற வெப்பநிலை", "hi": "उपयुक्त तापमान"},
    "weather": {"en": "Favourable weather", "ta": "சாதகமான வானிலை", "hi": "अनुकूल मौसम"},
    "climate": {"en": "Favourable climate conditions", "ta": "சாதகமான காலநிலை நிலைமைகள்", "hi": "अनुकूल जलवायु स्थितियां"},
    "input_intensity": {"en": "Good input management", "ta": "நல்ல உள்ளீடு மேலாண்மை", "hi": "अच्छा इनपुट प्रबंधन"},
    "farming_intensity": {"en": "Balanced input intensity", "ta": "சீரான உள்ளீடு அளவு", "hi": "संतुलित इनपुट तीव्रता"},
    "crop_choice": {"en": "Good crop selection", "ta": "நல்ல பயிர் தேர்வு", "hi": "अच्छा फसल चयन"},
    "season_choice": {"en": "Optimal sowing season", "ta": "உகந்த விதைப்பு பருவம்", "hi": "उपयुक्त बुवाई का मौसम"},
    "land_utilization": {"en": "Efficient land utilization", "ta": "திறமையான நில பயன்பாடு", "hi": "कुशल भूमि उपयोग"},
    "soil_type": {"en": "Suitable soil type", "ta": "ஏற்ற மண் வகை", "hi": "उपयुक्त मिट्टी प्रकार"},
}

UI_LABELS_I18N = {
    "predicted_yield": {"en": "Predicted Yield", "ta": "கணிக்கப்பட்ட மகசூல்", "hi": "अनुमानित उपज"},
    "top_positive_factors": {"en": "Top Positive Factors", "ta": "முக்கிய நேர்மறை காரணிகள்", "hi": "मुख्य सकारात्मक कारक"},
    "top_negative_factors": {"en": "Top Factors Reducing Yield", "ta": "மகசூலை குறைக்கும் முக்கிய காரணிகள்", "hi": "उपज कम करने वाले मुख्य कारक"},
    "recommendations": {"en": "Recommendations", "ta": "பரிந்துரைகள்", "hi": "सिफारिशें"},
    "listen": {"en": "Listen", "ta": "கேளுங்கள்", "hi": "सुनें"},
    "why_low_yield": {"en": "Why is my yield low?", "ta": "எனது மகசூல் ஏன் குறைவாக உள்ளது?", "hi": "मेरी उपज कम क्यों है?"},
    "what_should_i_do": {"en": "What should I do?", "ta": "நான் என்ன செய்ய வேண்டும்?", "hi": "मुझे क्या करना चाहिए?"},
}

TTS_LANGUAGE_TAGS = {"en": "en-IN", "ta": "ta-IN", "hi": "hi-IN"}

SEASON_NAMES_I18N = {
    "Kharif": {"en": "Kharif", "ta": "காரிஃப்", "hi": "खरीफ"},
    "Rabi": {"en": "Rabi", "ta": "ரபி", "hi": "रबी"},
    "Summer": {"en": "Summer", "ta": "கோடை", "hi": "गर्मी"},
    "Winter": {"en": "Winter", "ta": "குளிர்காலம்", "hi": "सर्दी"},
    "Autumn": {"en": "Autumn", "ta": "இலையுதிர்காலம்", "hi": "शरद ऋतु"},
    "Whole Year": {"en": "Whole Year", "ta": "முழு ஆண்டு", "hi": "पूरे वर्ष"},
}

CROP_NAMES_I18N = {
    "Rice": {"en": "Rice", "ta": "நெல்", "hi": "चावल"},
    "Wheat": {"en": "Wheat", "ta": "கோதுமை", "hi": "गेहूं"},
    "Maize": {"en": "Maize", "ta": "சோளம்", "hi": "मक्का"},
    "Sugarcane": {"en": "Sugarcane", "ta": "கரும்பு", "hi": "गन्ना"},
    "Cotton(lint)": {"en": "Cotton", "ta": "பருத்தி", "hi": "कपास"},
    "Groundnut": {"en": "Groundnut", "ta": "நிலக்கடலை", "hi": "मूंगफली"},
    "Potato": {"en": "Potato", "ta": "உருளைக்கிழங்கு", "hi": "आलू"},
    "Onion": {"en": "Onion", "ta": "வெங்காயம்", "hi": "प्याज"},
    "Soyabean": {"en": "Soyabean", "ta": "சோயாபீன்", "hi": "सोयाबीन"},
    "Banana": {"en": "Banana", "ta": "வாழை", "hi": "केला"},
    "Coconut": {"en": "Coconut", "ta": "தென்னை", "hi": "नारियल"},
    "Sunflower": {"en": "Sunflower", "ta": "சூரியகாந்தி", "hi": "सूरजमुखी"},
    "Tobacco": {"en": "Tobacco", "ta": "புகையிலை", "hi": "तंबाकू"},
    "Turmeric": {"en": "Turmeric", "ta": "மஞ்சள்", "hi": "हल्दी"},
    "Sesamum": {"en": "Sesamum", "ta": "எள்", "hi": "तिल"},
    "Bajra": {"en": "Bajra", "ta": "கம்பு", "hi": "बाजरा"},
    "Jowar": {"en": "Jowar", "ta": "சோளம் (சார்கம்)", "hi": "ज्वार"},
    "Gram": {"en": "Gram", "ta": "கடலை", "hi": "चना"},
    "Tur": {"en": "Tur", "ta": "துவரை", "hi": "अरहर"},
    "Moong(Green Gram)": {"en": "Moong", "ta": "பாசிப்பயறு", "hi": "मूंग"},
}


def get_translated(dictionary: dict, key: str, lang: str, sub_key: str = None) -> str:
    entry = dictionary.get(key)
    if entry is None:
        return key
    if sub_key is not None:
        sub_entry = entry.get(sub_key)
        if sub_entry is None:
            sub_entry = entry.get("low", {})
        entry = sub_entry
    if isinstance(entry, dict):
        return entry.get(lang) or entry.get("en") or key
    return entry
