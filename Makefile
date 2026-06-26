# 常用命令快捷方式，本地运行 `make <目标>`

.PHONY: install test api web app smoke report clean

install:        ## 安装依赖 + Playwright 浏览器
	pip install -r requirements.txt
	playwright install chromium

test:           ## 跑全部用例
	pytest

api:            ## 只跑接口测试
	pytest -m api

web:            ## 只跑 Web 测试
	pytest -m web

app:            ## 只跑 App 测试
	pytest -m app

smoke:          ## 只跑冒烟用例(P0核心链路)
	pytest -m smoke

parallel:       ## 并发跑(4进程加速)
	pytest -n 4

report:         ## 本地生成并打开 Allure 报告
	allure serve reports/allure-results

clean:          ## 清理报告/日志/缓存
	rm -rf reports/allure-results reports/allure-report logs .pytest_cache
