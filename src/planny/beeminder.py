from typing import Optional
from planny.utils import *
import requests
from datetime import datetime
from _private import BEEMINDER_USER, BEEMINDER_TOKEN

# slugs
MEDITATION='meditation'
SITUPS = 'situps'
PUSHUPS = 'pushups'
STRETCH = 'stretch'
RUN = 'run'
BEEMINDER_PATTERNS = ['pushups?', 'situps?','run', 'ran', 'stretch', 'meditation', 'water']

class Beeminder:
    def __init__(self, user=BEEMINDER_USER, token=BEEMINDER_TOKEN) -> None:
        self._base_url="https://www.beeminder.com/api/v1"
        self._user=user
        self._token=token

    @staticmethod
    def name_to_slug(name: str) -> str:
        d = {
            'pushup':PUSHUPS, 'pushups?':PUSHUPS,
            'situp':SITUPS,'situps?':SITUPS, 'crunch':SITUPS, 'crunches':SITUPS,
            'drink':'water',
            'stretched':STRETCH, 'stretches':STRETCH, 'stretching':STRETCH,
            'running':RUN, 'ran':RUN,
            'meditated':MEDITATION, 'meditate':MEDITATION
            }
        return d.get(name, name)

    
    def get_goal(self,slug: str) -> JSON_Dict:
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
        endpoint = f'users/{self._user}/goals/{slug}/datapoints.json'
        data = {}
        if count: data['count']=count
        if sort: data['sort']=sort
        datapoints = self._call(endpoint, data) # list of datapoints
        # {'timestamp', 'value', 'comment', 'daystamp'}
        return datapoints

    def add_datapoint(self, slug: str, value: float, comment: Optional[str] = None) -> JSON_Dict:
        slug = self.name_to_slug(slug)
        print(f"add_datapoint(): added {value} to {slug}")
        endpoint = f'users/{self._user}/goals/{slug}/datapoints.json'
        data : Dict[str, Any] = {'value': value}
        if comment is not None:
            data['comment'] = comment
        result = self._call(endpoint, data, method='POST')
        return result
    
    def get_user(self) -> JSON_Dict:
        endpoint = f'users/{self._user}.json'
        user = self._call(endpoint)

        goals_slugs = user['goals'] # list of slugs ['', '', ]
        updated_at = user['updated_at'] # timestamp of last update
        last_update_date = datetime.fromtimestamp(updated_at) #datetime object
        return user
    
    def charge(self, amount: float, note: str, dryrun: str = 'true') -> JSON_Dict:
        endpoint = 'charges.json'
        data = {'amount':amount, note:'note', 'dryrun':dryrun}
        charge = self._call(endpoint, data, method='POST')
        return charge
    
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
    