from datetime import datetime
from dataclasses import dataclass
from typing import Optional
TASK_DEFAULT_DURATION = 20

@dataclass
class Task:
    name: str
    description: str = ''
    duration: int = TASK_DEFAULT_DURATION
    project: str = "Misc"
    list: str = "misc"
    start_datetime : datetime = None # type: ignore
    end_datetime : datetime = None # type: ignore
    next_event_name : str = ''
    num_cards_in_list: int = 0
    num_total_cards: int = 0
    num_completed_cards: int = 0
    origin: str = ""
    trello_id : str = ""
    gantt_id : int = 0