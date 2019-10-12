import configparser
import requests

def loadConfig(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    return config

def makeApiRequest(url, auth, verify):
    response = requests.get(url, verify=verify, auth=auth)
    if response.status_code == 200:
        return response.json()
    else:
        print(url + ' -- ' + str(response.status_code))
        return {}