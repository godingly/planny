from planny.tasks import Tasker
from planny.parser import Parser
from planny.beeminder import Beeminder
from planny.utils import *


class Model:
    def __init__(self) -> None:
        self.parser = Parser()
        self.tasker = Tasker()
        self.bee = Beeminder()
    
    def evaluate(self, expression):
        # parse
        type_, data = self.parser.parse(expression)
        print(f"Model::evaluate() type: {type_}, data={data}")
        # execute
        if type_ == TASK_COMPLETION_TYPE:
            self.complete_current_task()
        elif type_ == BEEMINDER_TYPE:
            self.add_beeminder(data)
    
    
    def complete_current_task(self):
        # TODO
        pass
    
    def add_beeminder(self, slug_value_dict):
        for slug,value in slug_value_dict.items():
            self.bee.add_datapoint(slug=slug, value=value)
    


