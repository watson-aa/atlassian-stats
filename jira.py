import common
import db
import datetime

class Jira:
    __config = None

    def __init__(self):
        pass

    def loadConfig(self, config_file):
        self.__config = common.loadConfig(config_file)

    # TODO: implement end_date
    def loadData(self, start_date, end_date):
        for project in self.__config['projects']:
            self._getIssueDataFromApi(project, self.__config['projects'][project], start_date) 

    def _getChangelogDataFromApi(self, issue, conn):
        url = 'https://' + self.__config['server']['Domain'] + self.__config['server']['ApiPath'] + 'issue/' + issue + '?expand=changelog'
        auth = (self.__config['server']['User'], self.__config['server']['Password'])
        data = common.makeApiRequest(url, auth, False)

        changelog = self.__extractChangelogData(data)
        conn.addChangelog(changelog)

    def _getIssueDataFromApi(self, project, project_name, start_date):
        earliest_date = datetime.datetime.now()

        conn = db.Connection(self.__config['database'])

        start = 0
        total = 50
        while start <= total: 
            url = 'https://' + self.__config['server']['Domain'] + self.__config['server']['ApiPath'] + 'search?jql=status%20%3D%20' + self.__config['server']['Status'] + '%20AND%20project%20%3D%20' + project + '&startAt=' + str(start)
            auth = (self.__config['server']['User'], self.__config['server']['Password'])
            data = common.makeApiRequest(url, auth, False)

            total = data['total']
            start += data['maxResults']

            (issues, accounts) = self.__extractIssueData(project, project_name, data)

            update_date = None
            try:
                update_date = datetime.datetime.strptime(issues[-1:][0]['updated_date'][:23], '%Y-%m-%dT%H:%M:%S.%f')
            except:
                update_date = datetime.datetime.now()

            conn.addUsers(accounts)
            conn.addIssues(issues)

            for issue in issues:
                self._getChangelogDataFromApi(issue['issue_key'], conn)

            if update_date < start_date:
                break

        conn.closeConnection()

        return issues

    def __addAccount(self, account, accounts):
        if account is None:
            return (None, accounts)

        tmp_account = {
            'slug': account['key'],
            'name': account['name'],
            'emailAddress': account['emailAddress'],
            'displayName': account['displayName'],
            'type': 'NORMAL'
        }
        accounts[tmp_account['slug']] = tmp_account
        return (account, accounts)

    def __extractChangelogData(self, data):
        changelog = []
        for event in data['changelog']['histories']:
            field = event['items'][0]['field']
            if field not in ('description', 'Attachment', None):
                author = event.get('author')
                changelog.append({
                    'issue_key': data['key'],
                    'author': None if author is None else author['key'],
                    'timestamp': event['created'],
                    'field': field,
                    'value': event['items'][0]['toString']
                })
        return changelog

    def __extractIssueData(self, project, project_name, data):
        issues = []
        accounts = {}
        for issue in data['issues']:
            (assignee, accounts) = self.__addAccount(issue['fields']['assignee'], accounts)
            (creator, accounts) = self.__addAccount(issue['fields']['creator'], accounts)
            (reporter, accounts) = self.__addAccount(issue['fields']['reporter'], accounts)
            issues.append({
                'issue_key': issue['key'],
                'priority': issue['fields']['priority']['id'],
                'status': issue['fields']['status']['name'],
                'assignee': assignee['key'] if assignee is not None else None,
                'creator': creator['key'] if creator is not None else None,
                'reporter': reporter['key'] if reporter is not None else None,
                'type': issue['fields']['issuetype']['name'],
                'project': project,
                'project_name': project_name,
                'created_date': issue['fields']['created'],
                'updated_date': issue['fields']['updated'],
                'resolved_date': issue['fields']['resolutiondate'],
                'description': None,
                'summary': issue['fields']['summary']
            })
        return (issues, accounts)

if __name__ == '__main__':
    jira = Jira()
    jira.loadConfig('./config/jira.ini')
    jira.loadData(datetime.datetime.now() - datetime.timedelta(days=3))