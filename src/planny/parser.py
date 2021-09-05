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
HOURS_PAT = rf'(?P<start_time>{HOUR_PAT})-(?P<end_time>{HOUR_PAT})' # 10-12:30
DAY_SHORT_FORM = r'\b(sun|mon|tue|wed|thu|fri|sat)\b'
DAY_LONG_FORM = r'\b(sunday|monday|tueday|wednesday|thursday|friday|saturday)\b'
# DAY_PAT = r'\b(?P<day>(mon|tues|wed(nes)?|thur(s)?|fri|sat(ur)?|sun)(day)?)\b'

BOARD_PAT = r"-b\s+(?P<board>\w+)"

# PREFIX
BEE_PREFIX = 'bee '
TASK_PREFIX = 'task '
EVENT_PREFIX = 'event '
BREAK_PREFIX = 'break'
BOARD_START_PREFIX = 'start '

def parse(s: str) -> Tuple[Expr_Type, JSON_Dict]:
    s = s.lower()
    
    if s in EVENT_FINISH_CODES:
        return Expr_Type.EVENT_FINISH, {}
    
    elif s == 'exit':
        type_, data = Expr_Type.EXIT, {}

    elif s.startswith(BREAK_PREFIX):
        type_, data = parse_break(s)

    elif s.startswith(BEE_PREFIX):
        type_, data = parse_beeminder(s[len(BEE_PREFIX):])
    
    elif s.startswith(EVENT_PREFIX):
        type_, data = parse_event(s[len(EVENT_PREFIX):])
    
    elif s[0] in ['+', '-']:
        type_, data = parse_change_minutes(s)

    elif s.startswith(BOARD_START_PREFIX):
        board = s[len(BOARD_START_PREFIX):].strip()
        type_, data = Expr_Type.BOARD_START, {'board':board}
    
    else:
        type_, data = Expr_Type.UNKNOWN, {}
    
    return type_, data

def search_and_consume(pat: str, s:str) -> Tuple[Optional[Match], str]:
    """ takes a pattern and string, and if there's a match then consumes the pattern from the string"""
    match = re.search(pat, s)
    if not match: return match, s
    sub_s = s[:match.start()]+s[match.end():]
    return match, sub_s

def parse_break(s: str) -> Tuple[Expr_Type, JSON_Dict]:
    duration_match, _ = search_and_consume(DURATION_MIN_PAT, s)
    d = defaultdict(dict)
    duration = int(duration_match.group("minutes")) if duration_match else 5
    d['name'] = 'break' # type: ignore
    d['start']['datetime'] = utils_time.get_current_local(round=False) 
    d['end']['datetime'] = d['start']['datetime'] + timedelta(minutes=duration)
    return Expr_Type.BREAK, d

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
        # TODO perhaps all day event, i.e. s = 'event name Wednesday'
        return s, {}
    # parse date
    # if there's no date, then assume date=today
    # TODO add parse_date
    if 'duration' in d:
        duration = int(d['duration']) 
        start_datetime = utils_time.get_current_local(round=False) # type: Datetime
        end_datetime = start_datetime + timedelta(minutes=duration) # type: Datetime
        if duration > 5:
            end_datetime = utils_time.round_datetime(end_datetime)
    elif 'start' in d and 'time' in d['start']: # 12:30-13:00
        start_time = d['start']['time'] # type: str # 08:25, 13:30  
        start_datetime = utils_time.get_today_with_hour(start_time) # type: Datetime
        end_time = d['end']['time'] # could be 13:00, or 06:00
        end_datetime = utils_time.get_today_with_hour(end_time) # type: Datetime
        if end_datetime < start_datetime:
            end_datetime += timedelta(days=1)
    else:
        return s, {}
    # TODO all day event
    d['start']['datetime'] = start_datetime
    d['end']['datetime'] = end_datetime
    
    return snew, d

def parse_event(s: str) -> Tuple[Expr_Type, JSON_Dict]:
    "name [-b board] [20m] or [12:00-13] [Wed|Wednesday|1/7|1/7/23]"
    # consume 20m / (12:00-13)
    snew, d = parse_datetime(s)
    if not d:
        return Expr_Type.UNKNOWN, {}

    board_match, snew = search_and_consume(BOARD_PAT, snew)
    if board_match:
        d['board'] = board_match.group('board')
    d['name'] = snew.strip()
    return Expr_Type.EVENT, d 

def parse_change_minutes(s: str) -> Tuple[Expr_Type, JSON_Dict]:
    d = {}
    multiplier = 1 if s[0] == '+' else -1
    s = s[1:]
    match = re.match(DURATION_MIN_PAT, s)
    if not match:
        return Expr_Type.UNKNOWN, {}
    d['minutes']= multiplier * int(match.group("minutes"))
    return Expr_Type.CHANGE_MINUTES, d

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
