import datetime
import subprocess, os, sys

def timestampPrint(message):
    print('[{}] {} '.format(datetime.datetime.now(), message))

def getNumLines(filename):
    res = subprocess.check_output(["sudo", "wc", "-l", filename])
    num_lines = int(res.split(' ')[0])
    return num_lines