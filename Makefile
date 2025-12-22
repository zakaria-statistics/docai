.PHONY: help build up down logs restart clean pull-models chat add query list api-logs api-health api-docs check-ports

help:
	@echo "DocAI Docker Commands"
	@echo "====================="
	@echo "make check-ports   - Check if required ports are available"
	@echo "make build         - Build Docker images"
	@echo "make up            - Start all services (including API)"
	@echo "make down          - Stop all services"
	@echo "make logs          - View logs (all services)"
	@echo "make restart       - Restart all services"
	@echo "make pull-models   - Download Ollama models"
	@echo "make clean         - Stop and remove everything (including volumes)"
	@echo ""
	@echo "CLI Commands (requires services running)"
	@echo "========================================"
	@echo "make chat          - Start chat session"
	@echo "make list          - List indexed documents"
	@echo "make add FILE=path - Add document (e.g., make add FILE=/app/test_docs/file.md)"
	@echo "make query Q=text  - Query documents (e.g., make query Q='What is ML?')"
	@echo ""
	@echo "API Commands"
	@echo "============"
	@echo "make api-logs      - View API server logs"
	@echo "make api-health    - Check API health"
	@echo "make api-docs      - Open API docs in browser"
	@echo "make api-test      - Run API test queries"

check-ports:
	@./check-ports.sh

build:
	docker compose build

up:
	docker compose up -d
	@echo "Waiting for services to be healthy..."
	@sleep 5
	@docker compose ps

down:
	docker compose down

logs:
	docker compose logs -f

restart:
	docker compose restart

pull-models:
	@echo "Pulling llama3.1:8b (this may take 5-10 minutes)..."
	docker exec docai-ollama ollama pull llama3.1:8b
	@echo "Pulling nomic-embed-text..."
	docker exec docai-ollama ollama pull nomic-embed-text
	@echo "Models installed successfully!"
	docker exec docai-ollama ollama list

clean:
	docker compose down -v
	rm -rf ./data/vector_db ./data/documents ./data/sessions
	@echo "All data cleaned!"

# DocAI commands
chat:
	docker compose run --rm docai chat

list:
	docker compose run --rm docai list

add:
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make add FILE=/app/test_docs/file.md"; \
		exit 1; \
	fi
	docker compose run --rm docai add $(FILE)

query:
	@if [ -z "$(Q)" ]; then \
		echo "Usage: make query Q='Your question here'"; \
		exit 1; \
	fi
	docker compose run --rm docai query "$(Q)"

# API commands
api-logs:
	docker compose logs -f docai-api

api-health:
	@echo "Checking API health..."
	@curl -s http://localhost:8080/health | python3 -m json.tool || echo "API not responding"

api-docs:
	@echo "Opening API docs at http://localhost:8080/docs"
	@which xdg-open > /dev/null && xdg-open http://localhost:8080/docs || \
	 which open > /dev/null && open http://localhost:8080/docs || \
	 echo "Please open http://localhost:8080/docs in your browser"

api-test:
	@echo "Testing API endpoints..."
	@echo "\n1. Health check:"
	@curl -s http://localhost:8080/health | python3 -m json.tool
	@echo "\n\n2. List documents:"
	@curl -s http://localhost:8080/documents | python3 -m json.tool
	@echo "\n\n3. Root endpoint:"
	@curl -s http://localhost:8080/ | python3 -m json.tool

# Initial setup
setup: build up pull-models
	@echo "Setup complete!"
	@echo ""
	@echo "Try CLI: make chat"
	@echo "Try API: make api-health"
	@echo "API Docs: http://localhost:8080/docs"
