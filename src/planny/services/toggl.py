import sys
if __name__=='__main__': sys.path.insert(0,r'C:\Users\godin\Python\planny\src')

import requests
from requests.auth import HTTPBasicAuth
from urllib.parse import urlencode
import json
import datetime
from datetime import timedelta
from typing import Optional, Any, List, Dict

import planny.utils.time as utils_time


""" Time entry dict looks like this:
{'id': 2159688252,
'wid': 642211,
'pid': 166536779,
'uid': 1095454,
'start': '2021-09-07T11:55:22+00:00',
'duration': -1631015722,
'description': 'current_te',
'duronly': False,
'at': '2021-09-07T11:55:25+00:00'}
"""


JSON_Dict = Dict[str, Any]
TimeEntryDict = Dict[str, Any]
EXERCISE = 'exercise'

def get_project_name(project_name):
    d = {
        'elliptical': EXERCISE, 'treadmill': EXERCISE, 'run': EXERCISE,'walk': EXERCISE,
    }
    return d.get(project_name, project_name)

class Toggl:
    def __init__(self, json_path):
        with open(json_path) as f:
            d = json.load(f)
        self.api_token = d['token']
        self.timezone = d['timezone']
        self.base_url = 'https://www.toggl.com/api/v8'
        self.wid = 642211
        self.proj_name_id_dict = self.project_name_id_dict()
    
    def project_name_id_dict(self) -> dict:
         # workspace id
        endpoint = f'workspaces/{self.wid}/projects'
        # params={'actual_hours':True}
        list_of_projects = self._call(endpoint=endpoint) # List
        name_id_dict = {}
        for proj in list_of_projects:
            name_id_dict[ proj['id'] ] = proj['name']
            name_id_dict[ proj['name'] ] = proj['id']
        return name_id_dict
   
    def get_running_time_entry(self) -> TimeEntryDict:
        """ return time entry dict {'id', 'wid','uid', 'start','duration','description'}"""
        endpoint = 'time_entries/current'
        return self._call(endpoint=endpoint)['data'] # time entry
         
    def add_time_entry(self, description: str, proj_name: str,
                      start_datetime: datetime.datetime, end_datetime: datetime.datetime):
        proj_name = get_project_name(proj_name)
        
        endpoint = 'time_entries'
        duration = int((end_datetime - start_datetime).total_seconds())
        proj_id = self.proj_name_id_dict.get(proj_name, self.proj_name_id_dict['misc'])
        data = {'time_entry':{'pid':proj_id, 'start':start_datetime.isoformat(), 'end':end_datetime.isoformat(),
                'duration':duration, 'created_with':'planny', 'description':description}}
        res = self._call(endpoint, data=data, method="POST")
        return res
    
    
    def _call(self, endpoint: str, data = None, params={},method: str = 'GET'):
        url = f'{self.base_url}/{endpoint}'
        if params:
            url += '?{}'.format(urlencode(params))
        data = json.dumps(data) if data else None
        headers = {'content-type': 'application/json'}
        
        if method== 'GET':
            result = requests.get(url, headers=headers, auth=HTTPBasicAuth(self.api_token, 'api_token'))
        elif method == 'POST':
            result = requests.post(url, headers=headers, data=data, auth=HTTPBasicAuth(self.api_token, 'api_token'))
        elif method == 'PUT':
            result = requests.put(url, headers=headers, data=data, auth=HTTPBasicAuth(self.api_token, 'api_token'))
        elif method =='DELETE':
            result = requests.delete(url, headers=headers, data=data, auth=HTTPBasicAuth(self.api_token, 'api_token'))
        else: # method 
            raise Exception(f'_call(), unknown method: {method}')
        
        if not result.status_code == requests.codes.ok:
            raise Exception(f'Toggl API failed with code {result.status_code}: {result.text}, {method} {url}, {data}')

        return result.json()

def main():
    json_path = r'C:\Users\godin\Python\planny\src\credentials\toggl.json'
    end = utils_time.get_current_local()
    start = end + timedelta(minutes=-5)
    t = Toggl(json_path)
    res = t.add_time_entry("you know", "bathroom", start, end)
    print(res)
    a=3

if __name__=='__main__':
    main()
