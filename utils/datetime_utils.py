"""
Dedicated datetime utility library for reliable date/time handling
"""
import datetime
import pytz
from typing import Optional, Tuple, Dict, Any
from dateutil import parser, relativedelta

class DateTimeHandler:
    """Handles all date/time operations with London timezone"""
    
    def __init__(self):
        self.london_tz = pytz.timezone('Europe/London')
        self.now = datetime.datetime.now(self.london_tz)
    
    def get_current_info(self) -> Dict[str, Any]:
        """Get comprehensive current date/time information"""
        return {
            'current_datetime': self.now.strftime('%d %B %Y, %I:%M %p'),
            'current_date': self.now.strftime('%Y-%m-%d'),
            'current_day': self.now.strftime('%A'),
            'timezone': 'Europe/London',
            'today': self.now.strftime('%Y-%m-%d'),
            'tomorrow': (self.now + datetime.timedelta(days=1)).strftime('%Y-%m-%d'),
            'yesterday': (self.now - datetime.timedelta(days=1)).strftime('%Y-%m-%d'),
            'today_day': self.now.strftime('%A'),
            'tomorrow_day': (self.now + datetime.timedelta(days=1)).strftime('%A'),
            'yesterday_day': (self.now - datetime.timedelta(days=1)).strftime('%A')
        }
    
    def parse_relative_date(self, relative_term: str) -> str:
        """Convert relative terms to actual dates"""
        relative_term = relative_term.lower().strip()
        
        if relative_term == 'today':
            return self.now.strftime('%Y-%m-%d')
        elif relative_term == 'tomorrow':
            return (self.now + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        elif relative_term == 'yesterday':
            return (self.now - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        elif relative_term == 'next week':
            return (self.now + datetime.timedelta(weeks=1)).strftime('%Y-%m-%d')
        elif relative_term == 'last week':
            return (self.now - datetime.timedelta(weeks=1)).strftime('%Y-%m-%d')
        else:
            return self.now.strftime('%Y-%m-%d')  # default to today
    
    def parse_natural_language_date(self, text: str) -> Optional[str]:
        """Parse natural language date expressions"""
        try:
            # Try to parse with dateutil
            parsed_date = parser.parse(text, fuzzy=True)
            if parsed_date.tzinfo is None:
                parsed_date = self.london_tz.localize(parsed_date)
            return parsed_date.strftime('%Y-%m-%d')
        except:
            return None
    
    def get_date_range(self, start_date: str, end_date: str = None) -> Tuple[str, str]:
        """Get RFC3339 formatted date range for API calls"""
        # Handle relative dates
        if start_date.lower() in ['today', 'tomorrow', 'yesterday']:
            start_date = self.parse_relative_date(start_date)
        
        if end_date and end_date.lower() in ['today', 'tomorrow', 'yesterday']:
            end_date = self.parse_relative_date(end_date)
        
        # Parse dates
        try:
            if len(start_date) == 10:  # YYYY-MM-DD format
                start_dt = self.london_tz.localize(datetime.datetime.strptime(start_date, '%Y-%m-%d'))
                start_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
            else:
                start_dt = parser.parse(start_date)
                if start_dt.tzinfo is None:
                    start_dt = self.london_tz.localize(start_dt)
            
            if end_date:
                if len(end_date) == 10:  # YYYY-MM-DD format
                    end_dt = self.london_tz.localize(datetime.datetime.strptime(end_date, '%Y-%m-%d'))
                    end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
                else:
                    end_dt = parser.parse(end_date)
                    if end_dt.tzinfo is None:
                        end_dt = self.london_tz.localize(end_dt)
            else:
                # Default to same day
                end_dt = start_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            return start_dt.isoformat(), end_dt.isoformat()
            
        except Exception as e:
            # Fallback to today
            today_start = self.now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start.replace(hour=23, minute=59, second=59, microsecond=999999)
            return today_start.isoformat(), today_end.isoformat()
    
    def format_datetime_for_display(self, dt_str: str) -> str:
        """Format datetime string for nice display"""
        if not dt_str:
            return ''
        try:
            dt = parser.parse(dt_str)
            if dt.tzinfo is None:
                dt = self.london_tz.localize(dt)
            else:
                dt = dt.astimezone(self.london_tz)
            return dt.strftime('%d %B %Y, %I:%M %p')
        except:
            return dt_str
    
    def is_valid_date(self, date_str: str) -> bool:
        """Check if a date string is valid"""
        try:
            if len(date_str) == 10:  # YYYY-MM-DD
                datetime.datetime.strptime(date_str, '%Y-%m-%d')
                return True
            else:
                parser.parse(date_str)
                return True
        except:
            return False

# Global instance
dt_handler = DateTimeHandler() 