import sys
from typing import Any, Dict, List
if __name__=='__main__': sys.path.insert(0,r'C:\Users\godin\Python\planny\src')

from datetime import datetime, timedelta
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import planny.utils.time as utils_time
from planny.utils.utils import *


# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']
PRIMARY = 'primary'
PLANNY_CMD = 'planny_cmd'
JSON_Dict = Dict[str, Any]


def get_credentials(secret_credentials_path: str, gcal_token_path: str=""):
    """
    secret credentials at https://developers.google.com/workspace/guides/create-credentials
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if gcal_token_path and os.path.exists(gcal_token_path):
        creds = Credentials.from_authorized_user_file(gcal_token_path, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            flow = InstalledAppFlow.from_client_secrets_file(secret_credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(gcal_token_path, 'w') as token:
            token.write(creds.to_json())
    return creds #type google.oauth2.credentials.Credentials

def event_to_dict(event) -> JSON_Dict:
    d = { key:event[key] for key in ['id', 'summary', 'start', 'end'] }
    d['calendar_name'] = event['organizer']['displayName']
    return d

class GCal:
    def __init__(self, secret_credentials_path: str, gcal_token_path: str="", debug: bool = False):
        self.creds = get_credentials(secret_credentials_path, gcal_token_path)
        self.service = build('calendar', 'v3', credentials=self.creds) # type googleapiclient.discovery.Resource
        self.timeZone_str = utils_time.get_local_timezone_str()
        self.debug = debug
        self.primaryCal = 'primary'
        self.calendar_names_to_ids = self.get_calendars_names_to_ids()

    def get_calendars_names_to_ids(self):
        list_of_calendar_dicts = self.service.calendarList().list().execute()['items'] # type: ignore # list
        names_to_ids = {}
        for d in list_of_calendar_dicts:
            if d.get('primary', False): continue
            names_to_ids[ d['summary'] ] = d['id']
        return names_to_ids
    
    def get_current_event(self, calendar_name='') -> JSON_Dict:
        """ returns dict of current event if there's one,
        {'id','summary','start':{'dateTime'/'date'}, 'end':{'dateTime}, 'calendar_name'}"""
        calendarId = 'primary' if not calendar_name else self.calendar_names_to_ids[calendar_name]
        now = datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
        nextMinute = (datetime.utcnow() + timedelta(minutes=1)).isoformat() + 'Z'
        events_result = self.service.events().list(calendarId=calendarId, timeMin=now,  # type: ignore
                                        timeMax=nextMinute, maxResults=1,
                                        singleEvents=True,
                                        orderBy='startTime').execute() 
        list_of_event_dicts_res = events_result.get('items', []) # List[event]
        if not list_of_event_dicts_res:
            print(f'gcal::get_current_event({calendar_name}) - No events found ')
            return {}
        return event_to_dict(list_of_event_dicts_res[0])
    
    def delete_event(self, calendar_id, event_id):
        self.service.events().delete(calendarId=calendar_id, eventId=event_id).execute() # type: ignore
    
    def get_events(self, calendar_name='', maxResults=10) -> List[JSON_Dict]:
        """ returns list of event dicts, sorted by start time,
        [{'id','summary','start':{'dateTime'/'date'}, 'end':{'dateTime}, 'calendar_name'}]"""
        calendarId = 'primary' if not calendar_name else self.calendar_names_to_ids[calendar_name]

        now = datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
        
        events_result = self.service.events().list(calendarId=calendarId, timeMin=now, # type: ignore
                                            maxResults=maxResults, singleEvents=True,
                                            orderBy='startTime').execute() # dict
        list_of_event_dicts_res = events_result.get('items', []) # List[event]
        if not list_of_event_dicts_res:
            print(f'gcal::get_events({calendar_name}) - No events found')
        my_list_event_dicts = [] # sorted by start time
        for event in list_of_event_dicts_res: # event['start]['dateTime'] - isostring, event['summary']
            # 'id', 'summary', 'start':{'dateTime'}, 'end':{'dateTime}', 'calendar_name'
            my_list_event_dicts.append(event_to_dict(event))
        
        return my_list_event_dicts

    def add_event(self, summary : str,                  
                  start: datetime,
                  end : datetime,
                  calendar_name: str='',
                  all_day: bool=False):
        """ start/end (datetime) aware, in local timezone,  if all-day, then only YYYY-MM-DD """
        calendarId = 'primary' if not calendar_name else self.calendar_names_to_ids[calendar_name]
        start_datetime_iso = start.isoformat()
        end_datetime_iso = end.isoformat()
        if all_day:
            start_date = start_datetime_iso.split('T')[0]
            end_date = end_datetime_iso.split('T')[0]
            event = {'start': {'date': start_date, 'timeZone': self.timeZone_str,},
                     'end': {'date': end_date, 'timeZone': self.timeZone_str,},
                     'summary':summary}
        else:
            event = {'start': { 'dateTime': start_datetime_iso, 'timeZone': self.timeZone_str,},
                     'end': {'dateTime': end_datetime_iso, 'timeZone': self.timeZone_str,},
                     'summary':summary}    
        event = self.service.events().insert(calendarId=calendarId, body=event).execute() # type: ignore
        assert event['status'] == 'confirmed', f'event={event}, {summary}, start={start}, end={end}'
        event_id = event['id']
        return event_id

    def delete_current_event(self, calendar_name='primary'):
        calendarId = 'primary' if not calendar_name else self.calendar_names_to_ids[calendar_name]
        event_dict = self.get_current_event(calendar_name)
        if not event_dict:
            return
        self.delete_event(calendarId, event_dict['id'])
    
    ######### PLANNY_CMD #######
    def get_current_planny_cmd(self) -> JSON_Dict:
        """ return {'id', 'summary', 'start':{'dateTime'}, 'end':{'dateTime'}}, or empty dict """
        return self.get_current_event(PLANNY_CMD)
    
    def get_next_planny_cmd(self) -> JSON_Dict:
        """ return {'id', 'summary', 'start':{'dateTime'}, 'end':{'dateTime'}} """
        return self.get_events(calendar_name=PLANNY_CMD, maxResults=1)[0]

    def add_planny_cmd_event(self, summary:str, start: datetime, end:datetime):
        self.add_event(summary, start, end, calendar_name=PLANNY_CMD)
    
    def delete_current_planny_cmd(self):
        self.delete_current_event(PLANNY_CMD)


def iso_str_to_datetime(iso_str: str) -> datetime:
    """convert from isoformat 2021-09-02T14:00:00+03:00 to aware datetime.datetime object"""
    return datetime.fromisoformat(iso_str)


if __name__ == '__main__':
    credentials_path = r'C:\Users\godin\Python\planny\src\credentials\credentials_gcal_desktop_secret.json'
    gcal = GCal(credentials_path)
    gcal.delete_current_planny_cmd()
    
    a=3
    

