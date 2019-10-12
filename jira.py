import common
import db
import datetime

class Jira:
    __config = None

    # statics
    _page_size = 100
    _loop_limit = 25

    def __init__(self):
        pass

    def loadConfig(self, config_file):
        self.__config = common.loadConfig(config_file)

    def loadData(self, start_date):
        for project in self.__config['projects']:
            self._getDataFromApi(project, self.__config['projects'][project], start_date) 

    def _getDataFromApi(self, project_name, project, start_date):
        earliest_date = datetime.datetime.now()
        counter = 0

        url = 'https://' + self.__config['server']['Domain'] + self.__config['server']['ApiPath'] + project_name + '?jql=status%20%3D%20Done%20AND%20project%20%3D%20'
        print(url)
        auth = (self.__config['server']['User'], self.__config['server']['Password'])
        data = common.makeApiRequest(url, auth, False)

        print(data)

if __name__ == '__main__':
    jira = Jira()
    jira.loadConfig('./config/jira.ini')
    jira.loadData(datetime.datetime.now() - datetime.timedelta(days=3))