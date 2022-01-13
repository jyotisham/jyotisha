#!/bin/bash
# This file is to be used after making some corrections to code, which will 
# break tests. Running this file will update all the required files, so that future re-factoring etc.
# can be done, with appropriate tests.
find spatio_temporal/data/ -type f | grep -v timing | xargs rm
# find . -name *.md* | xargs dos2unix
pytest
