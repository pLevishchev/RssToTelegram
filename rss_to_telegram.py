import os
import re
import time
import isodate
import logging
import argparse
import requests
import threading
import feedparser
import configparser
from datetime import datetime, timedelta, timezone
from dateutil import parser as dateparser
from concurrent.futures import ThreadPoolExecutor
from message_formatter import MessageFormatter

logging_directory = 'logs'
os.makedirs(logging_directory, exist_ok=True)
logging.basicConfig(level=logging.INFO, 
                    filename=os.path.join(logging_directory, 'rss_to_telegram.log'),
                    filemode='w', 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class RssToTelegram:
    """
    Class that fetches RSS feeds and posts them to a Telegram channel.
    """
        
    def __init__(self, config_file):
        """
        Initializes the RssToTelegram class.
        Reads the configuration file to set up the necessary parameters.
        """
        
        self.semaphore = threading.Semaphore()
        self.config = self.read_config(config_file)

    def read_config(self, file_path):
        """
        Reads the provided configuration file.
        Returns a dictionary with the necessary configuration parameters.
        """

        config = configparser.ConfigParser()
        try:
            config.read(file_path)

            return {
                "token": config.get("Telegram", "token"),
                "channel": config.get("Telegram", "channel"),
                "feeds": config.get("RSS", "feeds").split(","),
                "youtube_api_key": config.get("YouTube", "api_key")
            }

        except configparser.NoSectionError as e:
            logging.error(f"Missing section in config file: {str(e)}")
            return None
        except configparser.NoOptionError as e:
            logging.error(f"Missing option in config file: {str(e)}")
            return None
        except configparser.ParsingError as e:
            logging.error(f"Error while parsing config file: {str(e)}")
            return None

    def truncate_summary(self, summary,
                         max_characters=200):
        """
        Truncates the summary of a feed entry to the maximum character limit.
        The summary is truncated at the end of a sentence.
        """

        sentences = re.split(r'(?<=[.!?])\s+', summary)
        truncated = ''
        for sentence in sentences:
            if len(truncated) + len(sentence) <= max_characters:
                truncated += ' ' + sentence
            else:
                break
        return truncated.strip()

    def read_rss_feed(self, feed_url, history_file):
        """
        Reads and parses an RSS feed from the provided URL.
        It checks each feed entry against a history file and sends new entries to a Telegram channel.
        """

        try:
            logging.info(f"Reading RSS feed: {feed_url}")
            feed = feedparser.parse(feed_url)
        except Exception as e:
            logging.error(f"Error occurred while parsing feed {feed_url}: {str(e)}")
            return

        if os.path.exists(history_file):
            with open(history_file, "r") as f:
                history = set(f.read().splitlines())
        else:
           history = set()

        three_months_ago = datetime.now(timezone.utc) - timedelta(days = 3)

        for entry in reversed(feed.entries):
            date_str = entry.get('published', entry.get('updated'))
            entry_date = dateparser.parse(date_str)
            author = entry.author if hasattr(entry, 'author') else "RSS"
            if entry_date > three_months_ago and entry.id not in history:
                history.add(entry.id)
                message = MessageFormatter.format_message(
                    author,
                    entry.title,
                    self.truncate_summary(entry.summary),
                    entry.link)
                
                if 'youtube.com' in feed_url:
                    video_id = entry.link.split("=")[-1]
                    if self.is_youtube_video_short(video_id):
                        continue
                try:
                    self.send_telegram_message(message)
                except Exception as e:
                    logging.error(f"Failed to send message for entry {entry.id} due to error: {str(e)}")

                with open(history_file, "a") as f:
                    f.write(entry.id + "\n")
                    logging.info(f"Entry {entry.id} added to the history")

    def is_youtube_video_short(self, video_id):
        """
        Checks whether a YouTube video is shorter than one minute.
        It uses the YouTube Data API to fetch the video details.
        """

        url = f"https://www.googleapis.com/youtube/v3/videos?id={video_id}&part=contentDetails&key={self.config['youtube_api_key']}"

        try:
            response = requests.get(url)
            response.raise_for_status()
        except Exception as e:
            logging.error(f"Failed to retrieve video details due to error: {str(e)}")
            return False

        data = response.json()
        if data['items']:
            duration_str = data['items'][0]['contentDetails']['duration']
            duration = isodate.parse_duration(duration_str)
            return duration.total_seconds() < 60
        else:
            logging.error(f"Failed to send request to YouTube API: {response.content}")
            return False

    def send_telegram_message(self, message):
        """
        Sends a message to a specified Telegram channel.
        It uses the Telegram Bot API to send the message.
        """
        with self.semaphore:
            url = f"https://api.telegram.org/bot{self.config['token']}/sendMessage"

            payload = {
                'chat_id': self.config['channel'],
                'text': message,
                'parse_mode': 'HTML'
            }
            try:
                response = requests.post(url, payload)
                response.raise_for_status()
            except Exception as e:
                logging.error(f"Failed to send message due to error: {str(e)}")
            time.sleep(60)
    def run(self):
        """
        Starts the feed reader. It fetches the feeds concurrently.
        """
        
        history_dir = 'history'
        os.makedirs(history_dir, exist_ok=True)
        while True:
            with ThreadPoolExecutor() as executor:
                for feed_url in self.config["feeds"]:
                    history_filename = f"{feed_url.replace('https://', '').replace('/', '_')}_history.txt"
                    history_file = os.path.join(history_dir, history_filename)
                    executor.submit(self.read_rss_feed, feed_url, history_file)
            time.sleep(1800)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'RSS to Telegram bot.')
    parser.add_argument('--config',
                        type = str, 
                        default = 'configurations/config_template.ini',
                        help = 'Path to the configuration file.')

    args = parser.parse_args()

    bot = RssToTelegram(args.config)
    
    if bot.config is None:
        logging.error("Failed to read configuration. Exiting.")
        exit(1)

    bot.run()