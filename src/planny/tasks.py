from datetime import datetime

class Task:
    def __init__(self, name: str, tag: str = '') -> None:
        self.name=name
        self.tag=tag
    
    def start(self) -> None:
        self.starttime = datetime.now()
    
    def end(self) -> None:
        self.endtime = datetime.now()
        self.length_seconds = (self.endtime - self.starttime).seconds 

class Tasker:
    def __init__(self) -> None:
        self.currentTask = None
    
    def new(self, name, tag = '') -> Task:
        # complete previous task if one exists
        if self.current is not None:
            # TODO
            pass
        # create new task
        new_task = Task(name=name, tag=tag)
        # set current task to new task
        self.current = new_task
        return new_task
    
    def fail_current(self) -> None:
        pass
        
    def complete_current(self) -> None:
        # complete current task
        # if in list, move to next task in list
        # else, set current to None
        pass
