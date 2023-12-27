presubmit: format check_type lint

format:
	isort script 
	pyink script

check_type:
	mypy script

lint:
	pylint script
