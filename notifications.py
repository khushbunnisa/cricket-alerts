import threading
from time import sleep
from win10toast import ToastNotifier
import requests
from bs4 import BeautifulSoup

class NotificationManager:
    def __init__(self):
        self.notifier = ToastNotifier()
        self.thread = None
        self.running = False

    def fetch_score(self, matchNum):
        try:
            page = requests.get('http://static.cricinfo.com/rss/livescores.xml', timeout=10)
            page.raise_for_status()
            soup = BeautifulSoup(page.text, 'lxml')
            matches = soup.find_all('description')
            live_matches = [s.get_text() for s in matches if '*' in s.get_text()]
            return live_matches[matchNum] if matchNum < len(live_matches) else "Match not found"
        except requests.exceptions.RequestException as e:
            print(f"Error fetching match score: {e}")
            return "Error fetching match score"

    def notify(self, score):
        self.notifier.show_toast(score, "Latest Score Alert!", duration=10)

    def start_notifications(self, matchNum):
        self.running = True
        while self.running:
            current_score = self.fetch_score(matchNum)
            self.notify(current_score)
            sleep(30)

    def start(self, matchNum):
        if self.thread is None:
            self.thread = threading.Thread(target=self.start_notifications, args=(matchNum,))
            self.thread.start()

    def stop(self):
        if self.thread is not None:
            self.running = False
            self.thread.join()
            self.thread = None

notification_manager = NotificationManager()