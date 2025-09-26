.PHONY: run api test
run: ; python -m src.app.cli "Help"
api: ; uvicorn src.app.main:app --reload
test: ; pytest -q
