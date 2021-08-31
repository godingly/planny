import sys
if __name__=='__main__':
    sys.path.insert(0,r'C:\Users\godin\Python\planny\src')

import re
from typing import Tuple, Optional, Match
from collections import defaultdict
import datetime
from datetime import timedelta

from planny.utils.utils import *
import planny.utils.time as utils_time


# REGEX PATTERNS 
NUM_PAT = r'(?P<number>-?\d+(?:.\d+)?)' # 20.3, -13
WORD_PAT = r'\s*\w+\s+' # one word
WORDS_PAT = rf'(?P<words>{WORD_PAT}(?:{WORD_PAT})*)' # multiple words

DURATION_MIN_PAT = r'(?P<minutes>\d\d*)m(?:inutes|inute|in)?\b' # 20m, 20minutes
HOUR_PAT = r'\d\d*(?::\d\d)?' #10, 10:30
HOURS_PAT = rf'(?P<start_time>{HOUR_PAT})-(?P<end_time>{HOUR_PAT})' #10-12:30
DAY_SHORT_FORM = r'\b(sun|mon|tue|wed|thu|fri|sat)\b'
DAY_LONG_FORM = r'\b(sunday|monday|tueday|wednesday|thursday|friday|saturday)\b'
# DAY_PAT = r'\b(?P<day>(mon|tues|wed(nes)?|thur(s)?|fri|sat(ur)?|sun)(day)?)\b'

PLAYLIST_PAT = r"-p\s+(?P<playlist>\w+)"

# PREFIX
BEE_PREFIX = 'bee '
TASK_PREFIX = 'task '
EVENT_PREFIX = 'event '
PLAYLIST_DELETE_PREFIX = 'playlist delete'
PLAYLIST_START_PREFIX = 'playlist start'
NEXT_TASK_CODES = ['n', 'next']

def parse(s: str) -> Tuple[Expr_Type, JSON_Dict]:
    s = s.lower()
    
    if s in EVENT_FINISH_CODES:
        return Expr_Type.EVENT_FINISH, {}

    if s in NEXT_TASK_CODES:
        return Expr_Type.NEXT_TASK, {}
    
    elif s == 'exit':
        type_, data = Expr_Type.EXIT, {}

    elif s.startswith(BEE_PREFIX):
        type_, data = parse_beeminder(s[len(BEE_PREFIX):])
    
    elif s.startswith(EVENT_PREFIX):
        type_, data = parse_event(s[len(EVENT_PREFIX):])
    
    elif s.startswith('+'):
        type_, data = parse_more_minutes(s[1:])
    
    elif s.startswith(TASK_PREFIX):
        type_, data = parse_task(s[len(TASK_PREFIX):])
    
    elif s.startswith(PLAYLIST_DELETE_PREFIX):
        playlist = s[len(PLAYLIST_DELETE_PREFIX):].strip()
        type_, data = Expr_Type.PLAYLIST_DELETE, {'playlist':playlist}

    elif s.startswith(PLAYLIST_START_PREFIX):
        playlist = s[len(PLAYLIST_START_PREFIX):].strip()
        type_, data = Expr_Type.PLAYLIST_DELETE, {'playlist':playlist}
    
    else:
        type_, data = parse_task(s)
    
    if type_ == Expr_Type.UNKNOWN:
        type_, data = parse_task(s)
    
    return type_, data

def search_and_consume(pat: str, s:str) -> Tuple[Optional[Match], str]:
    """ takes a pattern and string, and if there's a match then consumes the pattern from the string"""
    match = re.search(pat, s)
    if not match: return match, s
    sub_s = s[:match.start()]+s[match.end():]
    return match, sub_s

# def parse_playlist() -> Tuple[str, JSON_Dict]:
#     pass

def parse_task(s: str) -> Tuple[Expr_Type, JSON_Dict]:
    """ task summary -p playlist 20m"""
    d = dict()
    match, snew = search_and_consume(DURATION_MIN_PAT, s)
    if match: # 20m, duration
        d['duration'] = match.group("minutes")
    else: 
        # TODO perhaps insert default time
        return Expr_Type.UNKNOWN, d
    
    match, snew = search_and_consume(PLAYLIST_PAT,snew)
    if match: # -p playlist
        d['playlist'] = match.group("playlist")
    else: return Expr_Type.UNKNOWN, d
    d['summary'] = snew.strip()
    return Expr_Type.TASK, d


def parse_time(s: str) -> Tuple[str, JSON_Dict]:
    """ look for 20m or 12:00-13, returns consumed string"""
    d = defaultdict(dict)
    duration_match, snew = search_and_consume(DURATION_MIN_PAT, s)
    if duration_match: # 20m, duration
        d['duration'] = duration_match.group("minutes")
    else: # maybe 12:00-13
        hours_match, snew = search_and_consume(HOURS_PAT, s)
        if not hours_match: # no 12:00-13
            return s, {}
        start_time = hours_match.group("start_time")
        d['start']['time'] = utils_time.get_hour_minute(start_time) #08:25
        end_time = hours_match.group("end_time")
        d['end']['time'] = utils_time.get_hour_minute(end_time) #08:25
    return snew, d

def parse_datetime(s: str) -> Tuple[str, JSON_Dict]:
    snew, d = parse_time(s)
    if not d:
        # TODO perhaps all day event, i.e. s = 'event summary Wednesday'
        return s, {}
    # parse date
    # if there's no date, then assume date=today
    # TODO look for date, parse_date
    if 'duration' in d:
        duration = int(d['duration']) 
        start_datetime = utils_time.get_current_local(round=False) # type: datetime.datetime
        end_datetime = start_datetime + timedelta(minutes=duration) # type: datetime.datetime
        if duration >= 5:
            end_datetime = utils_time.round_datetime(end_datetime)
    elif 'start' in d and 'time' in d['start']: # 12:30-13:00
        start_time = d['start']['time'] # type: str # 08:25, 13:30  
        start_datetime = utils_time.get_today_with_hour(start_time) # type: datetime.datetime
        end_time = d['end']['time'] # could be 13:00, or 06:00
        end_datetime = utils_time.get_today_with_hour(end_time) # type: datetime.datetime
        if end_datetime < start_datetime:
            end_datetime += timedelta(days=1)
    else:
        raise Exception('addEvent() invalid input')
    # TODO all day event
    d['start']['datetime'] = start_datetime
    d['end']['datetime'] = end_datetime
    
    return snew, d


def parse_event(s: str) -> Tuple[Expr_Type, JSON_Dict]:
    "summary (20m) or [12:00-13] [Wed|Wednesday|1/7|1/7/23]"
    # consume 20m / (12:00-13)
    snew, d = parse_datetime(s)
    if not d:
        return Expr_Type.UNKNOWN, {}
    d['summary'] = snew.strip()
    return Expr_Type.EVENT, d 


def parse_more_minutes(s: str) -> Tuple[Expr_Type, JSON_Dict]:
    d = {}
    match = re.match(DURATION_MIN_PAT, s)
    if not match:
        return Expr_Type.UNKNOWN, {}
    d['minutes']= match.group("minutes")
    return Expr_Type.MORE_MINUTES, d


def parse_beeminder(s: str) -> Tuple[Expr_Type, JSON_Dict]:
    print("entering parse_beeminder()")
    slug_val_dict = {}
    slug_val_pat =  rf'\b(\w+)\s+{NUM_PAT}'
    # extract slug and valuge
    for match in re.finditer(slug_val_pat, s):
        slug = match.group(1)
        value = match.group(2)
        slug_val_dict[slug]=value
    if slug_val_dict:
        print(slug_val_dict)
        return Expr_Type.BEEMINDER, slug_val_dict
    else:
        return Expr_Type.UNKNOWN, {}


if __name__=='__main__':
    a=2
    a=3