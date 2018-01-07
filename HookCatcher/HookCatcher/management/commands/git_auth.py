'''
ISSUES: sometimes the JWT will return
{u'documentation_url': u'https://developer.github.com/v3',
 u'message': u"'Expiration time' claim ('exp') is too far in the future"}
and generating new private key on the Git App will get rid of this issue


'''

import json
from datetime import datetime

import jwt
import requests
from django.conf import settings  # database dir
from django.core.management.base import BaseCommand
from github import Github


def git_auth_header(pemfile):
    INSTALLATION_ID = 5199  # FIND ID on app
    # link: settings https://github.com/settings/apps/health-inspector

    time_now = int((datetime.now()-datetime(1970, 1, 1)).total_seconds())
    time_after = time_now + (10 * 60)

    payload = {
        # issued at time
        'iat': time_now,
        # JWT expiration time (10 minute maximum)
        'exp': time_after,
        # GitHub App's identifier
        'iss': INSTALLATION_ID
    }

    with open(pemfile, 'r') as pem_file:
        # Authenticate JWT as a GitHub App
        key = pem_file.read()
        token = jwt.encode(payload, key, algorithm='RS256')

        headers = {
            'Authorization': 'Bearer ' + token,
            'Accept': 'application/vnd.github.machine-man-preview+json',
        }

        return headers


def create_new_token(headers):
    # Authenticate as an installation
    app_url = 'https://api.github.com/app/installations'
    reply = requests.get(app_url, headers=headers)

    # ASUMPTION: with list of installations using the Private key,
    #            the first installation is right one

    # QUESTION: How to install same Github APP on different people's Githubs
    install_id = json.loads(reply.text)[0]['id']

    install_url = 'https://api.github.com/app/installations/{0}'\
        .format(install_id)

    install_reply = requests.get(install_url, headers=headers)
    access_tokens_url = json.loads(install_reply.text)['access_tokens_url']

    find_existing_tokens = requests.post(access_tokens_url, headers=headers)
    existing_access_tokens = json.loads(find_existing_tokens.text)

    return existing_access_tokens['token']


class Command(BaseCommand):
    def add_arguments(self, parser):
        # Select the Commit to add a status to
        parser.add_argument('status', type=str)
        # TODO: figure out what to replace the hardset repo to some variable
        parser.add_argument('git_repo', type=str)
        parser.add_argument('commit_hash', type=str)

    def handle(self, *args, **options):
        PEMFILE = settings.GITHUB_APP_PEMFILE
        HEADER = git_auth_header(PEMFILE)

        TOKEN = create_new_token(HEADER)

        # Use github to get the commit that we want to set status for
        g = Github(TOKEN)

        r = g.get_repo(full_name_or_id=options['git_repo'])

        c = r.get_commit(options['commit_hash'])

        status_msg_map = {'success': 'All visual diffs were generated and approved!',
                          'pending': 'There are states that have changed. Please approve of these changes.',  # noqa: E501
                          'failure': 'States are unapproved. Please approve of these changes.',
                          'error': 'Health Inspector had a build error! Please check the history.'}

        '''
            Only commit statuses for the most recent commit in the PR are shown in review
            otherwise, can be found next to the 'commits' tab of PR

            NOTE: CANNOT EDIT OR REMOVE commit statuses
        '''

        c.create_status(options['status'],
                        target_url='https://google.com',
                        description=status_msg_map[options['status']],
                        context='health-inspector')

        print 'Commit status: {0} added'.format(options['status'])
