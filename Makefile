PYTHON ?= python3

.PHONY: run db-init db-migrate compile

run:
	$(PYTHON) -m uvicorn app.main:app --reload

db-init:
	$(PYTHON) scripts/init_db.py

db-migrate:
	alembic upgrade head

compile:
	$(PYTHON) -m compileall app
