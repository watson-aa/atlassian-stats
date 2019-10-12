import configparser
import requests
import db
import datetime

class Bitbucket:
    __config = None

    # statics
    _page_size = 100
    _loop_limit = 25

    def __init__(self):
        pass

    def loadConfig(self, config_file):
        self.__config = configparser.ConfigParser()
        self.__config.read(config_file)
        return self.__config

    def loadData(self, start_date):
        for project in self.__config['projects']:
            self._getDataFromApi(project, self.__config['projects'][project], start_date)

    def _makeApiRequest(self, url, auth, verify):
        response = requests.get(url, verify=verify, auth=auth)
        if response.status_code == 200:
            return response.json()
        else:
            print(url + ' -- ' + str(response.status_code))
            return {}

    def __extractActData(self, activity_id, data):
        reviewers = []
        comments = []
        for value in data['values']:
            if value['action'] == 'COMMENTED':
                comments.append({
                    'activityId': activity_id,
                    'createdDate': value['createdDate'],
                    'user': value['user']['slug'],
                    'commentAction': value['commentAction'],
                    'comment': value['comment']['text']
                })
            elif value['action'] == 'APPROVED' or value['action'] == 'UNAPPROVED':
                reviewers.append({
                    'activityId': activity_id,
                    'createdDate': value['createdDate'],
                    'user': value['user']['slug'],
                    'action': value['action']
                })
        return (reviewers, comments)

    def _getDataFromApi(self, project_name, project, start_date):
        earliest_date = datetime.datetime.now()
        counter = 0

        conn = db.Connection(self.__config['database'])

        while earliest_date > start_date and counter < self._loop_limit:
            url = 'https://' + self.__config['server']['Domain'] + self.__config['server']['ApiPath'] + project + '?state=ALL&limit=' + str(self._page_size) + '&start=' + str(self._page_size * counter)
            auth = (self.__config['server']['User'], self.__config['server']['Password'])

            data = self._makeApiRequest(url, auth, False)
            (activities, users) = self.__extractPRData(project_name, data)

            conn.addUsers(users)
            earliest_date = conn.addActivities(activities)

            for activity in activities:
                url = 'https://' + self.__config['server']['Domain'] + self.__config['server']['ApiPath'] + project + '/' + str(activity['id']) + '/activities'
                data = self._makeApiRequest(url, auth, False)
                (reviewers, comments, users) = self.__extractActData(activity['id'], data)
                conn.addUsers(users)
                conn.addReviewers(reviewers)
                conn.addComments(comments)

            counter += 1

        conn.closeConnection()

    def __extractPRData(self, project_name, data):
        actions = []
        users = {}
        reviews = []
        for value in data['values']:
            actions.append({
                'id': value['id'],
                'title': value['title'],
                'description': value['description'] if value.get('description') else '',
                'state': value['state'],
                'open': value['open'],
                'closed': value['closed'],
                'createdDate': value['createdDate'],
                'updatedDate': value['updatedDate'],
                'closedDate': 0 if not value.get('closedDate') else value['closedDate'],
                'author': value['author']['user']['slug'],
                'fromBranch': value['fromRef']['displayId'],
                'toBranch': value['toRef']['displayId'],
                'comments': '' if not value['properties'].get('commentCount') else value['properties']['commentCount'],
                'project': project_name
            })
            users[value['author']['user']['slug']] = value['author']['user']

        return (actions, users)

    def __extractActData(self, activity_id, data):
        reviewers = []
        comments = []
        users = {}
        for value in data['values']:
            if value['action'] == 'COMMENTED':
                comments.append({
                    'activityId': activity_id,
                    'createdDate': value['createdDate'],
                    'user': value['user']['slug'],
                    'commentAction': value['commentAction'],
                    'comment': value['comment']['text']
                })
            elif value['action'] == 'APPROVED' or value['action'] == 'UNAPPROVED':
                reviewers.append({
                    'activityId': activity_id,
                    'createdDate': value['createdDate'],
                    'user': value['user']['slug'],
                    'action': value['action']
                })
            users[value['user']['slug']] = value['user']
            
        return (reviewers, comments, users)

if __name__ == '__main__':
    bb = Bitbucket()
    bb.loadConfig('./config/bitbucket.ini')
    bb.loadData(datetime.datetime.now() - datetime.timedelta(days=3))