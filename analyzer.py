import sys

from applehealthanalyzer import AppleHealthAnalyzer
from browserhistoryanalyzer import BrowserHistoryAnalyzer
from youtubehistoryanalyzer import YoutubeHistoryAnalyzer
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from datetime import datetime, time
import numpy as np
from scipy.stats import ttest_ind
def parse_timestamps(data):
    parsed_data = {}
    for date, (wake, sleep) in data.items():
        wake_time = datetime.strptime(wake, "%I:%M %p").time()
        sleep_time = datetime.strptime(sleep, "%I:%M %p").time()
        if sleep_time < wake_time:
            sleep_time = (sleep_time.hour + 24, sleep_time.minute)
        else:
            sleep_time = (sleep_time.hour, sleep_time.minute)
        sleep_time = time(sleep_time[0] % 24, sleep_time[1])

        parsed_data[date] = (wake_time, sleep_time)
    return parsed_data

def align_datasets(yt_data, google_data, apple_data):
    all_dates = set(yt_data.keys()) | set(google_data.keys()) | set(apple_data.keys())
    aligned_data = {date: (None, None) for date in all_dates}

    for date in all_dates:
        yt_entry = yt_data.get(date, (None, None))
        google_entry = google_data.get(date, (None, None))
        apple_entry = apple_data.get(date, (None, None))

        aligned_data[date] = {
            'youtube': yt_entry,
            'chrome': google_entry,
            'apple': apple_entry
        }

    return aligned_data

def estimate_average_sleep_schedule(data, mode="apple"):
    total_start = 0
    total_end = 0
    count = 0

    for date, entry in data.items():
        start, end = entry[mode]
        if start is not None and end is not None:
            start_hour = start.hour + start.minute / 60
            end_hour = end.hour + end.minute / 60
            if end_hour < start_hour:
                end_hour += 24

            total_start += start_hour
            total_end += end_hour
            count += 1

    if count == 0:
        return None, None

    avg_start = total_start / count
    avg_end = total_end / count

    return avg_start, avg_end

def calculate_accuracy(aligned_data, avg_sleep_schedule):
    accuracy = {'youtube': [], 'chrome': []}

    for date, entry in aligned_data.items():
        apple_start, apple_end = entry['apple']
        if apple_start is None or apple_end is None:
            continue

        for source in ['youtube', 'chrome']:
            source_start, source_end = entry[source]
            if source_start is None or source_end is None:
                continue
            apple_start_hour = apple_start.hour + apple_start.minute / 60
            apple_end_hour = apple_end.hour + apple_end.minute / 60

            source_start_hour = source_start.hour + source_start.minute / 60
            source_end_hour = source_end.hour + source_end.minute / 60

            apple_start_diff = abs(apple_start_hour - avg_sleep_schedule[0])
            apple_end_diff = abs(apple_end_hour - avg_sleep_schedule[1])

            source_start_diff = abs(source_start_hour - avg_sleep_schedule[0])
            source_end_diff = abs(source_end_hour - avg_sleep_schedule[1])

            accuracy_diff = (apple_start_diff + apple_end_diff) - (source_start_diff + source_end_diff)
            accuracy[source].append(accuracy_diff)

    return accuracy

def calculate_statistics(accuracy):
    stats = {}
    for source, diffs in accuracy.items():
        stats[source] = {
            'mean': np.mean(diffs),
            'std': np.std(diffs),
            'min': np.min(diffs),
            'max': np.max(diffs)
        }
    return stats

def plot_start_end_times(aligned_data):
    dates = []
    start_times = {'youtube': [], 'chrome': [], 'apple': []}
    end_times = {'youtube': [], 'chrome': [], 'apple': []}

    for date, entry in aligned_data.items():
        dates.append(date)
        for source in ['youtube', 'chrome', 'apple']:
            start, end = entry[source]
            if start is not None:
                start_times[source].append(start.hour + start.minute / 60)
            else:
                start_times[source].append(None)
            if end is not None:
                end_times[source].append(end.hour + end.minute / 60)
            else:
                end_times[source].append(None)

    df_start = pd.DataFrame(start_times, index=dates)
    df_end = pd.DataFrame(end_times, index=dates)

    fig, ax = plt.subplots(2, 1, figsize=(14, 12), sharex=True)

    df_start.plot(ax=ax[0], marker='o')
    ax[0].set_title('Start Times Across All Dates')
    ax[0].set_ylabel('Time (24-hour format)')
    ax[0].legend(loc='upper right')

    df_end.plot(ax=ax[1], marker='o')
    ax[1].set_title('End Times Across All Dates')
    ax[1].set_ylabel('Time (24-hour format)')
    ax[1].legend(loc='upper right')

    plt.xlabel('Date')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
def main():
    args = sys.argv
    if len(args) < 4:
        print("usage: [filepath for youtube data (html)] [filepath for Chrome data (json)] [filepath for Apple Health data (xml)]")
    yt_path = args[1]
    google_path = args[2]
    apple_path = args[3]
    yt = YoutubeHistoryAnalyzer(yt_path)
    google = BrowserHistoryAnalyzer(google_path)
    apple = AppleHealthAnalyzer(apple_path)
    print("loading data: Youtube")

    yt_data = yt.analyze()
    print("loading data: Google")
    google_data = google.process_daily_timestamps()
    print("loading data: Apple")
    apple_data = apple.analyze()

    print(apple_data)
    yt_data_parsed = parse_timestamps(yt_data)
    google_data_parsed = parse_timestamps(google_data)
    apple_data_parsed = parse_timestamps(apple_data)

    aligned_data = align_datasets(yt_data_parsed, google_data_parsed, apple_data_parsed)

    avg_sleep_schedule = estimate_average_sleep_schedule(aligned_data)
    print("Average Sleep Schedule (Apple Ground Truth):", avg_sleep_schedule)

    youtube_avg_sleep_schedule = estimate_average_sleep_schedule(aligned_data, "youtube")
    print("Average Sleep Schedule (Youtube):", youtube_avg_sleep_schedule)

    chrome_avg_sleep_schedule = estimate_average_sleep_schedule(aligned_data, "chrome")
    print("Average Sleep Schedule (Chrome):", chrome_avg_sleep_schedule)

    accuracy = calculate_accuracy(aligned_data, avg_sleep_schedule)
    print("Accuracy Comparison:", accuracy)

    accuracy_stats = calculate_statistics(accuracy)
    print("Accuracy Statistics:", accuracy_stats)

    plt.figure(figsize=(10, 6))
    sns.boxplot(data=[accuracy['youtube'], accuracy['chrome']], palette='viridis')
    plt.xticks(ticks=[0, 1], labels=['YouTube', 'Chrome'])
    plt.title('Accuracy Comparison of Sleep Schedule Estimation')
    plt.ylabel('Accuracy Difference (Lower is Better)')
    plt.xlabel('Data Source')
    plt.show()

    plot_start_end_times(aligned_data)

    # T test
    youtube_diffs = accuracy['youtube']
    chrome_diffs = accuracy['chrome']
    t_stat, p_value = ttest_ind(youtube_diffs, chrome_diffs)

    print(f"T-Statistic: {t_stat}")
    print(f"P-Value: {p_value}")

    alpha = 0.05
    if p_value < alpha:
        print("Reject the null hypothesis: There is a statistically significant difference.")
    else:
        print("Fail to reject the null hypothesis: There is no statistically significant difference.")

