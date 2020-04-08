import datetime
import glob
import os

def now():
    time = datetime.datetime.now()
    return time.strftime("%Y-%m-%d %H:%M:%S - ")

def clean(directory):
    toRemoveList = glob.glob( directory + 'tmp*')
    for fileToRemove in toRemoveList:
        os.remove(fileToRemove)