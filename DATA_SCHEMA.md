# Схема на данните (Data Schema)

## JSON Schema за hospitals_ultimate_coords.csv

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Hospital Registry Entry",
  "description": "Схема на запис в Националния регистър на лечебните заведения с договор с НЗОК",
  "type": "object",
  "required": [
    "Наименование",
    "Област",
    "Община",
    "Населено място",
    "Адрес"
  ],
  "properties": {
    "id": {
      "type": "integer",
      "description": "Уникален идентификатор на записа",
      "minimum": 1
    },
    "Наименование": {
      "type": "string",
      "description": "Пълно наименование на лечебното заведение",
      "maxLength": 500,
      "examples": [
        "МБАЛ Света Анна София ЕАД",
        "УМБАЛ Александровска ЕАД"
      ]
    },
    "Област": {
      "type": "string",
      "description": "Област по административно-териториалното деление на България",
      "maxLength": 100,
      "examples": [
        "София",
        "Пловдив",
        "Варна",
        "Бургас"
      ]
    },
    "Община": {
      "type": "string",
      "description": "Община",
      "maxLength": 100
    },
    "Населено място": {
      "type": "string",
      "description": "Град или село",
      "maxLength": 100
    },
    "Адрес": {
      "type": "string",
      "description": "Пълен адрес на заведението",
      "maxLength": 200,
      "examples": [
        "бул. Пещерско шосе 66",
        "ул. Георги Софийски 1"
      ]
    },
    "Управител": {
      "type": ["string", "null"],
      "description": "Имена на управителите на заведението",
      "maxLength": 200
    },
    "Телефон": {
      "type": ["string", "null"],
      "description": "Телефонни номера за контакт",
      "maxLength": 100
    },
    "lat": {
      "type": ["number", "null"],
      "description": "Географска ширина (latitude) в WGS84",
      "minimum": 41.0,
      "maximum": 44.5
    },
    "lng": {
      "type": ["number", "null"],
      "description": "Географска дължина (longitude) в WGS84",
      "minimum": 22.0,
      "maximum": 29.0
    },
    "quality_score": {
      "type": ["integer", "null"],
      "description": "Качество на геокодирането (0-100)",
      "minimum": 0,
      "maximum": 100
    },
    "provider": {
      "type": ["string", "null"],
      "description": "Източник на геокодирането",
      "enum": [
        "nominatim_free",
        "nominatim_structured",
        "overpass",
        "nominatim_free_lowconf",
        "nominatim_structured_lowconf",
        "overpass_lowconf",
        null
      ]
    },
    "display_name": {
      "type": ["string", "null"],
      "description": "Пълен адрес от геокодера",
      "maxLength": 500
    },
    "street_number": {
      "type": ["string", "null"],
      "description": "Извлечен номер на сграда",
      "maxLength": 20
    },
    "street_name_clean": {
      "type": ["string", "null"],
      "description": "Почистено име на улица без номер",
      "maxLength": 200
    },
    "search_query": {
      "type": ["string", "null"],
      "description": "Оптимизирана заявка за геокодиране",
      "maxLength": 500
    },
    "original_address": {
      "type": ["string", "null"],
      "description": "Оригинален адрес преди нормализация",
      "maxLength": 200
    },
    "original_city": {
      "type": ["string", "null"],
      "description": "Оригинално име на град преди нормализация",
      "maxLength": 100
    }
  }
}
```

## Типове данни (SQL DDL)

```sql
CREATE TABLE hospitals (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    
    -- Основни данни от НЗОК
    naimenovanie VARCHAR(500) NOT NULL COMMENT 'Наименование на лечебното заведение',
    oblast VARCHAR(100) NOT NULL COMMENT 'Област',
    obshtina VARCHAR(100) NOT NULL COMMENT 'Община',
    naseleno_miasto VARCHAR(100) NOT NULL COMMENT 'Населено място',
    adres VARCHAR(200) NOT NULL COMMENT 'Адрес',
    upravitel VARCHAR(200) COMMENT 'Управител',
    telefon VARCHAR(100) COMMENT 'Телефон',
    
    -- Географски данни
    lat DECIMAL(10,7) COMMENT 'Latitude (WGS84)',
    lng DECIMAL(10,7) COMMENT 'Longitude (WGS84)',
    quality_score TINYINT UNSIGNED COMMENT 'Качество на геокодирането (0-100)',
    provider VARCHAR(50) COMMENT 'Източник на координатите',
    display_name VARCHAR(500) COMMENT 'Пълен адрес от геокодера',
    
    -- Извлечени данни
    street_number VARCHAR(20) COMMENT 'Номер на сграда',
    street_name_clean VARCHAR(200) COMMENT 'Име на улица',
    search_query VARCHAR(500) COMMENT 'Search query',
    
    -- Оригинални данни
    original_address VARCHAR(200) COMMENT 'Оригинален адрес',
    original_city VARCHAR(100) COMMENT 'Оригинален град',
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    data_version VARCHAR(20),
    
    -- Индекси
    INDEX idx_oblast (oblast),
    INDEX idx_city (naseleno_miasto),
    INDEX idx_quality (quality_score),
    INDEX idx_coords (lat, lng),
    
    -- Пълнотекстово търсене
    FULLTEXT INDEX ft_name (naimenovanie),
    FULLTEXT INDEX ft_address (adres)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

## Data Dictionary (Речник на данните)

| Поле | Тип | Дължина | Null | Описание | Пример |
|------|-----|---------|------|----------|--------|
| `id` | Integer | - | No | Уникален идентификатор | 1 |
| `Наименование` | String | 500 | No | Наименование на заведението | "МБАЛ Света Анна София ЕАД" |
| `Област` | String | 100 | No | Област | "София" |
| `Община` | String | 100 | No | Община | "СОФИЯ" |
| `Населено място` | String | 100 | No | Град/село | "София" |
| `Адрес` | String | 200 | No | Пълен адрес | "бул. Димитър Моллов 1" |
| `Управител` | String | 200 | Yes | Управител(и) | "Д-Р ИВАН ПЕТРОВ" |
| `Телефон` | String | 100 | Yes | Телефони | "02/1234567, 0888123456" |
| `lat` | Decimal | 10,7 | Yes | Latitude (градуси) | 42.6977082 |
| `lng` | Decimal | 10,7 | Yes | Longitude (градуси) | 23.3218675 |
| `quality_score` | Integer | 0-100 | Yes | Качество на координатите | 95 |
| `provider` | String | 50 | Yes | Геокодер | "nominatim_free" |
| `display_name` | String | 500 | Yes | Адрес от геокодера | "1, Георги Софийски..." |
| `street_number` | String | 20 | Yes | Номер на сграда | "66" |
| `street_name_clean` | String | 200 | Yes | Име на улица | "Пещерско шосе" |
| `search_query` | String | 500 | Yes | Търсеща заявка | "бул. Пещерско шосе 66, Пловдив, България" |
| `original_address` | String | 200 | Yes | Оригинален адрес | "бул. Пещерско шосе 66 ет. 1" |
| `original_city` | String | 100 | Yes | Оригинален град | "ГР. Пловдив" |

## Качествени класове (Quality Tiers)

| Клас | Score | Критерии | Употреба |
|------|-------|----------|----------|
| **Excellent** | 80-100 | Точен адрес с номер, проверен град, високоточни координати | Production-ready, navigation |
| **Good** | 60-79 | Адрес без номер или приблизителен номер | Показване с предупреждение |
| **Fair** | 40-59 | Ниво квартал/улица без номер | Reference only, no navigation |
| **Poor** | 1-39 | Само град или неточни данни | Не се препоръчва |
| **Missing** | NULL | Не е намерен | Изисква ръчна обработка |

## Валидационни правила

### 1. Координати
```python
# България: приблизителни граници
41.0 <= lat <= 44.5
22.0 <= lng <= 29.0
```

### 2. Адрес
```python
# Задължителни компоненти
required = ['Населено място', 'Адрес']

# Формат на адрес (регулярен израз)
address_pattern = r'^(ул\.|бул\.|жк|пл\.)\s+.+\s+\d+.*$'
```

### 3. Quality Score
```python
# Диапазон
0 <= quality_score <= 100

# Препоръчително минимум
quality_score >= 60  # за production
```

## Формати за export

### CSV
```
Encoding: UTF-8
Delimiter: , (comma)
Quote: " (double quote)
Escape: \ (backslash)
Line ending: \n (LF)
Header: Yes (first row)
```

### JSON
```json
{
  "hospitals": [
    {
      "id": 1,
      "name": "МБАЛ Света Анна София ЕАД",
      "location": {
        "region": "София",
        "municipality": "СОФИЯ",
        "city": "София",
        "address": "бул. Димитър Моллов 1",
        "coordinates": {
          "lat": 42.6977082,
          "lng": 23.3218675,
          "quality": 100
        }
      },
      "contact": {
        "manager": "Д-Р ИВАН ПЕТРОВ",
        "phone": "02/1234567"
      },
      "metadata": {
        "provider": "nominatim_free",
        "last_updated": "2025-10-27T14:30:00Z"
      }
    }
  ]
}
```

### GeoJSON
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [23.3218675, 42.6977082]
      },
      "properties": {
        "name": "МБАЛ Света Анна София ЕАД",
        "address": "бул. Димитър Моллов 1",
        "city": "София",
        "region": "София",
        "quality_score": 100,
        "phone": "02/1234567"
      }
    }
  ]
}
```

## API Endpoints (препоръчителни)

```
GET /api/v1/hospitals
GET /api/v1/hospitals/{id}
GET /api/v1/hospitals?region={oblast}
GET /api/v1/hospitals?city={city}
GET /api/v1/hospitals?quality_min={score}
GET /api/v1/hospitals/near?lat={lat}&lng={lng}&radius={km}
```

## Metadata (съгласно DCAT стандарт)

```json
{
  "title": "Национален регистър на лечебните заведения с договор с НЗОК",
  "description": "Регистър на всички лечебни заведения в България с договор с Национална здравноосигурителна каса, обогатен с географски координати",
  "publisher": "Национална здравноосигурителна каса (НЗОК)",
  "issued": "2025-10-27",
  "modified": "2025-10-27",
  "language": "bg",
  "spatial": "България",
  "temporal": "2025",
  "format": ["CSV", "JSON", "GeoJSON"],
  "license": "CC-BY-4.0",
  "accrualPeriodicity": "monthly",
  "distribution": [
    {
      "format": "CSV",
      "downloadURL": "hospitals_ultimate_coords.csv"
    }
  ],
  "keyword": [
    "болници",
    "здравеопазване",
    "НЗОК",
    "лечебни заведения",
    "координати",
    "геолокация"
  ]
}
```
