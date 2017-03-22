# HookCatcher

Generates perceptual diff of Kolibri states.

## Setup

### Install dependencies

```
$ pip install -r requirements.txt
```


### Reference data directory

You'll need a directory for storing data. You can either start from scratch with an empty directory, or use an existing database and image set. See [this repo](https://github.com/MingDai/HookCatcherData) for example.

To point at the data, create a new _user_settings.py_ file in the project root.
Add the local directory that your data is stored in:

```python
DATABASE_DIR = "../HookCatcherData"
```
Add the Github Repository API that you are testing for:
  For Example:
```python
GIT_REPO_API = "https://api.github.com/repos/MingDai/kolibri/"
```
Add your Github [personal access token](https://help.github.com/articles/creating-a-personal-access-token-for-the-command-line/)
```python
GIT_OAUTH = '756c39c9edbfd20c3c43b5fc6957bf1e446e0787'
```

### Start server

```
$ python manage.py runserver (port)
```

NOTE: port defaults to 8000

To view site enter the following website url into your browser:
http://127.0.0.1:8000/
