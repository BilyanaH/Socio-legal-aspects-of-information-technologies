# Manual coordinates for addresses that cannot be geocoded automatically
# Format: "street||city||oblast": {"lat": ..., "lng": ..., "provider": "manual", "display_name": "..."}

MANUAL_COORDS = {
    # Burgas problematic addresses - using approximate hospital locations based on public sources
    "Стефан Стамболов 73||БУРГАС||Бургас": {
        "lat": 42.492,
        "lng": 27.470,
        "provider": "manual",
        "display_name": "ул. Стефан Стамболов 73, Бургас (approximate)"
    },
    "Доцд-р Константин Кънчев||БУРГАС||Бургас": {
        "lat": 42.493,
        "lng": 27.471,
        "provider": "manual",
        "display_name": "ул. Доц.д-р Константин Кънчев, Бургас (approximate)"
    },
    
    # Sofia addresses
    "Столов 67||СОФИЯ||София (столица)": {
        "lat": 42.6708,
        "lng": 23.3215,
        "provider": "manual",
        "display_name": "бул. Столетов 67, София (approximate)"
    },
    "Сливница 309||СОФИЯ||София (столица)": {
        "lat": 42.7144,
        "lng": 23.2753,
        "provider": "manual",
        "display_name": "бул. Сливница 309, София (approximate)"
    }
}
