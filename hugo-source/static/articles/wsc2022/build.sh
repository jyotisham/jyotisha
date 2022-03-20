#!/usr/bin/bash

while true; do
rm *.bbl *.blg *.aux
xelatex jyotisha_py__fest_db
bibtex jyotisha_py__fest_db
xelatex jyotisha_py__fest_db
xelatex jyotisha_py__fest_db
sleep 25
done
