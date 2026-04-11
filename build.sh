#!/bin/bash
pip install -r requirements.txt
python -c "from app_enhanced import init_db; init_db(); print('DB initialized')"
