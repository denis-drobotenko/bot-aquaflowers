from src.ai_manager import detect_user_language

# Тестируем определение языка
test_cases = [
    ("Hello, how are you?", "English"),
    ("Привет, как дела?", "Russian"),
    ("Hola, ¿cómo estás?", "Spanish"),
    ("Bonjour, comment allez-vous?", "French"),
    ("Hallo, wie geht es dir?", "German"),
    ("Ciao, come stai?", "Italian"),
    ("Olá, como você está?", "Portuguese"),
    ("สวัสดีครับ", "Thai"),
    ("That :)", "English"),
    ("No, thx", "English"),
    ("Let it be 4 am tmr", "English"),
    ("Ok, 9 am", "English")
]

print("=== ТЕСТ ОПРЕДЕЛЕНИЯ ЯЗЫКА ===")
for text, expected in test_cases:
    detected = detect_user_language(text)
    print(f"'{text}' -> {detected} (ожидалось: {expected})")

print("\n=== ТЕСТ С ПЕТРОМ ===")
petr_messages = [
    "That :)",
    "Wha?",
    "I don't understand Russian 😅",
    "No, thx",
    "Let it be 4 am tmr",
    "Ok, 9 am"
]

for msg in petr_messages:
    lang = detect_user_language(msg)
    print(f"'{msg}' -> {lang}") 