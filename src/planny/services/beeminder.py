""" beeminder integration"""
from typing import Optional
import requests
from datetime import datetime
import json
from typing import Any, Dict
JSON_Dict = Dict[str, Any]


# slugs
MEDITATION='meditation'
SITUPS = 'situps'
PUSHUPS = 'pushups'
STRETCH = 'stretch'
RUN = 'run'
TRACKED = 'tracked'

DEFAULT_CHARGE_AMOUNT = 5 # default amount of dollars to charge

class Beeminder:
    def __init__(self, json_path: str, debug: bool) -> None:
        self._base_url="https://www.beeminder.com/api/v1"
        # read user and authentication from json
        with open(json_path) as f:
            d = json.load(f)
        self._username=d['username']
        self._token=d['auth_token']
        self.debug = debug
    
    @staticmethod
    def name_to_slug(name: str) -> str:
        d = {
            'pushup':PUSHUPS, 
            'situp':SITUPS,
            'drink':'water',
            'stretched':STRETCH, 'stretches':STRETCH, 'stretching':STRETCH,
            'running':RUN, 'ran':RUN,
            'meditated':MEDITATION, 'meditate':MEDITATION
            }
        return d.get(name, name)

    
    def get_goal(self,slug: str) -> JSON_Dict:
        endpoint = f'users/{self._username}/goals/{slug}.json'
        data = {'datapoints':'true'}
        result = self._call(endpoint, data)
        return result

    def get_goals(self):
        endpoint = f'users/{self._username}/goals.json'
        list_of_goals = self._call(endpoint) # list of goals [{}, {}, .. , {}]
        # goal {'slug', 'last_datapoint}
        return list_of_goals
    
    def get_datapoints(self, slug, count=None, sort=None):
        endpoint = f'users/{self._username}/goals/{slug}/datapoints.json'
        data = {}
        if count: data['count']=count
        if sort: data['sort']=sort
        datapoints = self._call(endpoint, data) # list of datapoints
        # {'timestamp', 'value', 'comment', 'daystamp'}
        return datapoints

    def add_datapoint(self, slug: str, value: float, comment: Optional[str] = None) -> JSON_Dict:
        slug = self.name_to_slug(slug)
        endpoint = f'users/{self._username}/goals/{slug}/datapoints.json'
        data : Dict[str, Any] = {'value': value}
        if comment is not None:
            data['comment'] = comment
        result = self._call(endpoint, data, method='POST')
        print(f"add_datapoint(): added {value} to {slug}")
        return result
    
    def get_user(self) -> JSON_Dict:
        endpoint = f'users/{self._username}.json'
        user = self._call(endpoint)

        goals_slugs = user['goals'] # list of slugs ['', '', ]
        updated_at = user['updated_at'] # timestamp of last update
        last_update_date = datetime.fromtimestamp(updated_at) #datetime object
        return user
    
    def charge(self, note: str,amount: int = 0, dryrun: str = '') -> Optional[JSON_Dict]:
        endpoint = 'charges.json'
        if not amount: amount = DEFAULT_CHARGE_AMOUNT
        data = {'amount':amount, note:'note'}
        if dryrun or self.debug or note=="break": 
            return
        charge = self._call(endpoint, data, method='POST')
        print(f"!!! charged {amount}$ for {note}")
        return charge

    def add_time_tracked(self, secondsTracked: int):
        if secondsTracked > 100:
            hoursTracked = secondsTracked / 60 / 60
            self.add_datapoint(TRACKED, hoursTracked)
    
    def _call(self, endpoint: str,
                    data: Optional[JSON_Dict] = None,
                    method: str = 'GET') -> JSON_Dict:
        if not data: data = {}
        data['auth_token'] = self._token
        
        url = f'{self._base_url}/{endpoint}/'
        
        if method== 'GET':
            result = requests.get(url, data)
        elif method == 'POST':
            result = requests.post(url, data)
        elif method == 'PUT':
            result = requests.put(url, data)
        else: # method 
            raise Exception(f'_call(), unknown method: {method}')
        
        if not result.status_code == requests.codes.ok:
            raise Exception(f'Beeminder API failed with code {result.status_code}: {result.text}')

        return result.json()

