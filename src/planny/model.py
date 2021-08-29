import datetime
from planny.tasks import Tasker
import planny.parser as parser
from planny.services.gcal import GCal
from planny.services.beeminder import Beeminder
from planny.utils.utils import *
import planny.utils.time as utils_time

from datetime import timedelta


class Model:
    def __init__(self, args) -> None:
        self.args = args
        self.tasker = Tasker()
        self.bee = Beeminder(args.beeminder_json, args.debug)
        self.gcal = GCal(args.gcal_credentials_json, args.debug)
        self.secsTracked = 0 # in seconds
    
    def evaluate(self, expression):
        # parse
        type_, data = parser.parse(expression)
        print(f"Model::evaluate() type: {type_}, data={data}")
        # execute
        if type_ == Expr_Type.EVENT_FINISH:
            self.endCurEvent()
        elif type_ == Expr_Type.BEEMINDER:
            self.addBeeminder(data)
        elif type_ == Expr_Type.EVENT:
            self.addEvent(data)
        elif type_ == Expr_Type.MORE_MINUTES:
            return type_, data

        return type_, data

    def endCurEvent(self):
        pass
    
    def updateTimeTracked(self):
        if self.secsTracked > 0:
            self.bee.add_time_tracked(self.secsTracked)
            self.secsTracked = 0
    
    def addTimeTracked(self, timeInSeconds: int):
        self.secsTracked += timeInSeconds
        if self.secsTracked > 3600:
            self.updateTimeTracked()
            
    
    def addBeeminder(self, slug_value_dict):
        for slug,value in slug_value_dict.items():
            self.bee.add_datapoint(slug=slug, value=value)

    def addEvent(self, d: JSON_Dict):
        # parse time
        if 'duration' in d:
            duration = int(d['duration'])
            start_datetime = utils_time.get_current_local(round=True) # type: datetime.datetime
            end_datetime = start_datetime + timedelta(minutes=duration) # type: datetime.datetime
        elif 'start' in d and 'time' in d['start']: # 12:30-13:00
            start_time = d['start']['time']
            start_datetime = utils_time.get_today_with_hour(start_time) # type: datetime.datetime
            end_time = d['end']['time'] # could be 13:00, or 6
            end_datetime = utils_time.get_today_with_hour(end_time) # type: datetime.datetime
            if end_datetime < start_datetime:
                end_datetime += timedelta(days=1)
        else:
            raise Exception('addEvent() invalid input')
        # TODO all day event
        d['duration'] = end_datetime - start_datetime
        d['start']['datetime'] = start_datetime
        d['end']['datetime'] = end_datetime

        # create event
        self.gcal.add_event(summary=d['summary'],
                            start=start_datetime,
                            end=end_datetime,
                            all_day=False)
    


    def beeCharge(self, summary, amount=0):
        if amount:
            self.bee.charge(note=summary,amount=amount)
        else:
            self.bee.charge(note=summary)