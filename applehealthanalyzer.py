import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from collections import defaultdict
class AppleHealthAnalyzer:
    def __init__(self, file_path):
        self.file_path = file_path
        self.schedule = {}
    def parse_xml(self):
        # Parse the XML file
        tree = ET.parse(self.file_path)
        root = tree.getroot()

        # Dictionary to hold sleep intervals grouped by date
        sleep_intervals = defaultdict(list)

        # Define the cutoff date
        cutoff_date = datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

        # Extract sleep analysis records
        for record in root.findall('.//Record[@type="HKCategoryTypeIdentifierSleepAnalysis"]'):
            start_date = record.get('startDate')
            end_date = record.get('endDate')

            # Convert start_date and end_date to datetime objects
            start_dt = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S %z')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S %z')

            # Filter records to only include those after 2020
            if start_dt >= cutoff_date:
                # Group by date
                date_str = start_dt.date().isoformat()
                sleep_intervals[date_str].append((start_dt, end_dt))

        # Dictionary to hold the earliest start and latest end times per date
        sleep_schedule = {}

        # Process each date's sleep intervals
        for date, intervals in sleep_intervals.items():
            earliest_start = min(intervals, key=lambda x: x[0])[0]
            latest_end = max(intervals, key=lambda x: x[1])[1]
            sleep_schedule[date] = (earliest_start, latest_end)

        self.schedule = sleep_schedule

    def format_sleep_schedule(self):
        formatted_schedule = []
        for date, (earliest_start, latest_end) in self.schedule.items():
            formatted_schedule.append({
                'date': date,
                'earliest_start': earliest_start.strftime('%Y-%m-%d %H:%M:%S %z'),
                'latest_end': latest_end.strftime('%Y-%m-%d %H:%M:%S %z')
            })
        return formatted_schedule

    def analyze(self):
        self.parse_xml()

        return self.format_sleep_schedule()
    # Example usage
file_path = 'C:/Users/Vincent/Downloads/export.xml'
ah = AppleHealthAnalyzer(file_path)
sleep_schedule = ah.parse_xml()
formatted_schedule = ah.format_sleep_schedule()

# Print the formatted sleep schedule
for entry in formatted_schedule:
    print(f"Date: {entry['date']}, Earliest sleep: {entry['earliest_start']}, Latest wake: {entry['latest_end']}")