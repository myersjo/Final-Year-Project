import datetime

def timestampPrint(message):
    print('[{}] {} '.format(datetime.datetime.now(), message))