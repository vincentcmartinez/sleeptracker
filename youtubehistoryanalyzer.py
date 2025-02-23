from collections import defaultdict
from datetime import datetime

from bs4 import BeautifulSoup
from io import StringIO
import re


class YoutubeHistoryAnalyzer:
    def __init__(self, filepath):
        self.BUFFER_SIZE = 1024 * 1024
        self.date_time_pattern = re.compile(r'\b\w+\s\d{1,2},\s\d{4},\s\d{1,2}:\d{2}:\d{2}\s\w+\s\w+\b')
        self.stamps = []
        self.filepath = filepath
        self.schedules = {}

    def process_buffer(self, buffer):
        with StringIO(buffer) as buffer_io:
            soup = BeautifulSoup(buffer_io, 'lxml')
            content_cells = soup.find_all('div', class_='content-cell mdl-cell mdl-cell--6-col mdl-typography--body-1')
            for cell in content_cells:
                timestamp = cell.contents[len(cell.contents) - 1].text
                if not str(timestamp).startswith("<a"):
                    self.stamps.append(str(timestamp).replace('\u202f', ' '))

    def process_html_file(self):
        with open(self.filepath, 'r', encoding='utf-8') as file:
            buffer = ''
            while True:
                chunk = file.read(self.BUFFER_SIZE)
                if not chunk:
                    break
                buffer += chunk
                self.process_buffer(buffer)
                buffer = ''

    def process_daily_timestamps(self):
        grouped_by_date = defaultdict(list)
        for timestamp in self.stamps:
            timestamp_no_tz = timestamp.rsplit(' ', 1)[0]
            try:
                dt = datetime.strptime(timestamp_no_tz, '%b %d, %Y, %I:%M:%S %p')
            except ValueError:
                continue
            date_str = dt.strftime('%Y-%m-%d')
            time_str = dt.strftime('%I:%M:%S %p')
            if dt > datetime.strptime("01 01, 2025, 12:00:00 AM", '%m %d, %Y, %I:%M:%S %p'):
                grouped_by_date[date_str].append(time_str)

        result = {}

        for date, ts_list in grouped_by_date.items():
            sorted_ts_list = sorted(ts_list, key=lambda x: datetime.strptime(x, '%I:%M:%S %p'))
            earliest = sorted_ts_list[0]
            latest = sorted_ts_list[-1]
            result[date] = (earliest, latest)

        sorted_result = sorted(result.items())
        self.schedules = sorted_result
        return self.schedules
    def normalize_for_analysis(self):
        ret = {}
        for schedule in self.schedules:
            new1 = schedule[1][0][:5] + schedule[1][0][8:]
            new2 = schedule[1][1][:5] + schedule[1][1][8:]
            ret[schedule[0]] = (new1,new2)
        return ret
    def analyze(self):
        self.process_html_file()
        self.process_daily_timestamps()
        return self.normalize_for_analysis()
