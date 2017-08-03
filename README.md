# Auto-Screenshots

Generates perceptual diff of a git repository as you make pull requests.

## Setup

### Install dependencies

#### System Requirements
Download and install the following:
[Python 2](https://www.python.org/downloads/) w/ pip installed<br />
[Node](https://nodejs.org/en/) w/ npm installed<br />
[Redis](https://redis.io/)<br />
[PostgreSQL](https://www.postgresql.org/)<br />
  ```postgres
  CREATE DATABASE garnish_db
  CREATE USER garnish_user WITH LOGIN PASSWORD 'garnish'
  ```
[PhantomJS](http://phantomjs.org/)<br />

#### Python Packages
```
$ pip install -r requirements.txt
$ yarn install
```

### Initial setup and personal configurations

First, you'll need a directory for storing data. You can either start from scratch with an empty directory, or use an existing database and image set. See [this repo](https://github.com/MingDai/HookCatcherData) for example.


To point at the data, create a new _user_settings.py_ file in the project root.
Add the local directory that your data is stored in:

```python
DATABASE_DIR = "../HookCatcherData"
```

Add the Github Repository that you are testing for:
https://github.com/YOUR_GITHUB_USERNAME/YOUR_GITHUB_REPO
```python
GIT_REPO = "YOUR_GITHUB_USERNAME/YOUR_GITHUB_REPO"
```

Add your Github [personal access token](https://help.github.com/articles/creating-a-personal-access-token-for-the-command-line/):
```python
GIT_OAUTH = 'YOU_AUTH_ID_HERE'
```

Add the name of the directory in the Git Repository that stores the state representation JSON files. See [this folder](https://github.com/MingDai/kolibri/tree/test-master/states) for example:
```python
STATES_FOLDER = 'NAME_OF_YOUR_STATES_FOLDER'
```

Add the file path to the directory of the Github repo you are testing on:
```python
WORKING_DIR = 'PATH_TO_YOUR_WORKING_DIR'
```

You need to set what tools and resolutions you want to take all your screenshots in. Add the screenshot configuration file to root of this directory. See [this file](https://github.com/MingDai/HookCatcher/blob/develop/config.json) for example:
```python
SCREENSHOT_CONFIG = "NAME_OF_YOUR_CONFIG_FILE"
```

### Start server

```
$ python manage.py runserver (port)
```

NOTE: port defaults to 8000

To view site enter the following website url into your browser:
http://127.0.0.1:8000/


## Command Line Tools
In the root of this directory utilize the following Django commands.

#### Generate screenshots and take Image Diffs of a Github Pull Request
NOTE: you must run redis-server before you run the auto-screenshot command
```
$ redis-server
--- open a new terminal view ---
$ python manage.py auto-screenshot <Github Pull Request Number>
```

#### Generate a full-page screenshot of a url using PhantomJS
```
$ python manage.py genScreenshot <URL> <Image Name>
```

#### Generate a perceptual diff between two images using ImageMagick
```
$ python manage.py genDiff imagemagick <Image Name 1> <Image Name 2> <Resulting Diff Name>
```
