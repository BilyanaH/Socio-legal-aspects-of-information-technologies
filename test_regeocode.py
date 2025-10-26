from geocode_hospitals import geocode_address

tests = [
    ("бул. 25-ти септември 68", "Добрич", "Добрич", "ДКЦ-2-Добрич ЕООД"),
    ("ул. Димитър Петkov №3", "Добрич", "Добрич", "ДКЦ-I-Добрич ЕООД"),
]

for addr, city, oblast, name in tests:
    print("Testing:", name, addr, city, oblast)
    res = geocode_address(addr, city, oblast, name_hint=name)
    print("Result:", res)
    print()
