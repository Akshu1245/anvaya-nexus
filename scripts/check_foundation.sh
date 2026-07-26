#!/usr/bin/env sh
set -eu

python -m pytest backend/tests --ignore=backend/tests/test_production_frontend.py
npm --prefix frontend run lint
npm --prefix frontend run test -- --run
npm --prefix frontend run build
python -m pytest backend/tests/test_production_frontend.py
