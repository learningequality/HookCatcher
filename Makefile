migrate:
	python HookCatcher/manage.py migrate

rundevserver: migrate
	python HookCatcher/manage.py runserver 0.0.0.0:8080
