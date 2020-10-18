lint:
	@echo "\n${BLUE}Running Pylint against source and test files...${NC}\n"
	@pylint --rcfile=setup.cfg **/*.py **/boards/*.py

run:
	python3 source/scraper.py
