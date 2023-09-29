type-check:
	mypy src/monitor

lint:
	pylint src --load-plugins pylint_quotes

style-check:
	flake8 src

test:
	pytest src/tests --cov=monitor --cov-report=html && coverage report --fail-under=80
