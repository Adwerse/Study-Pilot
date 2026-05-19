PYTHON=python3.11

install:
	$(PYTHON) -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt

run:
	.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

migrate:
	for f in migrations/*.sql; do \
		echo "Running $$f..."; \
		psql $$DATABASE_URL -f $$f; \
	done

test:
	.venv/bin/pytest tests/ -v

lint:
	.venv/bin/ruff check app/
	.venv/bin/ruff format --check app/

health:
	curl -s http://localhost:8000/health | python3 -m json.tool

ready:
	curl -s http://localhost:8000/health/ready | python3 -m json.tool
