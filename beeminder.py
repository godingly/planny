import requests
import sys,os
import json
from datetime import datetime


class Beeminder:
    def __init__(self):
        self._base_url="https://www.beeminder.com/api/v1"
        self._user="thefinaldanse"
        self._token="zyvC_K-zsNR-cKJYiixR"

    def get_goal(self,slug):
        # https://www.beeminder.com/api/v1/users/alice/goals/weight.json?auth_token=abc123&datapoints=true
        endpoint = f'users/{self._user}/goals/{slug}.json'
        data = {'datapoints':'true'}
        result = self._call(endpoint, data)
        return result

    def get_goals(self):
        endpoint = f'users/{self._user}/goals.json'
        list_of_goals = self._call(endpoint) # list of goals [{}, {}, .. , {}]
        # goal {'slug', 'last_datapoint}
        return list_of_goals
    
    def get_datapoints(self, slug, count=None, sort=None):
        # https://www.beeminder.com/api/v1/users/alice/goals/weight/datapoints.json?auth_token=abc123
        endpoint = f'users/{self._user}/goals/{slug}/datapoints.json'
        data = {}
        if count: data['count']=count
        if sort: data['sort']=sort
        datapoints = self._call(endpoint, data) # list of datapoints
        # {'timestamp', 'value', 'comment', 'daystamp'}
        return datapoints

    def add_datapoint(self, slug, value, comment=None):
        endpoint = f'users/{self._user}/goals/{slug}/datapoints.json'
        data = {'value':value}
        if comment: data['comment'] = comment
        result = self._call(endpoint, data, method='POST')
        return result

    
    def get_user(self):
        # https://www.beeminder.com/api/v1/users/alice.json?auth_token=abc123
        endpoint = f'users/{self._user}.json'
        user = self._call(endpoint)
        goals_slugs = user['goals'] # list of slugs ['', '', ]
        updated_at = user['updated_at'] # timestamp
        date = datetime.fromtimestamp(updated_at) #datetime object
        return user
    
    def charge(self, amount, note, dryrun='true'):
        endpoint = 'charges.json'
        data = {'amount':amount, note:'note', 'dryrun':dryrun}
        charge = self._call(endpoint, data, method='POST')
        return charge
    
    def _call(self, endpoint, data=None, method='GET'):
        if not data: data = {}
        data['auth_token'] = self._token
        url = f'{self._base_url}/{endpoint}/'
        result = None
        if method== 'GET':
            result = requests.get(url, data)
        elif method == 'POST':
            result = requests.post(url, data)
        elif method == 'PUT':
            result = requests.put(url, data)
        
        if not result.status_code == requests.codes.ok:
            raise Exception(f'Beeminder API failed with code {result.status_code}: {result.text}')

        return None if result is None else result.json()

if __name__ == '__main__':
    bee=Beeminder()
    a=3
    