import datetime

def now():
    time = datetime.datetime.now()
    return time.strftime("%Y-%m-%d %H:%M:%S - ")