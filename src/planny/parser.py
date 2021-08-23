import re
from typing import Tuple
from planny.utils import *
from planny.beeminder import BEEMINDER_PATTERNS

NUM_PAT = r'(-?\d+(?:.\d+)?)'
TASK_COMPLETION_WORDS = ['finish', 'finished', 'c']


class Parser:
    def __init__(self) -> None:
        pass
    
    def parse(self, string: str) -> Tuple[str, JSON_Dict]:
        string = string.lower()
        if string in TASK_COMPLETION_WORDS:
            return TASK_COMPLETION_TYPE, {}
        elif string.startswith('bee '):
            type_, data = self.parse_beeminder(string[4:])
        elif string.startswith('do '):
            type_, data = self.parse_task(string)
        else:
            type_, data = self.parse_beeminder(string)
        return type_, data


    def parse_task(self, s: str) -> Tuple[str, dict[str, str]]:
        # TODO
        return UNKNOWN_TYPE, {}


    def parse_beeminder(self, s: str) -> Tuple[str, JSON_Dict]:
        print("entering parse_beeminder()")
        slug_val_dict = {}
        for slug_pat in BEEMINDER_PATTERNS:
            pattern = re.compile(rf'{slug_pat} {NUM_PAT}', re.IGNORECASE)
            match = re.search(pattern, s)
            if match:
                value = match.group(1)
                slug_val_dict[slug_pat]=value
        if slug_val_dict:
            print(slug_val_dict)
            return BEEMINDER_TYPE, slug_val_dict
        else:
            return UNKNOWN_TYPE, {}
