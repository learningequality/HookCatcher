# HookCatcher

Generates perceptual diff of Kolibri states.

## Setup

### Install dependencies

```
$ pip install -r requirements.txt
```


### Reference data directory

You'll need a directory for storing data. You can either start from scratch with an empty directory, or use an existing database and image set. See [this repo](https://github.com/MingDai/HookCatcherData) for example.

To point at the data, create a new _user_settings.py_ file in the project root, and add:

```python
DATABASE_DIR = "../HookCatcherData"
```


### Start server

```
$ python manage.py runserver (port)
```

NOTE: port defaults to 8000

To view site enter the following website url into your browser:
http://127.0.0.1:8000/
