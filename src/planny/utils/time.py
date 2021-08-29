""" utils for handling timezones. The trick is to always use Aware datetime,
in utc. you create one by datetime.ta
"""
from PyQt5.QtCore import QDateTime, QTime

import datetime
from datetime import timedelta, tzinfo, timezone
import tzlocal
import pytz
import arrow
import dateutil
from dateutil.parser import parse as dateutil_parse

from typing import Optional

date_formats = ['D.M', 'DD.M', 'D.MM', 'DD.MM',
    'D/M', 'DD/M', 'D/MM', 'DD/MM',
    'D.M.YY', 'DD.M.YY', 'D.MM.YY', 'DD.MM.YY', 'D.M.YYYY', 'DD.M.YYYY', 'D.MM.YYYY', 'DD.MM.YYYY',
    'D/M/YY', 'DD/M/YY', 'D/MM/YY', 'DD/MM/YY', 'D/M/YYYY', 'DD/M/YYYY', 'D/MM/YYYY', 'DD/MM/YYYY',]

# typing
datetime_t = datetime.datetime
datetime_d = datetime.date


def get_local_timezone_str() -> str:
    """America/Los_Angeles"""
    return str(tzlocal.get_localzone())

def get_local_timezone() -> tzinfo:
    """ if tz = get_local_timezone(), can be used with dt.astimezone(tz) """
    local_timezone_str = get_local_timezone_str()
    return pytz.timezone(local_timezone_str)

def round_datetime(dt: datetime_t) -> datetime_t:
    dt = dt.replace(second=0, microsecond=0)
    min_ = dt.minute
    delta_min = 5-(min_ % 5)
    round_date_time = dt + timedelta(minutes=delta_min)
    return round_date_time

def utc_to_local(utc_dt: datetime_t) -> datetime_t:
    """ datetime must be aware"""
    local_tz = get_local_timezone()
    return utc_dt.astimezone(local_tz)

def local_to_utc(local_dt: datetime_t) -> datetime_t:
    return local_dt.astimezone(timezone.utc)

def get_current_utc(round: bool=False) -> datetime_t:
    """ returns current aware utc datetime """
    current_utc_aware_dt = datetime.datetime.now(timezone.utc) 
    current_utc_aware_dt.replace(second=0, microsecond=0)
    if round:
        return round_datetime(current_utc_aware_dt)
    else:
        return current_utc_aware_dt

def get_current_local(round: bool=False) -> datetime_t:
    """ returns current aware local datetime"""
    current_utc_aware_dt = get_current_utc(round=round)
    return utc_to_local(current_utc_aware_dt)

def datetime_to_iso(dt: datetime_t) -> str:
    return dt.isoformat()

def get_today_with_hour(hour : str) -> datetime_t:
    """ hour = 12:00, returns datetime(2021,8,26,12,0)"""
    return dateutil_parse(hour)
    
def timedelta_to_datetime_time(td: timedelta) -> datetime.time:
    """ receives timedelta and returns timedate.time object"""
    time = (datetime.datetime.min + td).time()
    return time

# convert date string to datetime
def extract_date(s: str) -> Optional[datetime_d]:
    """ 29.5, 01.01, 1.1, 29.5.23, 29.05.2023. Or with '/' instead of '.' """
    today = datetime.datetime.today()
    try:
        date = arrow.get(s, date_formats).date()
        if date.year == 1:
            date = datetime.date(today.year, date.month, date.day)
        return date
    except arrow.parser.ParserError:
        return None

def str_to_day_of_week(s: str) -> int:
    """ could be Mon/mon/Monday/monday, returns 0"""
    return arrow.get(s, ['ddd', 'dddd']).weekday()

def datetime_time_to_hour_minutes(time: datetime.time) -> str:
    """ receives time(hour=20, minute=13), returns 20:13, and for 8:13AM returns 8:13"""
    return time.strftime('%#H:%M')

def datetimes_to_hours_minutes(time1: datetime_t, time2: datetime_t) -> str:
    """ receives two datetimes, returns 8:05-20:20"""
    hour_minute_str1 = time1.strftime('%#H:%M')
    hour_minute_str2 = time2.strftime('%#H:%M')
    return f'{hour_minute_str1}-{hour_minute_str2}'


def datetime_time_to_str(time: datetime.time) -> str:
    if time.hour != 0:
        return time.strftime('%#H:%M:%S') # 1:00:04
    else: # hour = 0
        return time.strftime('%#M:%S') # 7:03, 0:03

# PyQt5 QDateTime
def QDateTime_to_datetime(qDateTime: QDateTime):
    return qDateTime.toPyDateTime()    

def datetime_to_QDateTime(dt : datetime_t):
    return QDateTime(dt)

def QTime_to_str(qtime: QTime) -> str:
    if qtime.hour() != 0:
        return qtime.toString('H:mm:ss')
    else:
        return qtime.toString('m:ss')

# 01.07, 1/7, 01/07, 01/7, 1/07
