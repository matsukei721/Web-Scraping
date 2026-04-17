setup:
	python -m venv scraping/.venv
	scraping/.venv/bin/pip install -r scraping/requirements.txt

run:
	scraping/.venv/bin/python scraping/main.py $(if $(DATE),--date $(DATE),)
