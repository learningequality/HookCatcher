migrate:
	python HookCatcher/manage.py migrate

rundevserver: migrate
	python HookCatcher/manage.py runserver 0.0.0.0:8080

rqworkers:
	yarn add puppeteer
	python HookCatcher/manage.py rqworker default
