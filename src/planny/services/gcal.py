import sys
from typing import Any, Dict, List
if __name__=='__main__': sys.path.insert(0,r'C:\Users\godin\Python\planny\src')

from datetime import datetime, timedelta
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow, Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import planny.utils.time as utils_time
from planny.utils.utils import *


# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']
PRIMARY = 'primary'
PLANNY_CMD = 'planny_cmd'
JSON_Dict = Dict[str, Any]

def iso_str_to_datetime(iso_str: str) -> datetime:
    """convert from isoformat 2021-09-02T14:00:00+03:00 to aware datetime.datetime object"""
    return datetime.fromisoformat(iso_str)

def is_current(event_dict) -> bool:
    """ returns true if event is happening currently"""
    start_dt = event_dict['start']['dateTime']
    end_dt = event_dict['end']['dateTime']
    start_dt = datetime.fromisoformat(start_dt)
    end_dt = datetime.fromisoformat(end_dt)
    now = utils_time.get_current_local(with_seconds=True)
    return (start_dt <= now) and (now <= end_dt)

# OLD WORKING CODE
# def get_credentials(client_secrets: str, gcal_token_path: str=""):
#     """ secret credentials at https://developers.google.com/workspace/guides/create-credentials"""
#     creds = None
#     # The file token.json stores the user's access and refresh tokens, and is
#     # created automatically when the authorization flow completes for the first
#     # time.
#     if gcal_token_path and os.path.exists(gcal_token_path):
#         creds = Credentials.from_authorized_user_file(gcal_token_path, SCOPES)
#     # If there are no (valid) credentials available, let the user log in.
#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file(client_secrets, SCOPES)

#             creds = flow.run_local_server(port=0)
#         # Save the credentials for the next run
#         with open(gcal_token_path, 'w') as token:
#             token.write(creds.to_json())
#     return creds #type google.oauth2.credentials.Credentials


def get_credentials(client_secrets: str, gcal_token_path: str=""):
    """
    https://github.com/googleapis/google-api-python-client
    https://stackoverflow.com/questions/30637984/what-does-offline-access-in-oauth-mean/30638344
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if gcal_token_path and os.path.exists(gcal_token_path):
        creds = Credentials.from_authorized_user_file(gcal_token_path, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid: # create creds first time
        print("gcal::get_credentials() creds aren't valid!!")
        flow = InstalledAppFlow.from_client_secrets_file(client_secrets, SCOPES)
        authorization_url, state = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type='offline',
        # Enable incremental authorization. Recommended as a best practice.
        include_granted_scopes='true')
        creds = flow.run_local_server(port=0)
        with open(gcal_token_path, 'w') as token:
            token.write(creds.to_json())
        return creds
    
    if creds and creds.expired: # refresh
        print("gcal::get_credentials() trying to refresh")
        creds = Credentials(token=None, 
                            refresh_token=creds.refresh_token,
                            id_token=creds.id_token,
                            token_uri=creds.token_uri,
                            client_id=creds.client_id,
                            client_secret=creds.client_secret,
                            scopes=creds.scopes)
        with open(gcal_token_path, 'w') as token:
            token.write(creds.to_json())
    
    return creds #type google.oauth2.credentials.Credentials

def event_to_dict(event) -> JSON_Dict:
    d = { key:event[key] for key in ['id', 'summary', 'start', 'end'] }
    d['calendar_name'] = event['organizer']['displayName']
    return d

class GCal:
    def __init__(self, client_secrets: str, gcal_token_path: str="", debug: bool = False):
        self.creds = get_credentials(client_secrets, gcal_token_path)
        self.service = build('calendar', 'v3', credentials=self.creds) # type googleapiclient.discovery.Resource
        self.timeZone_str = utils_time.get_local_timezone_str()
        self.debug = debug
        self.primaryCal = 'primary'
        self.calendar_names_to_ids = self.get_calendars_names_to_ids()

    def exit(self):
        self.service.close()
    
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
        list_of_event_dicts_res = events_result.get('items', []) # List[{}, {}, ]
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
        try:
            event = self.service.events().insert(calendarId=calendarId, body=event).execute() # type: ignore    
        except Exception as e:
            print('An exception occurred: {}'.format(e))
            return 0
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
        """ return {'id', 'summary', 'start':{'dateTime'}, 'end':{'dateTime'}, 'next_event'}, or empty dict """
        list_event_dicts = self.get_events(PLANNY_CMD, maxResults=2)
        if not list_event_dicts: return {}
        first_event = list_event_dicts[0]
        if not is_current(first_event): return {}
        first_event['next_event'] = list_event_dicts[1]['summary'] if len (list_event_dicts)>=2 else ''
        return first_event
    
    def get_next_planny_cmd(self) -> JSON_Dict:
        """ return {'id', 'summary', 'start':{'dateTime'}, 'end':{'dateTime'}} """
        return self.get_events(calendar_name=PLANNY_CMD, maxResults=1)[0]

    def get_second_planny_cmd(self) -> JSON_Dict:
        """ return event after the current one"""
        list_events = self.get_events(calendar_name=PLANNY_CMD, maxResults=2)
        if len(list_events) < 2:
            return {}
        return list_events[1]

    def add_planny_cmd_event(self, summary:str, start: datetime, end:datetime):
        self.add_event(summary, start, end, calendar_name=PLANNY_CMD)
    
    def delete_current_planny_cmd(self):
        self.delete_current_event(PLANNY_CMD)

if __name__ == '__main__':
    credentials_path = r'C:\Users\godin\Python\planny\src\credentials\credentials_gcal_desktop_secret.json'
    gcal_token_path = r'C:\Users\godin\Python\planny\src\credentials\gcal_token.json'
    gcal = GCal(credentials_path, gcal_token_path=gcal_token_path, debug=True)
    res = gcal.get_current_planny_cmd()
    print(res)
    a=3
    

