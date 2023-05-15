# import pandas
import requests
import json
from requests.structures import CaseInsensitiveDict
from typing import Any, Dict, List, Optional
from requests.auth import HTTPBasicAuth
import datetime
from datetime import timedelta
from dateutil.rrule import rrule, DAILY

JSON_Dict = Dict[str, Any]
GERMAN = 'german'

class Gantt:
    def __init__(self, json_path):
        with open (json_path) as f:
            self.json_dict = json.load(f)
        self.json_path = json_path
        self.id_token = self.json_dict['id_token'] # only valid for 1 hour
        self.basic_btoa = self.json_dict['Basic_btoa']
        self.client_id = self.json_dict['client_id']
        self.client_secret = self.json_dict['client_secret']
        self.refresh_token = self.json_dict['refresh_token']
        self.refresh_tries = 0
        self.base_url = r'https://api.teamgantt.com/v1'
        self.project_name_id_dict = self.get_project_name_id_dict()

    
    def get_current_user(self):
        endpoint = 'current_user'
        user_dict = self._call(endpoint=endpoint) # {'id', 'companies':[{'id'}]}
        user_id = user_dict['id']
        comapny_id = user_dict['companies'][0]['id']
        return user_dict
    
    def get_project_name_id_dict(self):
        """ returns dict mapping between project id and name"""
        endpoint = 'projects/all'
        params={'status':'active'}
        proj_name_id_dict = {}
        resp = self._call(endpoint=endpoint, params=params) # {'proejcts':[]}
        projects_list_of_dicts = resp['projects'] # [{'id', 'name'}, {}, ...]
        for proj_dict in projects_list_of_dicts:
            proj_name_id_dict[proj_dict['id']] = proj_dict['name']
            proj_name_id_dict[proj_dict['name']] = proj_dict['id']
        return proj_name_id_dict

    def do_refresh_token(self):
        self.refresh_tries += 1
        url = "https://auth.teamgantt.com/oauth2/token"
        headers = CaseInsensitiveDict()
        headers["Authorization"] = self.basic_btoa
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        data = f"grant_type=refresh_token&refresh_token={self.refresh_token}"
        response = requests.post(url, headers=headers, data=data)
        resp_json = response.json()
        self.id_token = resp_json["id_token"]
        self.json_dict['id_token'] = resp_json["id_token"] # Ysg
        with open(self.json_path, 'w') as f:
            json.dump(self.json_dict, f)
        print('trying to refresh')

    # project
    def get_project_tasks(self, project_name="", project_id=''):
        assert project_name or project_id
        if not project_id: project_id = self.project_name_id_dict[project_name]
        endpoint = f'projects/{project_id}/children'
        resp = self._call(endpoint=endpoint) # list of task group dicts [{}, {}], one for each group
        # task_group_dict = {'children':[{},...{}] , 'id', 'name', 'project_id', 'project_name' } 
        # where child=task_dict = {'id', 'name':'2', 'parent_group_id', 'parent_group_name', 'days':1, 'dependencies':{},
        # 'start_date':2021-09-09, 'end_date':2021-09-09, 'estimated_hours', 'project_name', 'percent_complete'}
        # dependencies = {'parents': [ {'from_task':{'id', 'name':'1'}, 'id', 'project_id', 'to_task':{'id', 'name':2} } ],
        #                 'children':[ {'from_task':{'id', 'name':'2'}, 'to_task':{'id', 'name':'3'} }  ]}
        return resp
    
    # task
    def add_task(self, project_name,  name, start_date='', end_date='') -> JSON_Dict:
        """ returns task_dict, with task_dict= 
        {'id', 'name', 'parent_group_id', 'parent_group_name', 'days':0, 'dependencies':{},
        'start_date':2021-09-09, 'end_date':2021-09-09, 'estimated_hours', 'project_name', 'percent_complete'}
        """
        project_id = self.project_name_id_dict[project_name]
        endpoint = 'tasks'
        json_dict = {'type':'task', 'project_id':project_id, 'name':name}
        if start_date: json_dict['start_date'] = start_date
        if end_date: json_dict['end_date'] = end_date

        task_dict = self._call(endpoint, json_dict=json_dict, method='POST')
        return task_dict

    def add_list_of_tasks(self, project_name, task_names: List[str], task_dates: List[str]):
        assert len(task_names) == len(task_dates)
        parent_task = self.add_task(project_name, task_names[0], start_date=task_dates[0], end_date=task_dates[0])
        for name, date in zip(task_names[1:], task_dates[1:]):
            new_task = self.add_task(project_name, name, start_date=date, end_date=date)
            resp = self._call(f"tasks/{parent_task['id']}/dependencies", json_dict={'to_task': {'id':new_task['id']}}, method="POST")

            parent_task = new_task
            
    
    def prepend_task(self, project_name, name):
        list_of_tasks = self.get_project_tasks(project_name)[0]['children']
        parent_task = list_of_tasks[-1]
        parent_id = parent_task['id']
        
        # create new task
        new_task_dict = self.add_task(project_name, name, start_date=parent_task['start_date'], end_date=parent_task['end_date'])
        new_task_id = new_task_dict['id']
        
        
        # add dependency
        endpoint = f"tasks/{parent_task['id']}/dependencies"
        json_dict = {'to_task': {'id':new_task_id}}
        resp = self._call(endpoint, json_dict=json_dict, method="POST")
        return resp

    # general
    def _call(self, endpoint: str,
                    params = None,
                    data: Optional[JSON_Dict] = None,
                    json_dict = None,
                    method: str = 'GET'):
        if not data: data = {}
        
        url = f'{self.base_url}/{endpoint}'
        headers = {"Authorization": f"Bearer {self.id_token}"}
        if method== 'GET':
            response = requests.get(url, data=data, params=params, headers=headers)
        elif method == 'POST':
            response = requests.post(url, data=data, params=params,json=json_dict, headers=headers)
        elif method == 'PUT':
            response = requests.put(url, data=data, params=params, headers=headers)
        elif method =='DELETE':
            response = requests.delete(url, data=data, params=params, headers=headers)
        else: # method 
            raise Exception(f'_call(), unknown method: {method}')
        
        print('------------ REQUEST ----------------')
        print(response.request.url)
        print(response.request.headers)
        print(response.request.body)
        
        if response.status_code == 401 and self.refresh_tries < 2:
            self.do_refresh_token()
            self._call(endpoint=endpoint,params=params, data=data, method=method)
        self.refresh_tries=0
        if not response.status_code == requests.codes.ok:
            raise Exception(f'Gantt API failed with code {response.status_code}: {response.text}, {method} {url}')
        
        return response.json()

    

def main():
    # add assimil to german
    json_path = r'C:\Users\godin\Python\planny\src\credentials\gantt.json'
    g = Gantt(json_path)

    # assimil_csv = r'C:\Users\godin\Python\planny\src\credentials\assimil.csv'
    # df= pandas.read_csv(assimil_csv, header=0) # num, name, page
    days = 12
    RATE = 8
    task_names = [f"{i}/100 10m" for i in range(1,1+(RATE*days))]
    today = datetime.date.today()
    yester = today + timedelta(days=-1)
    end = yester + timedelta(days=days-1)
    dates = []
    for dt in rrule(DAILY, dtstart=yester, until=end):
        new_date = dt.strftime("%Y-%m-%d")
        dates += [new_date]*RATE
    # for i, date in enumerate(dates): 
    #     print(i+1, date)
    #     if ( (i+1)%8==0): print('')
    # exit()
    # response = g.add_task(GERMAN, "tst")
    # response = g.add_task(GERMAN, "tst", "2021-09-08", "2021-09-08")
    response = g.add_list_of_tasks(GERMAN, task_names, dates)
    # response = g.add_task(GERMAN, 'new task')
    print('------------ RESPONSE ----------------')
    print(response)
    a=3


if __name__=='__main__':
    main()
    