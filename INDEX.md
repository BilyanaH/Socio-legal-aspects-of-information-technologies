# Data Modeling: Hospital Registry Bulgaria - Navigation Index

## 🎯 Start Here

**New to this project?** → Read [`PROJECT_SUMMARY.md`](PROJECT_SUMMARY.md)  
**Need technical details?** → Read [`DATA_SCHEMA.md`](DATA_SCHEMA.md)  
**Want full documentation?** → Read [`README.md`](README.md)  
**Interested in legal aspects?** → Read [`NORMATIVE_ANALYSIS.md`](NORMATIVE_ANALYSIS.md)

---

## 📚 Documentation Files

| File | Purpose | Size |
|------|---------|------|
| **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** | Executive summary, quick start | ~15 KB |
| **[README.md](README.md)** | Complete project documentation | ~45 KB |
| **[DATA_SCHEMA.md](DATA_SCHEMA.md)** | Data schema, types, validation rules | ~22 KB |
| **[NORMATIVE_ANALYSIS.md](NORMATIVE_ANALYSIS.md)** | Legal analysis and proposals | ~38 KB |
| **INDEX.md** | This file - navigation guide | ~3 KB |

---

## 📊 Data Files

| File | Description | Records | Quality |
|------|-------------|---------|---------|
| **hospitals_ultimate_coords.csv** | ⭐ **MAIN FILE** - All hospitals with coordinates | 468 | Mixed |
| **hospitals_excellent.csv** | High quality coordinates (80-100) | 129 | Excellent |
| **hospitals_lowconf.csv** | Low confidence coordinates (40-59) | 144 | Fair |
| **hospitals_missing.csv** | Hospitals without coordinates | 163 | N/A |
| **hospitals_official_improved.csv** | Normalized addresses | 468 | Cleaned |

---

## 🗺️ Visualization

**[index.html](index.html)** - Interactive map with 305 hospitals

Open in browser to see:
- Color-coded markers by quality
- Filter by region
- Cluster groups
- Hospital information popups

---

## 🔧 Scripts

| Script | Purpose |
|--------|---------|
| **improve_data.py** | Address normalization and cleaning |
| **ultimate_geocode.py** | Multi-strategy geocoding |
| **continue_geocoding.py** | Process remaining hospitals |
| **final_summary.py** | Generate statistics |

---

## 📋 Project Structure

```
proba/
│
├── 📖 DOCUMENTATION
│   ├── INDEX.md                       ← You are here
│   ├── PROJECT_SUMMARY.md             ← Start here!
│   ├── README.md                      ← Full docs
│   ├── DATA_SCHEMA.md                 ← Technical schema
│   └── NORMATIVE_ANALYSIS.md          ← Legal analysis
│
├── 📊 DATA FILES
│   ├── hospitals_ultimate_coords.csv  ← ⭐ MAIN FILE
│   ├── hospitals_excellent.csv
│   ├── hospitals_lowconf.csv
│   ├── hospitals_missing.csv
│   ├── hospitals_official_cleaned.csv
│   └── hospitals_official_improved.csv
│
├── 🗺️ VISUALIZATION
│   └── index.html                     ← Interactive map
│
├── 🔧 SCRIPTS
│   ├── improve_data.py
│   ├── ultimate_geocode.py
│   ├── continue_geocoding.py
│   └── final_summary.py
│
└── 💾 CACHE & LOGS
    ├── ultimate_cache.json
    └── geocode_log.txt
```

---

## 🎓 For Academic Submission

### Required Documents

1. **Project Description** → `PROJECT_SUMMARY.md`
2. **Data Model** → `DATA_SCHEMA.md` + `hospitals_ultimate_coords.csv`
3. **Legal Analysis** → `NORMATIVE_ANALYSIS.md`
4. **Demonstration** → `index.html` (open in browser)

### Key Points

✅ Registry: Hospital facilities with NHIF contracts  
✅ Source: https://services.nhif.bg/references/lists/hospital.xhtm  
✅ Format: CSV (UTF-8) - compliant with Open Definition  
✅ Records: 468 hospitals, 305 with coordinates (65.2%)  
✅ Quality: 3-tier system (Excellent, Good, Fair)  
✅ Legal: Detailed proposals for normative changes  

---

## 🚀 Quick Actions

### View the Data

```bash
# Open in Excel/LibreOffice
File → Open → hospitals_ultimate_coords.csv
Encoding: UTF-8, Delimiter: ,
```

### View the Map

```bash
# Open in browser
Double-click: index.html
```

### Filter by Quality

```python
import pandas as pd

df = pd.read_csv('hospitals_ultimate_coords.csv', encoding='utf-8')

# Only excellent quality
excellent = df[df['quality_score'] >= 80]
print(f"Excellent: {len(excellent)} hospitals")

# Only with coordinates
with_coords = df[df['lat'].notna()]
print(f"With coordinates: {len(with_coords)} hospitals")
```

---

## 📈 Project Statistics

- **Total hospitals:** 468
- **With coordinates:** 305 (65.2%)
- **Excellent quality:** 129 (27.6% of total, 42.3% of geocoded)
- **Good quality:** 32 (6.8% of total, 10.5% of geocoded)
- **Fair quality:** 144 (30.8% of total, 47.2% of geocoded)
- **Without coordinates:** 163 (34.8%)

### Quality Distribution

```
★★★ Excellent (80-100): ████████████████░░░░░░░░░░░░░░░░ 42.3%
★★  Good (60-79):       ███░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 10.5%
★   Fair (40-59):       ███████████████░░░░░░░░░░░░░░░░░ 47.2%
```

---

## 🔗 External Links

- **NHIF Registry:** https://services.nhif.bg/references/lists/hospital.xhtm
- **Open Data Portal:** https://data.egov.bg/
- **Open Definition:** https://opendefinition.org/ofd/
- **OpenStreetMap:** https://www.openstreetmap.org/
- **Nominatim API:** https://nominatim.openstreetmap.org/

---

## 📞 Contact & Support

For questions about:
- **Data quality** → See `DATA_SCHEMA.md` section on validation
- **Geocoding** → See `README.md` section on processing
- **Legal aspects** → See `NORMATIVE_ANALYSIS.md`
- **Technical issues** → Check script comments in Python files

---

## ✅ Checklist for Reviewers

- [ ] Read `PROJECT_SUMMARY.md` for overview
- [ ] Open `hospitals_ultimate_coords.csv` in Excel/LibreOffice
- [ ] Open `index.html` in browser to see map
- [ ] Review `DATA_SCHEMA.md` for technical details
- [ ] Review `NORMATIVE_ANALYSIS.md` for legal proposals
- [ ] Check `README.md` for complete documentation

---

## 🎯 Mission Accomplished

✅ **State-regulated registry** identified and analyzed  
✅ **Data model** created with proper schema  
✅ **Open format** (CSV, UTF-8) compliant with standards  
✅ **Geographic enrichment** with quality scoring  
✅ **Legal analysis** with concrete proposals  
✅ **Visualization** with interactive map  
✅ **Documentation** complete and structured  

---

**Project Date:** October 27, 2025  
**Version:** 1.0  
**Status:** Complete ✅
