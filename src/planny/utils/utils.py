import datetime as dt
from typing import Any, Dict
from enum import Enum, auto
import random
import string

# typing
JSON_Dict = Dict[str, Any]
CmdName = str
ListName = str
Datetime = dt.datetime

# expression Types
class Expr_Type(Enum):
    BEEMINDER = auto()
    EVENT = auto()
    EVENT_FINISH = auto()
    CHANGE_MINUTES = auto()
    BOARD_START = auto()
    BREAK = auto()
    EXIT  = auto()
    UNKNOWN = auto()


EVENT_FINISH_CODES = ['f']
DEFAULT_BOARD = 'misc'


def get_random_string() -> str:
    return "".join(random.choices(string.ascii_lowercase, k=10))
