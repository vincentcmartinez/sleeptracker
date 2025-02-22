import json
from collections import defaultdict
from datetime import datetime, timedelta, time
import platform
from typing import Dict, List, Tuple, Any, Optional
from statistics import mean, median
import ijson
import pytz


class BrowserHistoryAnalyzer:
    def __init__(self, file_path: str, timezone: str = "US/Eastern"):
        self.file_path = file_path
        self.timezone = pytz.timezone(timezone)
        self.titles: Dict[str, Dict[str, Any]] = {}
        self.daily_patterns: Dict[str, Dict[str, int]] = {}

    def _normalize_title(self, title: str) -> str:
        title_lower = title.lower()
        if 'youtube' in title_lower:
            return 'YouTube - Combined'
        elif 'google' in title_lower:
            return 'Google - Combined'
        return title

    def _convert_timestamp(self, time_usec: int) -> datetime:
        dt_utc = datetime.utcfromtimestamp(time_usec / 1_000_000)
        dt_utc = dt_utc.replace(tzinfo=pytz.utc)
        return dt_utc.astimezone(self.timezone)

    def _format_datetime(self, dt: datetime) -> str:
        format_str = "%b %#d %Y, %#I:%M%p" if platform.system() == "Windows" else "%b %-d %Y, %-I:%M%p"
        return dt.strftime(format_str)

    def _format_time(self, dt: datetime) -> str:
        return dt.strftime("%I:%M %p")

    def _is_valid_time_gap(self, time_usec1: int, time_usec2: int, minutes: int = 5) -> bool:
        dt1 = datetime.utcfromtimestamp(time_usec1 / 1_000_000)
        dt2 = datetime.utcfromtimestamp(time_usec2 / 1_000_000)
        return dt2 - dt1 > timedelta(minutes=minutes)

    def analyze_daily_patterns(self, cutoff_timestamp: Optional[int] = None) -> None:
        self.daily_patterns = {}

        with open(self.file_path, encoding='utf-8') as file:
            for record in ijson.items(file, "Browser History.item"):
                if cutoff_timestamp and int(record["time_usec"]) < cutoff_timestamp:
                    break

                timestamp = record["time_usec"]
                dt = self._convert_timestamp(timestamp)
                date_str = dt.date().isoformat()

                if date_str not in self.daily_patterns:
                    self.daily_patterns[date_str] = {
                        'first_activity': timestamp,
                        'last_activity': timestamp
                    }
                else:
                    if timestamp < self.daily_patterns[date_str]['first_activity']:
                        self.daily_patterns[date_str]['first_activity'] = timestamp
                    if timestamp > self.daily_patterns[date_str]['last_activity']:
                        self.daily_patterns[date_str]['last_activity'] = timestamp

    def process_daily_timestamps(self) -> Dict[str, Tuple[str, str]]:
        daily_timestamps = {}

        with open(self.file_path, encoding='utf-8') as file:
            for record in ijson.items(file, "Browser History.item"):
                timestamp = record["time_usec"]
                dt = self._convert_timestamp(timestamp)
                date_str = dt.date().isoformat()

                if date_str not in daily_timestamps:
                    daily_timestamps[date_str] = {
                        'first_timestamp': timestamp,
                        'last_timestamp': timestamp
                    }
                else:
                    if timestamp < daily_timestamps[date_str]['first_timestamp']:
                        daily_timestamps[date_str]['first_timestamp'] = timestamp
                    if timestamp > daily_timestamps[date_str]['last_timestamp']:
                        daily_timestamps[date_str]['last_timestamp'] = timestamp

        formatted_daily_timestamps = {}
        for date, timestamps in daily_timestamps.items():
            first_dt = self._convert_timestamp(timestamps['first_timestamp'])
            last_dt = self._convert_timestamp(timestamps['last_timestamp'])
            formatted_daily_timestamps[date] = (
                self._format_datetime(first_dt),
                self._format_datetime(last_dt)
            )

        return formatted_daily_timestamps
    def calculate_sleep_schedule(self, min_gap_hours: int = 6) -> Dict[str, Any]:
        if not self.daily_patterns:
            self.analyze_daily_patterns()

        sleep_times = []
        wake_times = []
        sleep_durations = []

        sorted_dates = sorted(self.daily_patterns.keys())

        for i in range(len(sorted_dates) - 1):
            current_date = sorted_dates[i]
            next_date = sorted_dates[i + 1]

            last_activity = self._convert_timestamp(self.daily_patterns[current_date]['last_activity'])
            next_activity = self._convert_timestamp(self.daily_patterns[next_date]['first_activity'])

            gap_duration = next_activity - last_activity
            if timedelta(hours=min_gap_hours) <= gap_duration <= timedelta(hours=16):
                sleep_times.append(last_activity.time())
                wake_times.append(next_activity.time())
                sleep_durations.append(gap_duration.total_seconds() / 3600)

        def average_time(time_list: List[time]) -> time:
            minutes = [(t.hour * 60 + t.minute) for t in time_list]
            for i in range(len(minutes)):
                if i > 0 and minutes[i] < minutes[i - 1] - 720:
                    minutes[i] += 1440
            avg_minutes = int(mean(minutes))
            return time(hour=(avg_minutes // 60) % 24, minute=avg_minutes % 60)

        return {
            "average_sleep_time": self._format_time(datetime.combine(datetime.today(), average_time(sleep_times))),
            "average_wake_time": self._format_time(datetime.combine(datetime.today(), average_time(wake_times))),
            "median_sleep_duration": round(median(sleep_durations), 2),
            "days_analyzed": len(sorted_dates),
            "sleep_patterns_found": len(sleep_times),
            "earliest_wake_time": self._format_time(datetime.combine(datetime.today(), min(wake_times))),
            "latest_wake_time": self._format_time(datetime.combine(datetime.today(), max(wake_times))),
            "earliest_sleep_time": self._format_time(datetime.combine(datetime.today(), min(sleep_times))),
            "latest_sleep_time": self._format_time(datetime.combine(datetime.today(), max(sleep_times)))
        }

    def process_history(self, cutoff_timestamp: Optional[int] = None) -> None:
        with open(self.file_path, encoding='utf-8') as file:
            for record in ijson.items(file, "Browser History.item"):
                if cutoff_timestamp and int(record["time_usec"]) < cutoff_timestamp:
                    break

                normalized_title = self._normalize_title(record['title'])
                current_time = record['time_usec']

                if normalized_title in self.titles:
                    if self._is_valid_time_gap(current_time, self.titles[normalized_title]['latest']):
                        self.titles[normalized_title]['count'] += 1
                else:
                    self.titles[normalized_title] = {'count': 1}

                self.titles[normalized_title]['latest'] = current_time

    def get_filtered_titles(self, min_count: int = 10) -> Dict[str, Dict[str, Any]]:
        return {title: data for title, data in self.titles.items()
                if data['count'] >= min_count}

    def get_sorted_titles(self, min_count: int = 10) -> List[Dict[str, Any]]:
        filtered = self.get_filtered_titles(min_count)
        title_list = [{"name": title, **data} for title, data in filtered.items()]
        return sorted(title_list, key=lambda d: d['count'], reverse=True)

    def get_last_sites_per_day(self) -> Tuple[Dict[str, Tuple[int, str]], List[Tuple[str, int]]]:
        last_site_per_day = {}
        site_count = defaultdict(int)

        with open(self.file_path, encoding='utf-8') as file:
            for record in ijson.items(file, "Browser History.item"):
                timestamp_usec = record["time_usec"]
                title = self._normalize_title(record["title"])
                date_str = self._convert_timestamp(timestamp_usec).date()

                if date_str not in last_site_per_day or timestamp_usec > last_site_per_day[date_str][0]:
                    last_site_per_day[date_str] = (timestamp_usec, title)

        for _, title in last_site_per_day.values():
            site_count[title] += 1

        sorted_frequencies = sorted(site_count.items(), key=lambda x: x[1], reverse=True)
        return last_site_per_day, sorted_frequencies

    def save_results(self, filtered_output: str = "output.json",
                     sorted_output: str = "sorted.json",
                     patterns_output: str = "sleep_patterns.json",
                     min_count: int = 10) -> None:
        filtered_data = self.get_filtered_titles(min_count)
        sorted_data = self.get_sorted_titles(min_count)
        sleep_data = self.calculate_sleep_schedule()

        outputs = [
            (filtered_output, filtered_data),
            (sorted_output, sorted_data),
            (patterns_output, sleep_data)
        ]

        for filename, data in outputs:
            with open(filename, "w+") as file:
                json.dump(data, file, indent=4)


def main():
    file_path = "C:/Users/Vincent/Downloads/History.json"
    analyzer = BrowserHistoryAnalyzer(file_path)

    analyzer.process_history(cutoff_timestamp=1735707600)
    analyzer.analyze_daily_patterns(cutoff_timestamp=1735707600)

    sleep_schedule = analyzer.calculate_sleep_schedule()
    print("\nAnalyzed Sleep Schedule:")
    for key, value in sleep_schedule.items():
        print(f"{key.replace('_', ' ').title()}: {value}")

    analyzer.save_results()

    _, site_frequencies = analyzer.get_last_sites_per_day()
    print("\nFrequency of sites being last visited:")
    for title, count in site_frequencies:
        if count > 1:
            print(f"{title}: {count}")


if __name__ == "__main__":
    main()