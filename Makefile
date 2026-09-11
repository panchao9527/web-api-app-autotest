# 可选快捷方式；Windows 用户可直接运行右侧 Python 命令

.PHONY: install doctor self-test test api web app smoke regression parallel report clean

install:
	python -m pip install -r requirements.txt
	python -m playwright install chromium

doctor:
	python scripts/automation.py doctor

self-test:
	python scripts/automation.py self-test

test:
	python scripts/automation.py test --type all

api:
	python scripts/automation.py test --type api

web:
	python scripts/automation.py test --type web

app:
	python scripts/automation.py test --type app

smoke:
	python scripts/automation.py test --type all --marker smoke

regression:
	python scripts/automation.py test --type all --marker regression

parallel:
	python -m pytest testcases/api testcases/web -m "not app" -n 4 --require-executed

report:
	python scripts/automation.py report

clean:
	python scripts/automation.py clean
