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

from typing import List, Optional

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
    if dt.minute % 5 == 0:
        return dt
    delta_min = 5-(dt.minute % 5)
    round_date_time = dt + timedelta(minutes=delta_min)
    return round_date_time

def utc_to_local(utc_dt: datetime_t) -> datetime_t:
    """ datetime must be aware"""
    local_tz = get_local_timezone()
    return utc_dt.astimezone(local_tz)

def local_to_utc(local_dt: datetime_t) -> datetime_t:
    return local_dt.astimezone(timezone.utc)

def get_current_utc(round: bool=False, with_seconds: bool=False) -> datetime_t:
    """ returns current aware utc datetime """
    current_utc_aware_dt = datetime.datetime.now(timezone.utc) 
    if with_seconds:
        current_utc_aware_dt = current_utc_aware_dt.replace(microsecond=0)
    else:
        current_utc_aware_dt = current_utc_aware_dt.replace(second=0, microsecond=0)
    if round:
        return round_datetime(current_utc_aware_dt)
    else:
        return current_utc_aware_dt

def get_current_local(round: bool=False, with_seconds: bool=False) -> datetime_t:
    """ returns current aware local datetime"""
    current_utc_aware_dt = get_current_utc(round, with_seconds)
    return utc_to_local(current_utc_aware_dt)

def datetime_to_iso(dt: datetime_t) -> str:
    return dt.isoformat()

def get_today_with_hour(hour : str) -> datetime_t:
    """ hour = 13:00, 6:20, or 06:20, returns datetime(2021,8,26,13,0)"""
    return dateutil_parse(hour)
    
def timedelta_to_datetime_time(td: timedelta) -> datetime.time:
    """ receives timedelta and returns timedate.time object"""
    time = (datetime.datetime.min + td).time()
    return time

def timedelta_to_QTime(td: timedelta) -> QTime:
    datetime_time = timedelta_to_datetime_time(td)
    return QTime(datetime_time) # type: ignore

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

def from_iso_format_to_datetime(iso_str: str) -> datetime_t:
    return datetime.datetime.fromisoformat(iso_str)

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

def get_hour_minute(s: str) -> str:
    """ returns string 13:00, from input of 13:00 or 13,
         returns 08:25 for input 8:25, or 08:25"""
    l = s.split(':')
    if len(l) == 1:
        hour = l[0]
        minute = '00'
    elif len(l) == 2:
        hour = l[0]
        minute = l[1]
    else:
        raise Exception(f"get_hour_minute({s})")
    if len(hour) == 1: hour = '0'+hour
    assert len(hour)==2 and len(minute)==2
    return f'{hour}:{minute}'

def from_str_to_hour_minute(s: str) -> List[int]:
    """ gets 06:00 or 6:20, returns [6,0], or [6,20]"""
    return list(map(int, s.split(':')))

def add_times(*strings) -> str:
    """strings in format 01:15, 12. 
    returns 13:15"""
    total_hours, total_minutes = 0,0
    for s in strings:
        hours, minutes = from_str_to_hour_minute(s)
        total_hours += hours
        total_minutes += minutes
        q,total_minutes = divmod(total_minutes, 60)
        total_hours += q

    return f'{total_hours}:{total_minutes}'
    
def get_timedelta_from_now_to(dt: datetime_t) -> timedelta:
    """ dt msut be aware"""
    now = get_current_local(with_seconds=True)
    return (dt - now)

def get_now_plus_duration(duration_in_minutes: int, start_time: Optional[datetime_t] = None) -> datetime_t:
    """ return startime + duration. start_time defaults to local aware now. Returns local aware"""
    if not start_time:
        start_time = get_current_local()
    td = timedelta(minutes=duration_in_minutes)
    return start_time + td

if __name__=='__main__':
    now = get_current_local()
    a=3