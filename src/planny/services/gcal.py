from datetime import datetime
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import planny.utils.time as utils_time


# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']


def get_credentials(secret_credentials_path: str):
    """
    secret credentials at https://developers.google.com/workspace/guides/create-credentials
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            flow = InstalledAppFlow.from_client_secrets_file(secret_credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds #type google.oauth2.credentials.Credentials

class GCal:
    def __init__(self, secret_credentials_path: str, debug : bool):
        self.creds = get_credentials(secret_credentials_path)
        self.service = build('calendar', 'v3', credentials=self.creds) # type googleapiclient.discovery.Resource
        self.timeZone_str = utils_time.get_local_timezone_str()
        self.debug = debug

    def get_events(self):
        now = datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
        print('Getting the upcoming 10 events')
        events_result = self.service.events().list(calendarId='primary', timeMin=now,
                                            maxResults=10, singleEvents=True,
                                            orderBy='startTime').execute() # dict
        events = events_result.get('items', []) # List[event]

        if not events:
            print('No upcoming events found.')
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(start, event['summary'])

    def add_event(self,
                 summary : str,
                 start: datetime,
                 end : datetime, 
                 all_day: bool=False):
        """
        start/end (datetime) aware, in local timezone, 
        if all-day, then only YYYY-MM-DD
        """
        # TODO maybe input should be in utc
        start_datetime_iso = start.isoformat()
        end_datetime_iso = end.isoformat()
        if all_day:
            start_date = start_datetime_iso.split('T')[0]
            end_date = end_datetime_iso.split('T')[0]
            event = {
                'start': {
                    'date': start_date,
                    'timeZone': self.timeZone_str,},
                'end': {
                    'date': end_date,
                    'timeZone': self.timeZone_str,},
                'summary':summary
            }
        else:
            event={
                'start': {
                    'dateTime': start_datetime_iso,
                    'timeZone': self.timeZone_str,},
                'end': {
                    'dateTime': end_datetime_iso,
                    'timeZone': self.timeZone_str,},
                'summary':summary
            }    
        event = self.service.events().insert(calendarId='primary', body=event).execute() # dict
        assert event['status'] == 'confirmed', f'event={event}, {summary}, start={start}, end={end}'
        event_id = event['id']
        print ('Event created: %s' % (event.get('htmlLink')))
        return event_id

def update_event(event_id):
    # TODO
    pass

def delete_event(event_id):
    # TODO
    pass

def quick_add(summary):
    pass


def main():
    pass


if __name__ == '__main__':
    main()