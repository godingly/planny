""" beeminder integration"""
from typing import List, Optional
import requests
from datetime import datetime
import time
import json
from typing import Any, Dict
JSON_Dict = Dict[str, Any]

# slugs
MEDITATION = 'meditation'
SITUPS = 'situps'
PUSHUPS = 'pushups'
STRETCH = 'stretches'
RUN = 'run'
TRACK = 'track'
WATER = 'water2'
WEIGHT = 'weight'
WEIGHT_LOGGING = 'weight_logging'

DEFAULT_CHARGE_AMOUNT = 5 # default amount of dollars to charge

def get_today_midnight_unix_timestamp() -> int:
    """ return unix timestamp of this midnight"""
    midnight_dt = datetime.now().replace(hour=0,minute=0,second=0,microsecond=0)
    return int(midnight_dt.timestamp())

def get_today_daystamp() -> str:
    """ return str '17760704' """
    return datetime.today().strftime('%Y%m%d')

def get_unix_timestamp() -> int: return int(time.time())


class Beeminder:
    def __init__(self, json_path: str, debug: bool) -> None:
        self._base_url="https://www.beeminder.com/api/v1"
        # read user and authentication from json
        with open(json_path) as f:
            d = json.load(f)
        self._username=d['username']
        self._token=d['auth_token']
        self.debug = debug
        self.last_track_datapoint = {}
    
    # Global
    @staticmethod
    def name_to_slug(name: str) -> str:
        d = {
            'drink':WATER, 'water':WATER, 'drank':WATER, 
            'meditated':MEDITATION, 'meditate':MEDITATION, 'meditation':MEDITATION, 'meditations':MEDITATION,
            'pushup':PUSHUPS, 'pushups':PUSHUPS,
            'running':RUN, 'ran':RUN, 'run':RUN,
            'situp':SITUPS, 'situps':SITUPS, 
            'stretched':STRETCH, 'stretches':STRETCH, 'stretching':STRETCH, 'stretch':STRETCH,
            "tracked":TRACK, 'track':TRACK,
            "weight": WEIGHT,
            "weight_logging": WEIGHT_LOGGING,
            }
        return d.get(name.lower(), name)

    def get_user(self) -> JSON_Dict:
        endpoint = f'users/{self._username}.json'
        user = self._call(endpoint)

        goals_slugs = user['goals'] # list of slugs ['', '', ]
        updated_at = user['updated_at'] # timestamp of last update
        last_update_date = datetime.fromtimestamp(updated_at) #datetime object
        return user

    def get_goal_with_all_datapoints(self,slug: str) -> JSON_Dict:
        endpoint = f'users/{self._username}/goals/{slug}.json'
        data = {'datapoints':'true'}
        result = self._call(endpoint, data)
        return result

    def get_goals(self) -> List[JSON_Dict]:
        endpoint = f'users/{self._username}/goals.json'
        list_of_goals = self._call(endpoint) # list of goals [{'slug', 'last_datapoint'}, {}, .. , {}]
        return list_of_goals

    # Datapoints
    def get_datapoints(self, slug, count: int=0, sort: str='') -> List[JSON_Dict]:
        """ get [count] slug datapoints, possible sort
        sort is the attribute to sort by. could be id, updated_at, daystamp.
        returns [{'timestamp':unix_timestamp,'value', 'id', 'updated_at':unix_timestamp, 'daystamp':str}, {}, ...]"""
        slug = self.name_to_slug(slug)
        endpoint = f'users/{self._username}/goals/{slug}/datapoints.json'
        data = {}
        if count: data['count'] = count
        if sort: data['sort'] = sort
        datapoints = self._call(endpoint, data) # list of datapoints
        # {'timestamp', 'value', 'comment', 'daystamp'}
        return datapoints

    def get_last_datapoint(self, slug):
        """ returns last datapoint by update {'timestamp':unix_timestamp, 'value', 'id', 'updated_at':unix_timestamp, 'daystamp':str}"""
        datapoints = self.get_datapoints(slug, count=1, sort='updated_at')
        return datapoints[0]
    
    def add_datapoint(self, slug: str, value: float, comment: Optional[str] = None) -> JSON_Dict:
        """ returns added datapoint={'timestamp':unix_timestamp, 'value', 'id', 'updated_at':unix_timestamp, 'daystamp':str}"""
        if (slug=='weight'): 
            self.add_datapoint(WEIGHT_LOGGING, 1)
        slug = self.name_to_slug(slug)

        endpoint = f'users/{self._username}/goals/{slug}/datapoints.json'
        data : Dict[str, Any] = {'value': value}
        if comment is not None:
            data['comment'] = comment
        datapoint_dict = self._call(endpoint, data, method='POST')
        if datapoint_dict:
            print(f"add_datapoint(): added {value} to {slug}")
        else:
            print(f'error add_datapoint({slug}, {value})')
        return datapoint_dict

    def update_datapoint(self, slug: str, datapoint_id: str, value: float) -> JSON_Dict:
        """ returns updated datapoint = {'timestamp':unix_timestamp, 'value', 'id', 'updated_at':unix_timestamp, 'daystamp':str}"""
        slug = self.name_to_slug(slug)
        endpoint = f'users/{self._username}/goals/{slug}/datapoints/{datapoint_id}.json'
        data : Dict[str, Any] = {'value': value}
        datapoint_dict = self._call(endpoint, data, method='PUT')
        print(f"beeminder::update_datapoint(): updated {value} at {slug}")
        return datapoint_dict
        
    # Charge
    def charge(self, note: str,amount: int = 0, dryrun: str = '') -> Optional[JSON_Dict]:
        endpoint = 'charges.json'
        if not amount: amount = DEFAULT_CHARGE_AMOUNT
        data = {'amount':amount, note:'note'}
        if dryrun or self.debug or note=="break": 
            print(f"!!! (not) charged {amount}$ for {note}")
            return
        charge = self._call(endpoint, data, method='POST')
        with open(r'C:\Users\godin\Python\planny\src\credentials\charges.txt', 'a') as f:
            date = datetime.now().strftime('%d-%b-%Y %H:%M')
            f.write(f"{date}: {note}, {amount}$\n")
        print(f"!!! CHARGED {amount}$ FOR {note}")
        return charge

    def add_time_tracked(self, seconds_tracked: int):
        """ seconds_tracked - number of seconds to add"""
        if seconds_tracked < 100: return
        
        hours_tracked = seconds_tracked / 60 / 60
        
        if not self.last_track_datapoint:
            self.last_track_datapoint = self.get_last_datapoint(TRACK)
        
        # if not from today, create new one
        if self.last_track_datapoint['daystamp'] != get_today_daystamp():
            self.last_track_datapoint = self.add_datapoint(TRACK, hours_tracked)
        else: # update
            self.last_track_datapoint = self.update_datapoint(TRACK, self.last_track_datapoint['id'], self.last_track_datapoint['value'] + hours_tracked)
    
    # General
    def _call(self, endpoint: str,
                    data: Optional[JSON_Dict] = None,
                    method: str = 'GET'):
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
            raise Exception(f'Beeminder API failed with code {result.status_code}: {result.text}, {method} {url}')

        return result.json()


def main():
    json_path = r'C:\Users\godin\Python\planny\src\credentials\beeminder.json'
    b = Beeminder(json_path, debug=True)
    res = b.add_time_tracked(seconds_tracked=200)
    # print(res)
    a=3

if __name__=='__main__':
    main()
