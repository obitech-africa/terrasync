.PHONY: demo test docker

demo:
	cd backend && python -m uvicorn app.main:app --reload

test:
	cd backend && python -m pytest -q

docker:
	cd docker && docker compose up --build

db-status:
	cd backend && python -m app.db.migrate status

db-bootstrap:
	cd backend && python -m app.db.migrate bootstrap

db-upgrade:
	cd backend && python -m app.db.migrate upgrade

db-check:
	cd backend && python -m app.db.migrate check


prod-build:
	cd docker && docker compose build

prod-migrate:
	cd docker && docker compose run --rm migrate

prod-up:
	cd docker && docker compose up -d

prod-down:
	cd docker && docker compose down

prod-logs:
	cd docker && docker compose logs -f api

prod-status:
	cd docker && docker compose ps
