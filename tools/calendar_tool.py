from utils.calendar_api import GoogleCalendarAPI
from langchain.tools import tool
from typing import List
from datetime import datetime, timedelta
import pytz

LONDON_TZ = 'Europe/London'

# Helper for pretty date formatting
def pretty_datetime(dt_str):
    if not dt_str:
        return ''
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        dt = dt.astimezone(pytz.timezone(LONDON_TZ))
        return dt.strftime('%d %B %Y, %I:%M %p')
    except Exception:
        return dt_str

class CalendarTool:
    def __init__(self):
        self.api = GoogleCalendarAPI()
        self.calendar_tool_list = self._setup_tools()

    def _setup_tools(self) -> List:
        @tool
        def list_calendars(show_ids: bool = False) -> str:
            """List all user calendars (categories) with their names. Set show_ids=True to include IDs. Use this to help the user pick a calendar for further actions."""
            calendars = self.api.get_user_calendars()
            if not calendars:
                return 'No calendars found.'
            if show_ids:
                result = 'Your calendars:\n'
                for cal in calendars:
                    result += f"- {cal.get('summary','(No Name)')} (ID: {cal.get('id')})\n"
            else:
                result = 'Your calendars:\n'
                for cal in calendars:
                    result += f"- {cal.get('summary','(No Name)')}\n"
            return result

        @tool
        def list_events(calendar_id: str = 'primary', time_min: str = None, time_max: str = None) -> str:
            """List events for a calendar (optionally between time_min and time_max, RFC3339 format). Defaults to today in London time if no range is given. Use this to help the user see their schedule or pick events to update/delete."""
            tz = pytz.timezone(LONDON_TZ)
            if not time_min or not time_max:
                now = datetime.now(tz)
                start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                end = start.replace(hour=23, minute=59, second=59)
                time_min = start.isoformat()
                time_max = end.isoformat()
            events = self.api.get_events(calendar_id, time_min, time_max)
            if not events:
                return 'No events found for this period.'
            result = f"Events for {calendar_id} from {pretty_datetime(time_min)} to {pretty_datetime(time_max)}:\n"
            for ev in events:
                summary = ev.get('summary', '(No Title)')
                start = pretty_datetime(ev.get('start', {}).get('dateTime', ev.get('start', {}).get('date', '')))
                end = pretty_datetime(ev.get('end', {}).get('dateTime', ev.get('end', {}).get('date', '')))
                desc = ev.get('description', '')
                location = ev.get('location', '')
                result += f"- **{summary}**\n  Date: {start} to {end}\n  Description: {desc}\n  Location: {location}\n\n"
            return result

        @tool
        def search_events_by_keyword(calendar_id: str = 'primary', keyword: str = '', time_min: str = None, time_max: str = None) -> str:
            """Search for events in a calendar by keyword in the title or description, optionally in a time range. Returns a formatted list of matching events."""
            events = self.api.get_events(calendar_id, time_min, time_max)
            matches = [ev for ev in events if keyword.lower() in ev.get('summary','').lower() or keyword.lower() in ev.get('description','').lower()]
            if not matches:
                return f'No events found with keyword "{keyword}".'
            result = f"Events matching '{keyword}':\n"
            for ev in matches:
                summary = ev.get('summary', '(No Title)')
                start = pretty_datetime(ev.get('start', {}).get('dateTime', ev.get('start', {}).get('date', '')))
                end = pretty_datetime(ev.get('end', {}).get('dateTime', ev.get('end', {}).get('date', '')))
                result += f"- **{summary}**\n  Date: {start} to {end}\n  Event ID: {ev.get('id','')}\n\n"
            return result

        @tool
        def get_event_details(calendar_id: str = 'primary', event_id: str = '') -> str:
            """Get full details for a specific event by event_id. Returns a formatted summary."""
            if not event_id:
                return 'Please provide an event ID.'
            ev = self.api.get_event(calendar_id, event_id)
            summary = ev.get('summary', '(No Title)')
            start = pretty_datetime(ev.get('start', {}).get('dateTime', ev.get('start', {}).get('date', '')))
            end = pretty_datetime(ev.get('end', {}).get('dateTime', ev.get('end', {}).get('date', '')))
            desc = ev.get('description', '')
            location = ev.get('location', '')
            return f"**Event Details**\n- **Title:** {summary}\n- **Date:** {start} to {end}\n- **Description:** {desc}\n- **Location:** {location}\n- **Event ID:** {ev.get('id','')}\n"

        @tool
        def move_event(calendar_id: str, event_id: str, new_start: str, new_end: str) -> str:
            """Move/reschedule an event to a new time. Provide event_id, new_start, and new_end in RFC3339 format. Returns a confirmation."""
            ev = self.api.get_event(calendar_id, event_id)
            ev['start']['dateTime'] = new_start
            ev['start']['timeZone'] = LONDON_TZ
            ev['end']['dateTime'] = new_end
            ev['end']['timeZone'] = LONDON_TZ
            updated = self.api.update_event(calendar_id, event_id, ev)
            return f"Event '{updated.get('summary','(No Title)')}' moved to {pretty_datetime(new_start)} - {pretty_datetime(new_end)}."

        @tool
        def get_events_duration(calendar_id: str = 'primary', time_min: str = None, time_max: str = None) -> str:
            """Calculate the total duration of all events in a calendar in a given time range. Returns the total hours and a summary."""
            events = self.api.get_events(calendar_id, time_min, time_max)
            total_minutes = 0
            for ev in events:
                start = ev.get('start', {}).get('dateTime', ev.get('start', {}).get('date', ''))
                end = ev.get('end', {}).get('dateTime', ev.get('end', {}).get('date', ''))
                try:
                    dt_start = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    dt_end = datetime.fromisoformat(end.replace('Z', '+00:00'))
                    total_minutes += int((dt_end - dt_start).total_seconds() // 60)
                except Exception:
                    continue
            hours = total_minutes // 60
            minutes = total_minutes % 60
            return f"Total scheduled time: {hours} hours {minutes} minutes ({len(events)} events)."

        @tool
        def get_free_busy(calendar_id: str = 'primary', date: str = None) -> str:
            """Show free/busy slots for a given day (date in YYYY-MM-DD). Returns a formatted list of busy slots."""
            tz = pytz.timezone(LONDON_TZ)
            if not date:
                date = datetime.now(tz).strftime('%Y-%m-%d')
            start = tz.localize(datetime.strptime(date, '%Y-%m-%d')).replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
            events = self.api.get_events(calendar_id, start.isoformat(), end.isoformat())
            if not events:
                return f'You are free all day on {pretty_datetime(start.isoformat())[:11]}.'
            result = f"Busy slots for {pretty_datetime(start.isoformat())[:11]}:\n"
            for ev in events:
                ev_start = pretty_datetime(ev.get('start', {}).get('dateTime', ev.get('start', {}).get('date', '')))
                ev_end = pretty_datetime(ev.get('end', {}).get('dateTime', ev.get('end', {}).get('date', '')))
                result += f"- {ev_start} to {ev_end}\n"
            return result

        @tool
        def quick_add_event(calendar_id: str = 'primary', text: str = '') -> str:
            """Quickly add an event using a single natural language string (e.g., 'Lunch with Bob at 1pm Friday'). Returns a confirmation."""
            # This is a placeholder; Google Calendar API has a quickAdd endpoint, but not in v3 Python client. We'll parse with LLM and call create_event.
            return f"Quick add: {text}. Please use the create_event tool for full details."

        @tool
        def create_event(calendar_id: str, summary: str, start: str, end: str, description: str = "", location: str = "", minimal: bool = False) -> str:
            """Create an event in a calendar. Dates in RFC3339 format, always using Europe/London time zone. Set minimal=True for a short confirmation message. Always confirm with a detailed, nicely formatted summary."""
            event = {
                'summary': summary,
                'location': location,
                'description': description,
                'start': {'dateTime': start, 'timeZone': LONDON_TZ},
                'end': {'dateTime': end, 'timeZone': LONDON_TZ},
            }
            created = self.api.create_event(calendar_id, event)
            if minimal:
                return f"Event '{created.get('summary','(No Title)')}' created."
            summary_text = f"**Event Created!**\n\n- **Title:** {created.get('summary','(No Title)')}\n- **Date:** {pretty_datetime(created['start'].get('dateTime',''))} to {pretty_datetime(created['end'].get('dateTime',''))} (Europe/London)\n- **Description:** {created.get('description','')}\n- **Location:** {created.get('location','')}\n- **Calendar:** {calendar_id}\n- **Event ID:** {created.get('id','')}\n"
            return summary_text

        @tool
        def update_event(calendar_id: str, event_id: str, summary: str = None, start: str = None, end: str = None, description: str = None, location: str = None, minimal: bool = False) -> str:
            """Update an event in a calendar. Only provided fields will be updated. Dates in RFC3339, Europe/London. Set minimal=True for a short confirmation message. Always confirm with a detailed, nicely formatted summary."""
            event = self.api.get_event(calendar_id, event_id)
            if summary: event['summary'] = summary
            if start: event['start']['dateTime'] = start; event['start']['timeZone'] = LONDON_TZ
            if end: event['end']['dateTime'] = end; event['end']['timeZone'] = LONDON_TZ
            if description: event['description'] = description
            if location: event['location'] = location
            updated = self.api.update_event(calendar_id, event_id, event)
            if minimal:
                return f"Event '{updated.get('summary','(No Title)')}' updated."
            return f"Event updated: {updated.get('summary','(No Title)')} ({pretty_datetime(updated['start'].get('dateTime',''))} to {pretty_datetime(updated['end'].get('dateTime',''))})"

        @tool
        def delete_event(calendar_id: str, event_id: str, minimal: bool = False) -> str:
            """Delete a single event from a calendar by event_id. Set minimal=True for a short confirmation message. Use this when the user specifies a specific event to delete."""
            self.api.delete_event(calendar_id, event_id)
            if minimal:
                return f"Event deleted."
            return f"Event {event_id} deleted from {calendar_id}"

        @tool
        def delete_events_in_range(calendar_id: str = 'primary', time_min: str = None, time_max: str = None) -> str:
            """Delete all events in a calendar between time_min and time_max (RFC3339 format). Use this for requests like 'delete all events between 2-7pm from tomorrow onwards'. Always confirm with a nicely formatted summary of deleted events."""
            if not time_min or not time_max:
                return 'Please specify a valid time range.'
            deleted_ids = self.api.batch_delete_events(calendar_id, time_min, time_max)
            if not deleted_ids:
                return 'No events found to delete in the specified range.'
            result = f"Deleted {len(deleted_ids)} event(s) from {calendar_id} between {pretty_datetime(time_min)} and {pretty_datetime(time_max)}:\n"
            for eid in deleted_ids:
                result += f"- Event ID: {eid}\n"
            return result

        return [list_calendars, list_events, search_events_by_keyword, get_event_details, move_event, get_events_duration, get_free_busy, quick_add_event, create_event, update_event, delete_event, delete_events_in_range]
