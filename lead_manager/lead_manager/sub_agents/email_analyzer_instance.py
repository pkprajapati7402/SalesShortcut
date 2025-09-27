"""
Email Analyzer instance for the Lead Manager.
"""

from .email_analyzer import EmailAnalyzer
from .calendar_organizer_agent import calendar_organizer_agent

# Create the email analyzer instance with calendar organizer as dependency
email_analyzer = EmailAnalyzer(
    name="EmailAnalyzer",
    calendar_organizer_agent=calendar_organizer_agent,
    output_key="meeting_result"  
)