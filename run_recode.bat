@echo off
echo Starting full re-geocoding...
python full_recode_free.py > full_recode_output.txt 2>&1
echo Done! Check full_recode_output.txt for results
pause
