from utils.calendar_api import GoogleCalendarAPI
from utils.datetime_utils import dt_handler
from langchain.tools import tool
from typing import List
from datetime import datetime, timedelta
import pytz
import time

LONDON_TZ = 'Europe/London'

class CalendarTool:
    def __init__(self):
        self.api = GoogleCalendarAPI()
        self.calendar_tool_list = self._setup_tools()

    def _setup_tools(self) -> List:
        @tool
        def list_calendars(show_ids: bool = False) -> str:
            """List all user calendars (categories) with their names. Set show_ids=True to include IDs. Use this to help the user pick a calendar for further actions."""
            try:
                calendars = self.api.get_user_calendars()
                if not calendars:
                    return 'No calendars found. Please check your Google Calendar permissions.'
                
                if show_ids:
                    result = '**Your Calendars:**\n\n'
                    for cal in calendars:
                        name = cal.get('summary', '(No Name)')
                        cal_id = cal.get('id', 'No ID')
                        access_role = cal.get('accessRole', 'unknown')
                        result += f"📅 **{name}**\n   ID: `{cal_id}`\n   Access: {access_role}\n\n"
                else:
                    result = '**Your Calendars:**\n\n'
                    for cal in calendars:
                        name = cal.get('summary', '(No Name)')
                        result += f"📅 **{name}**\n"
                    result += f"\n*Found {len(calendars)} calendar(s). Use 'list_calendars' with show_ids=True to see calendar IDs for specific operations.*"
                
                return result
            except Exception as e:
                return f'❌ Error accessing calendars: {str(e)}. Please check your Google Calendar permissions.'

        @tool
        def smart_event_search(description: str, calendar_id: str = 'primary', search_recent: bool = True) -> str:
            """Intelligently search for events based on vague descriptions. This tool is perfect for finding events when users mention them without specific IDs. Search in recent/upcoming events by default."""
            try:
                # Determine search time range based on context
                if search_recent:
                    # Search in recent past and upcoming events (last 7 days + next 30 days)
                    time_min, time_max = dt_handler.get_date_range(
                        (dt_handler.now - timedelta(days=7)).strftime('%Y-%m-%d'),
                        (dt_handler.now + timedelta(days=30)).strftime('%Y-%m-%d')
                    )
                else:
                    # Search in all events
                    time_min, time_max = None, None
                
                events = self.api.get_events(calendar_id, time_min, time_max)
                
                # Smart keyword extraction and matching
                description_lower = description.lower()
                keywords = description_lower.split()
                
                # Enhanced matching logic
                matches = []
                for ev in events:
                    summary = ev.get('summary', '').lower()
                    desc = ev.get('description', '').lower()
                    location = ev.get('location', '').lower()
                    
                    # Check for exact matches first
                    if description_lower in summary or description_lower in desc:
                        matches.append((ev, 3))  # High priority
                    # Check for keyword matches
                    elif any(keyword in summary or keyword in desc or keyword in location for keyword in keywords if len(keyword) > 2):
                        matches.append((ev, 2))  # Medium priority
                    # Check for partial matches
                    elif any(keyword in summary or keyword in desc for keyword in keywords if len(keyword) > 3):
                        matches.append((ev, 1))  # Low priority
                
                # Sort by priority and recency
                matches.sort(key=lambda x: (x[1], x[0].get('start', {}).get('dateTime', '')), reverse=True)
                matches = [ev for ev, priority in matches]
                
                if not matches:
                    return f'🔍 No events found matching "{description}" in calendar "{calendar_id}". Try using more specific terms or check a different calendar.'
                
                result = f"🔍 **Found {len(matches)} event(s) matching '{description}' in calendar '{calendar_id}':**\n\n"
                
                for i, ev in enumerate(matches[:5], 1):  # Show top 5 matches
                    summary = ev.get('summary', '(No Title)')
                    start = dt_handler.format_datetime_for_display(ev.get('start', {}).get('dateTime', ev.get('start', {}).get('date', '')))
                    end = dt_handler.format_datetime_for_display(ev.get('end', {}).get('dateTime', ev.get('end', {}).get('date', '')))
                    location = ev.get('location', '')
                    
                    result += f"{i}. 📅 **{summary}**\n"
                    result += f"   🕐 {start} to {end}\n"
                    if location:
                        result += f"   📍 {location}\n"
                    result += f"   🆔 Event ID: `{ev.get('id', '')}`\n\n"
                
                if len(matches) > 5:
                    result += f"*... and {len(matches) - 5} more events. Please be more specific to narrow down the results.*\n"
                
                result += "**💡 Tip:** Use the event ID to perform specific actions like update, move, or delete."
                return result
                
            except Exception as e:
                return f'❌ Error searching events: {str(e)}.'

        @tool
        def list_events(calendar_id: str = 'primary', date: str = None, time_min: str = None, time_max: str = None) -> str:
            """List events for a calendar. You can specify a date (YYYY-MM-DD) or relative term (today/tomorrow/yesterday), or use time_min/time_max for custom ranges. Defaults to today if no date is given."""
            try:
                # Use datetime handler for reliable date parsing
                if date:
                    if date.lower() in ['today', 'tomorrow', 'yesterday']:
                        actual_date = dt_handler.parse_relative_date(date)
                        time_min, time_max = dt_handler.get_date_range(actual_date)
                    elif dt_handler.is_valid_date(date):
                        time_min, time_max = dt_handler.get_date_range(date)
                    else:
                        return f'❌ Invalid date format: {date}. Please use YYYY-MM-DD or relative terms like "today", "tomorrow".'
                elif not time_min or not time_max:
                    # Default to today
                    time_min, time_max = dt_handler.get_date_range('today')
                
                events = self.api.get_events(calendar_id, time_min, time_max)
                if not events:
                    date_display = dt_handler.format_datetime_for_display(time_min)[:11] if time_min else "the specified period"
                    return f'No events found for {date_display} in calendar "{calendar_id}".'
                
                date_display = dt_handler.format_datetime_for_display(time_min)[:11] if time_min else "the specified period"
                result = f"**Events for {date_display} in calendar '{calendar_id}':**\n\n"
                
                for ev in events:
                    summary = ev.get('summary', '(No Title)')
                    start = dt_handler.format_datetime_for_display(ev.get('start', {}).get('dateTime', ev.get('start', {}).get('date', '')))
                    end = dt_handler.format_datetime_for_display(ev.get('end', {}).get('dateTime', ev.get('end', {}).get('date', '')))
                    desc = ev.get('description', '')
                    location = ev.get('location', '')
                    
                    result += f"📅 **{summary}**\n"
                    result += f"   🕐 {start} to {end}\n"
                    if location:
                        result += f"   📍 {location}\n"
                    if desc:
                        result += f"   📝 {desc}\n"
                    result += f"   🆔 Event ID: `{ev.get('id', '')}`\n\n"
                
                return result
            except Exception as e:
                return f'❌ Error accessing events: {str(e)}. Please check the calendar ID and permissions.'

        @tool
        def search_events_by_keyword(calendar_id: str = 'primary', keyword: str = '', date: str = None, time_min: str = None, time_max: str = None) -> str:
            """Search for events in a calendar by keyword in the title or description, optionally in a date range. You can specify a date (YYYY-MM-DD) or relative term (today/tomorrow/yesterday). This is the primary tool for finding events when users mention them vaguely."""
            try:
                # Use datetime handler for reliable date parsing
                if date:
                    if date.lower() in ['today', 'tomorrow', 'yesterday']:
                        actual_date = dt_handler.parse_relative_date(date)
                        time_min, time_max = dt_handler.get_date_range(actual_date)
                    elif dt_handler.is_valid_date(date):
                        time_min, time_max = dt_handler.get_date_range(date)
                    else:
                        return f'❌ Invalid date format: {date}. Please use YYYY-MM-DD or relative terms like "today", "tomorrow".'
                
                events = self.api.get_events(calendar_id, time_min, time_max)
                
                # Enhanced keyword matching
                keyword_lower = keyword.lower()
                matches = []
                
                for ev in events:
                    summary = ev.get('summary', '').lower()
                    desc = ev.get('description', '').lower()
                    location = ev.get('location', '').lower()
                    
                    # Check for matches in title, description, or location
                    if (keyword_lower in summary or 
                        keyword_lower in desc or 
                        keyword_lower in location):
                        matches.append(ev)
                
                if not matches:
                    date_info = f" for {date}" if date else ""
                    return f'🔍 No events found with keyword "{keyword}" in calendar "{calendar_id}"{date_info}. Try using different keywords or check a different time period.'
                
                result = f"🔍 **Found {len(matches)} event(s) matching '{keyword}' in calendar '{calendar_id}':**\n\n"
                
                for ev in matches:
                    summary = ev.get('summary', '(No Title)')
                    start = dt_handler.format_datetime_for_display(ev.get('start', {}).get('dateTime', ev.get('start', {}).get('date', '')))
                    end = dt_handler.format_datetime_for_display(ev.get('end', {}).get('dateTime', ev.get('end', {}).get('date', '')))
                    location = ev.get('location', '')
                    
                    result += f"📅 **{summary}**\n"
                    result += f"   🕐 {start} to {end}\n"
                    if location:
                        result += f"   📍 {location}\n"
                    result += f"   🆔 Event ID: `{ev.get('id','')}`\n\n"
                
                result += "**💡 Tip:** Use the event ID to perform specific actions like update, move, or delete."
                return result
                
            except Exception as e:
                return f'❌ Error searching events: {str(e)}.'

        @tool
        def get_event_details(calendar_id: str = 'primary', event_id: str = '') -> str:
            """Get full details for a specific event by event_id. Returns a formatted summary."""
            if not event_id:
                return '❌ Please provide an event ID.'
            try:
                ev = self.api.get_event(calendar_id, event_id)
                summary = ev.get('summary', '(No Title)')
                start = dt_handler.format_datetime_for_display(ev.get('start', {}).get('dateTime', ev.get('start', {}).get('date', '')))
                end = dt_handler.format_datetime_for_display(ev.get('end', {}).get('dateTime', ev.get('end', {}).get('date', '')))
                desc = ev.get('description', '')
                location = ev.get('location', '')
                return f"**Event Details**\n- **Title:** {summary}\n- **Date:** {start} to {end}\n- **Description:** {desc}\n- **Location:** {location}\n- **Event ID:** {ev.get('id','')}\n"
            except Exception as e:
                return f'❌ Error getting event details: {str(e)}.'

        @tool
        def move_event(calendar_id: str, event_id: str, new_start: str, new_end: str) -> str:
            """Move/reschedule an event to a new time. Provide event_id, new_start, and new_end in RFC3339 format. Returns a confirmation."""
            try:
                ev = self.api.get_event(calendar_id, event_id)
                ev['start']['dateTime'] = new_start
                ev['start']['timeZone'] = LONDON_TZ
                ev['end']['dateTime'] = new_end
                ev['end']['timeZone'] = LONDON_TZ
                updated = self.api.update_event(calendar_id, event_id, ev)
                return f"✅ Event '{updated.get('summary','(No Title)')}' moved to {dt_handler.format_datetime_for_display(new_start)} - {dt_handler.format_datetime_for_display(new_end)}."
            except Exception as e:
                return f'❌ Error moving event: {str(e)}.'

        @tool
        def get_events_duration(calendar_id: str = 'primary', date: str = None, time_min: str = None, time_max: str = None) -> str:
            """Calculate the total duration of all events in a calendar for a given date or time range. You can specify a date (YYYY-MM-DD) or relative term (today/tomorrow/yesterday)."""
            try:
                # Use datetime handler for reliable date parsing
                if date:
                    if date.lower() in ['today', 'tomorrow', 'yesterday']:
                        actual_date = dt_handler.parse_relative_date(date)
                        time_min, time_max = dt_handler.get_date_range(actual_date)
                    elif dt_handler.is_valid_date(date):
                        time_min, time_max = dt_handler.get_date_range(date)
                    else:
                        return f'❌ Invalid date format: {date}. Please use YYYY-MM-DD or relative terms like "today", "tomorrow".'
                
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
                date_display = dt_handler.format_datetime_for_display(time_min)[:11] if time_min else "the specified period"
                return f"📊 **Time Summary for {date_display}:**\n- Total scheduled time: {hours} hours {minutes} minutes\n- Number of events: {len(events)}"
            except Exception as e:
                return f'❌ Error calculating duration: {str(e)}.'

        @tool
        def get_free_busy(calendar_id: str = 'primary', date: str = None) -> str:
            """Show free/busy slots for a given day. You can specify a date (YYYY-MM-DD) or relative term (today/tomorrow/yesterday). Returns a formatted list of busy slots."""
            try:
                # Use datetime handler for reliable date parsing
                if date:
                    if date.lower() in ['today', 'tomorrow', 'yesterday']:
                        actual_date = dt_handler.parse_relative_date(date)
                    elif dt_handler.is_valid_date(date):
                        actual_date = date
                    else:
                        return f'❌ Invalid date format: {date}. Please use YYYY-MM-DD or relative terms like "today", "tomorrow".'
                else:
                    actual_date = dt_handler.get_current_info()['today']
                
                time_min, time_max = dt_handler.get_date_range(actual_date)
                events = self.api.get_events(calendar_id, time_min, time_max)
                
                if not events:
                    date_display = dt_handler.format_datetime_for_display(time_min)[:11]
                    return f'✅ You are free all day on {date_display} in calendar "{calendar_id}".'
                
                date_display = dt_handler.format_datetime_for_display(time_min)[:11]
                result = f"📅 **Busy slots for {date_display} in calendar '{calendar_id}':**\n\n"
                
                for ev in events:
                    ev_start = dt_handler.format_datetime_for_display(ev.get('start', {}).get('dateTime', ev.get('start', {}).get('date', '')))
                    ev_end = dt_handler.format_datetime_for_display(ev.get('end', {}).get('dateTime', ev.get('end', {}).get('date', '')))
                    summary = ev.get('summary', '(No Title)')
                    result += f"🕐 {ev_start} to {ev_end} - {summary}\n"
                
                return result
            except Exception as e:
                return f'❌ Error getting free/busy info: {str(e)}.'

        @tool
        def quick_add_event(calendar_id: str = 'primary', text: str = '') -> str:
            """Quickly add an event using a single natural language string (e.g., 'Lunch with Bob at 1pm Friday'). Returns a confirmation."""
            # This is a placeholder; Google Calendar API has a quickAdd endpoint, but not in v3 Python client. We'll parse with LLM and call create_event.
            return f"Quick add: {text}. Please use the create_event tool for full details."

        @tool
        def create_event(calendar_id: str, summary: str, start: str, end: str, description: str = "", location: str = "", minimal: bool = False) -> str:
            """Create an event in a calendar. Dates in RFC3339 format, always using Europe/London time zone. Set minimal=True for a short confirmation message. Always confirm with a detailed, nicely formatted summary."""
            try:
                event = {
                    'summary': summary,
                    'location': location,
                    'description': description,
                    'start': {'dateTime': start, 'timeZone': LONDON_TZ},
                    'end': {'dateTime': end, 'timeZone': LONDON_TZ},
                }
                created = self.api.create_event(calendar_id, event)
                if minimal:
                    return f"✅ Event '{created.get('summary','(No Title)')}' created."
                summary_text = f"**✅ Event Created Successfully!**\n\n- **Title:** {created.get('summary','(No Title)')}\n- **Date:** {dt_handler.format_datetime_for_display(created['start'].get('dateTime',''))} to {dt_handler.format_datetime_for_display(created['end'].get('dateTime',''))} (Europe/London)\n- **Description:** {created.get('description','')}\n- **Location:** {created.get('location','')}\n- **Calendar:** {calendar_id}\n- **Event ID:** {created.get('id','')}\n"
                return summary_text
            except Exception as e:
                return f'❌ Error creating event: {str(e)}.'

        @tool
        def update_event(calendar_id: str, event_id: str, summary: str = None, start: str = None, end: str = None, description: str = None, location: str = None, minimal: bool = False) -> str:
            """Update an event in a calendar. Only provided fields will be updated. Dates in RFC3339, Europe/London. Set minimal=True for a short confirmation message. Always confirm with a detailed, nicely formatted summary."""
            try:
                event = self.api.get_event(calendar_id, event_id)
                if summary: event['summary'] = summary
                if start: event['start']['dateTime'] = start; event['start']['timeZone'] = LONDON_TZ
                if end: event['end']['dateTime'] = end; event['end']['timeZone'] = LONDON_TZ
                if description: event['description'] = description
                if location: event['location'] = location
                updated = self.api.update_event(calendar_id, event_id, event)
                if minimal:
                    return f"✅ Event '{updated.get('summary','(No Title)')}' updated."
                return f"✅ Event updated: {updated.get('summary','(No Title)')} ({dt_handler.format_datetime_for_display(updated['start'].get('dateTime',''))} to {dt_handler.format_datetime_for_display(updated['end'].get('dateTime',''))})"
            except Exception as e:
                return f'❌ Error updating event: {str(e)}.'

        @tool
        def delete_event(calendar_id: str, event_id: str, minimal: bool = False) -> str:
            """Delete a single event from a calendar by event_id. Set minimal=True for a short confirmation message. Use this when the user specifies a specific event to delete."""
            try:
                # Add timeout protection
                start_time = time.time()
                timeout = 30  # 30 seconds timeout
                
                self.api.delete_event(calendar_id, event_id)
                
                # Check if operation took too long
                if time.time() - start_time > timeout:
                    return f"⚠️ Event deletion completed but took longer than expected. Event {event_id} has been deleted from {calendar_id}."
                
                if minimal:
                    return f"✅ Event deleted."
                return f"✅ Event {event_id} deleted from {calendar_id}"
            except Exception as e:
                return f'❌ Error deleting event: {str(e)}. Please check the event ID and calendar permissions.'

        @tool
        def delete_events_in_range(calendar_id: str = 'primary', date: str = None, time_min: str = None, time_max: str = None) -> str:
            """Delete all events in a calendar between time_min and time_max (RFC3339 format) or for a specific date. You can specify a date (YYYY-MM-DD) or relative term (today/tomorrow/yesterday). Use this for requests like 'delete all events between 2-7pm from tomorrow onwards'. Always confirm with a nicely formatted summary of deleted events."""
            try:
                # Use datetime handler for reliable date parsing
                if date:
                    if date.lower() in ['today', 'tomorrow', 'yesterday']:
                        actual_date = dt_handler.parse_relative_date(date)
                        time_min, time_max = dt_handler.get_date_range(actual_date)
                    elif dt_handler.is_valid_date(date):
                        time_min, time_max = dt_handler.get_date_range(date)
                    else:
                        return f'❌ Invalid date format: {date}. Please use YYYY-MM-DD or relative terms like "today", "tomorrow".'
                elif not time_min or not time_max:
                    return '❌ Please specify a valid time range or date.'
                
                # Add timeout protection for batch operations
                start_time = time.time()
                timeout = 60  # 60 seconds timeout for batch operations
                
                deleted_ids = self.api.batch_delete_events(calendar_id, time_min, time_max)
                
                # Check if operation took too long
                if time.time() - start_time > timeout:
                    return f"⚠️ Batch deletion completed but took longer than expected. {len(deleted_ids)} events deleted from calendar '{calendar_id}'."
                
                if not deleted_ids:
                    date_display = dt_handler.format_datetime_for_display(time_min)[:11] if time_min else "the specified range"
                    return f'No events found to delete in {date_display} for calendar "{calendar_id}".'
                
                date_display = dt_handler.format_datetime_for_display(time_min)[:11] if time_min else "the specified range"
                result = f"🗑️ **Deleted {len(deleted_ids)} event(s) from calendar '{calendar_id}' for {date_display}:**\n\n"
                for eid in deleted_ids:
                    result += f"- Event ID: `{eid}`\n"
                return result
            except Exception as e:
                return f'❌ Error deleting events: {str(e)}. Please check the calendar ID and permissions.'

        return [list_calendars, smart_event_search, list_events, search_events_by_keyword, get_event_details, move_event, get_events_duration, get_free_busy, quick_add_event, create_event, update_event, delete_event, delete_events_in_range]
