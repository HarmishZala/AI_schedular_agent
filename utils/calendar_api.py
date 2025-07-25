import os
import datetime
import pickle
from typing import List, Optional
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.pickle'

class GoogleCalendarAPI:
    def __init__(self):
        self.creds = None
        self.service = None
        self.authenticate()

    def authenticate(self):
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'rb') as token:
                self.creds = pickle.load(token)
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                self.creds = flow.run_local_server(port=0)
            with open(TOKEN_FILE, 'wb') as token:
                pickle.dump(self.creds, token)
        self.service = build('calendar', 'v3', credentials=self.creds)

    def get_user_calendars(self) -> List[dict]:
        calendars_result = self.service.calendarList().list().execute()
        return calendars_result.get('items', [])

    def get_events(self, calendar_id: str = 'primary', time_min: Optional[str] = None, time_max: Optional[str] = None) -> List[dict]:
        events_result = self.service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        return events_result.get('items', [])

    def create_event(self, calendar_id: str, event: dict) -> dict:
        event = self.service.events().insert(calendarId=calendar_id, body=event).execute()
        return event

    def update_event(self, calendar_id: str, event_id: str, updated_event: dict) -> dict:
        event = self.service.events().update(calendarId=calendar_id, eventId=event_id, body=updated_event).execute()
        return event

    def delete_event(self, calendar_id: str, event_id: str) -> None:
        self.service.events().delete(calendarId=calendar_id, eventId=event_id).execute()

    def get_event(self, calendar_id: str, event_id: str) -> dict:
        event = self.service.events().get(calendarId=calendar_id, eventId=event_id).execute()
        return event

    def batch_delete_events(self, calendar_id: str, time_min: str, time_max: str) -> List[str]:
        """Delete all events in a calendar between time_min and time_max. Returns list of deleted event IDs."""
        events = self.get_events(calendar_id, time_min, time_max)
        deleted_ids = []
        for event in events:
            event_id = event.get('id')
            if event_id:
                self.delete_event(calendar_id, event_id)
                deleted_ids.append(event_id)
        return deleted_ids
