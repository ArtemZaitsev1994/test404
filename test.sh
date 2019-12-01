#!/bin/bash
source ../env/bin/activate
python messengers/server.py &
pytest -s -v server/test.py
echo 'start'
sleep 3
kill -9 %1
