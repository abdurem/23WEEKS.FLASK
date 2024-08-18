import re
import json
import time
from datetime import datetime, timedelta
from dateutil import parser

def standardize_date(date_string, language="english"):
    if not date_string or date_string.lower() in ["not mentioned", "non mentionnée"]:
        return ""
    try:
        date = parser.parse(date_string, dayfirst=(language == "french"))
        return date.strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return ""

def extract_dates(text):
    date_pattern = r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s*[A-Za-z]+\s*\d{2,4})\b'
    dates = re.findall(date_pattern, text, re.IGNORECASE)
    return [standardize_date(date) for date in dates if standardize_date(date)]

def extract_times(text):
    time_pattern = r'\b(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm|a.m|.p.m)?|\d{1,2}\s*(?:AM|PM|am|pm|.a.m|.p.m)?)\b'
    return re.findall(time_pattern, text, re.IGNORECASE)

def format_time(time_str):
    if not time_str:
        return ''
    
    time_str = time_str.strip().upper()
    time_pattern_12 = r'^(\d{1,2}):(\d{2})\s*(AM|PM)$'
    time_pattern_24 = r'^(\d{1,2}):(\d{2})$'
    
    match_12 = re.match(time_pattern_12, time_str)
    if match_12:
        hour, minute, period = match_12.groups()
        return f'{int(hour)}:{minute} {period}'

    match_24 = re.match(time_pattern_24, time_str)
    if match_24:
        hour, minute = match_24.groups()
        dt = datetime.strptime(f"{hour}:{minute}", "%H:%M")
        return dt.strftime("%I:%M %p")
    
    return time_str

def parse_time_and_recurrence(text):
    recurrence_patterns = {
        'everyday': 'daily',
        'every week': 'weekly',
        'every month': 'monthly',
        'daily': 'daily',
        'weekly': 'weekly',
        'monthly': 'monthly',
    }
    
    hour_pattern = re.search(r'every (\d+)\s*hour', text, re.IGNORECASE)
    minute_pattern = re.search(r'every (\d+)\s*minute', text, re.IGNORECASE)
    
    recurrence = None
    for key, value in recurrence_patterns.items():
        if key in text.lower():
            recurrence = value
            break

    if hour_pattern:
        hours = int(hour_pattern.group(1))
        recurrence = f'every {hours} hours'
    elif minute_pattern:
        minutes = int(minute_pattern.group(1))
        recurrence = f'every {minutes} minutes'
    
    times = extract_times(text)
    normalized_times = [format_time(time) for time in times]
    
    return normalized_times, recurrence

def extract_events_and_associate_times(text):
    event_patterns = [
        r'take my medicine',
        r'check my blood pressure',
        r'meeting',
        r'doctor\'s appointment',
        r'medication',
        r'schedule',
        r'appointment',
        r'visit',
        r'yoga class'
    ]
    
    events = []
    times = extract_times(text)
    
    for pattern in event_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            event_start = match.start()
            event_desc = match.group()
            
            time_match = re.search(r'\b(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm|.a.m|.p.m)?|\d{1,2}\s*(?:AM|PM|am|pm|.a.m|.p.m)?)\b', text[event_start:], re.IGNORECASE)
            time_str = time_match.group(0).strip().upper() if time_match else None
            
            date_match = re.search(r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s*[A-Za-z]+\s*\d{2,4})\b', text[event_start:], re.IGNORECASE)
            date_str = standardize_date(date_match.group(0)) if date_match else None
            
            events.append({
                "description": event_desc.capitalize(),
                "date": date_str,
                "time": format_time(time_str)
            })
    
    return events

def get_default_date(date_str):
    today = datetime.now()
    if date_str.lower() in ["today", "tomorrow"]:
        if date_str.lower() == "today":
            return today.strftime("%d/%m/%Y")
        elif date_str.lower() == "tomorrow":
            tomorrow = today + timedelta(days=1)
            return tomorrow.strftime("%d/%m/%Y")
    return date_str

def get_day_of_week(date_str):
    try:
        date = datetime.strptime(date_str, "%d/%m/%Y")
        return date.strftime("%A")
    except ValueError:
        return ""

def text_to_events(text, language="english"):
    start_time = time.time()
    
    dates = extract_dates(text)
    events = extract_events_and_associate_times(text)
    
    times, recurrence = parse_time_and_recurrence(text)
    
    for event in events:
        if event['time'] in times:
            event['recurrence'] = recurrence
        else:
            event['recurrence'] = recurrence or "once"
    
    for event in events:
        if not event['date']:
            event['date'] = get_default_date("tomorrow")
        if not event['recurrence']:
            event['recurrence'] = "once"
        event['day'] = get_day_of_week(event['date'])

    filtered_events = [event for event in events if event['date'] or event['time']]
    
    result = {
        "events": filtered_events if filtered_events else None,
        "dates": dates if dates else None,
        "times": times if times else None
    }

    total_time = time.time() - start_time
    result["processing_time"] = f"{total_time:.2f} seconds"
    
    return json.dumps(result, ensure_ascii=False, indent=2)
