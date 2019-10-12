import bitbucket
import datetime

if __name__ == '__main__':
    bb = bitbucket.Bitbucket()
    bb.loadConfig('./config/bitbucket.ini')
    bb.loadData(datetime.datetime(2019, 5, 1))
