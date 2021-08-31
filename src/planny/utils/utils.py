from typing import Any, Dict
from enum import Enum, auto
# typing
EXPR_TYPE = str
JSON_Dict = Dict[str, Any]

# expression Types

class Expr_Type(Enum):
    EVENT_FINISH = auto()
    BEEMINDER = auto()
    TASK = auto()
    EVENT = auto()
    MORE_MINUTES = auto()
    UNKNOWN = auto()
    EXIT  = auto()
    PLAYLIST_DELETE = auto()
    PLAYLIST_START = auto()
    NEXT_TASK = auto()


EVENT_FINISH_CODES = ['f']



