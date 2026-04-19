dev-db:
	docker-compose up -d postgres redis

dev-backend:
	cd backend && make run

dev-bot:
	cd bot && make run

dev-frontend:
	cd frontend && npm run dev

install-all:
	cd backend && make install
	cd bot && make install
	cd frontend && npm install

test-all:
	cd backend && make test

# Verify that everything is up
check:
	@echo "--- Health check ---"
	@curl -s http://localhost:8000/health | python3 -m json.tool
	@echo "--- DB check ---"
	@docker-compose exec postgres pg_isready -U postgres
