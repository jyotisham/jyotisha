#!/bin/bash
# This file is to be used after making some corrections to code, which will 
# break tests. Running this file will update all the required files, so that future re-factoring etc.
# can be done, with appropriate tests.
rm -f ~/Documents/Chennai-2019.json
python3 -m jyotisha.panchangam.scripts.write_daily_panchangam_tex  Chennai 13:05:24 80:16:12 'Asia/Calcutta' 2019 devanagari > spatio_temporal/data/daily-cal-2019-Chennai-deva.tex
cp ~/Documents/Chennai-2019.json spatio_temporal/data/

rm -f ~/Documents/Chennai-2018.json
python3 -m jyotisha.panchangam.scripts.write_daily_panchangam_tex  Chennai 13:05:24 80:16:12 'Asia/Calcutta' 2018 devanagari > spatio_temporal/data/daily-cal-2018-Chennai-deva.tex
cp ~/Documents/Chennai-2018.json spatio_temporal/data/

rm -f ~/Documents/Orinda-2019.json
python3 -m jyotisha.panchangam.scripts.write_daily_panchangam_tex  Orinda 37:51:38 -122:10:59 'America/Los_Angeles' 2019 devanagari > spatio_temporal/data/daily-cal-2019-Orinda-deva.tex
cp ~/Documents/Orinda-2019.json spatio_temporal/data/

rm -f ~/Documents/Orinda-2018.json
python3 -m jyotisha.panchangam.scripts.write_daily_panchangam_tex  Orinda 37:51:38 -122:10:59 'America/Los_Angeles' 2018 devanagari > spatio_temporal/data/daily-cal-2018-Orinda-deva.tex
cp ~/Documents/Orinda-2018.json spatio_temporal/data/

python3 -m jyotisha.panchangam.scripts.ics Chennai 13:05:24 80:16:12 'Asia/Calcutta' 2019 devanagari && mv ~/Documents/Chennai-2019-devanagari.ics spatio_temporal/data/ -v

