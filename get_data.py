import bitbucket
import jira
import datetime
import sys

DEFAULT_START = datetime.datetime.now() - datetime.timedelta(days=3)
DEFAULT_END = datetime.datetime.now()
DEFAULT_BB_INI = './config/bitbucket.ini'
DEFAULT_JIRA_INI = './config/jira.ini'

def ParseArgs(args):
    output = {}
    pairwise = zip(*[iter(args[1:])] * 2)
    for (key, val) in pairwise:
        if key[:2] == '--':
            output[key[2:].lower()] = val.lower()
        else:
            raise Exception('invalid parameter', key)
    return output

if __name__ == '__main__':
    start = DEFAULT_START
    end = DEFAULT_END
    bb_ini = DEFAULT_BB_INI
    jira_ini = DEFAULT_JIRA_INI

    args = ParseArgs(sys.argv)
    for key in args.keys():
        if key == 'start':
            start = datetime.datetime.fromisoformat(args[key])
        elif key == 'end':
            end = datetime.datetime.fromisoformat(args[key])
        elif key == 'bbini':
            bb_ini = args[key]
        elif key == 'jiraini':
            jira_ini = args[key]

    bb = bitbucket.Bitbucket()
    bb.loadConfig(bb_ini)
    bb.loadData(start, end)

    jira = jira.Jira()
    jira.loadConfig(jira_ini)
    jira.loadData(start, end)
