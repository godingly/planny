import sys
if __name__=='__main__':
    sys.path.insert(0,r'C:\Users\godin\Python\planny\src')

import re
from typing import Tuple, Optional, Match
from collections import defaultdict
from planny.utils.utils import *
from enum import Enum, auto

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

# PREFIX
BEE_PREFIX = 'bee '
TASK_PREFIX = 'task '
EVENT_PREFIX = 'event '

def parse(s: str) -> Tuple[Expr_Type, JSON_Dict]:
    s = s.lower()
    
    if s in EVENT_FINISH_CODES:
        return Expr_Type.EVENT_FINISH, {}
    
    elif s.startswith(BEE_PREFIX):
        type_, data = parse_beeminder(s[len(BEE_PREFIX):])
    
    elif s.startswith(EVENT_PREFIX):
        type_, data = parse_event(s[len(EVENT_PREFIX):])
    
    elif s.startswith('+'):
        type_, data = parse_more_minutes(s[1:])
    
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

# TODO search_consume wither finditer

def parse_more_minutes(s: str) -> Tuple[Expr_Type, JSON_Dict]:
    d = {}
    match = re.match(DURATION_MIN_PAT, s)
    if not match:
        return Expr_Type.UNKNOWN, {}
    d['minutes']= match.group("minutes")
    return Expr_Type.MORE_MINUTES, d

# def parse_playlist() -> Tuple[str, JSON_Dict]:
#     pass

# def parse_task(s: str) -> Tuple[Expr_Type.TASK, JSON_Dict]:
#     pass


# def parse_date(s: str) -> Tuple[str, JSON_Dict]:
#     """ possible date, could be Wed|wednesday|1.7|1.7.20"1.7.2020"""
#     # look for weekday
#     dict = {}
#     match, snew = search_and_consume(DAY_PAT, s)
#     if match:
#         dict['day']
#         # look for closest day of week
#     # else, look for date
    

def get_hour_minute(s: str) -> str:
    """ returns string 12:00, from input of 12:00 or 12"""
    l = s.split(':')
    if len(l) == 1:
        hour = l[0]
        minute = '00'
    elif len(l) == 2:
        hour = l[0]
        minute = l[1]
    else:
        raise Exception(f"get_hour_minute({s})")
    assert len(hour)==2 and len(minute)==2
    return f'{hour}:{minute}'

def parse_time(s: str) -> Tuple[str, JSON_Dict]:
    """ look for 20m or 12:00-13, returns consumed string"""
    d = defaultdict(dict)
    match, snew = search_and_consume(DURATION_MIN_PAT, s)
    if match: # 20m, duration
        d['duration'] = match.group("minutes")
    else: # 12:00-13
        match, snew = search_and_consume(HOURS_PAT, s)
        if not match: # no time
            return s, {}
        start_time = match.group("start_time")
        d['start']['time'] = get_hour_minute(start_time)
        end_time = match.group("end_time")
        d['end']['time'] = get_hour_minute(end_time)
    return snew, d

def parse_datetime(s: str) -> Tuple[str, JSON_Dict]:
    snew, d = parse_time(s)
    if not d:
        return s, {}
    # parse date

    return snew, d
    


def parse_event(s: str) -> Tuple[Expr_Type, JSON_Dict]:
    "summary (20m) or [12:00-13] [Wed|Wednesday|1/7|1/7/23]"
    # consume 20m / (12:00-13)
    snew, d = parse_datetime(s)
    if not d:
        return Expr_Type.UNKNOWN, {}
    d['summary'] = snew.strip()
    return Expr_Type.EVENT, d 


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
    s1 = '12:00-13 word1 word2'
    m, snew = parse_time(s1)
    a=3