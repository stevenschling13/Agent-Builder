.PHONY: run api test
run: ; python -m src.app.cli "help"
api: ; uvicorn src.app.main:app --reload
test: ; pytest -q
