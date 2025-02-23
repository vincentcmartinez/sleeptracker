import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from collections import defaultdict
class AppleHealthAnalyzer:
    def __init__(self, file_path):
        self.file_path = file_path
        self.schedule = {}
    def parse_xml(self):
        tree = ET.parse(self.file_path)
        root = tree.getroot()
        sleep_intervals = defaultdict(list)
        cutoff_date = datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        for record in root.findall('.//Record[@type="HKCategoryTypeIdentifierSleepAnalysis"]'):
            start_date = record.get('startDate')
            end_date = record.get('endDate')

            start_dt = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S %z')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S %z')

            if start_dt >= cutoff_date:
                date_str = start_dt.date().isoformat()
                sleep_intervals[date_str].append((start_dt, end_dt))
        sleep_schedule = {}
        for date, intervals in sleep_intervals.items():
            earliest_start = min(intervals, key=lambda x: x[0])[0]
            latest_end = max(intervals, key=lambda x: x[1])[1]
            sleep_schedule[date] = (earliest_start, latest_end)

        self.schedule = sleep_schedule

    def format_sleep_schedule(self):
        formatted_schedule = {}
        for date, (earliest_start, latest_end) in self.schedule.items():
            formatted_schedule[date] = (earliest_start.strftime('%I:%M %p'),latest_end.strftime('%I:%M %p'))
        return formatted_schedule

    def analyze(self):
        self.parse_xml()

        return self.format_sleep_schedule()
