
from applehealthanalyzer import AppleHealthAnalyzer
from browserhistoryanalyzer import BrowserHistoryAnalyzer
from youtubehistoryanalyzer import YoutubeHistoryAnalyzer

yt = YoutubeHistoryAnalyzer('C:/Users/Vincent/Downloads/watch-history.html')
google = BrowserHistoryAnalyzer("C:/Users/Vincent/Downloads/History.json")
apple = AppleHealthAnalyzer("C:/Users/Vincent/Downloads/export.xml")

yt_data = yt.analyze()
google_data = google.process_daily_timestamps()
apple_data = apple.analyze()

