# RSS to Telegram Bot

This bot fetches updates from specified RSS feeds and sends them to a Telegram channel. It supports multi-threading and can handle multiple feeds at once.

## Prerequisites

* Python 3.11
* Docker

## Installation and Setup

1. **Clone this repository:**

    ```console
    git clone https://github.com/pLevishchev/RssToTelegram.git
    cd RssToTelegram
    ```

2. **Set up your configuration:**

   You need to set up configuration file named `config_template.ini` in the `configurations` directory. The configuration files should look like this:

    ```ini
    [Telegram]
    token = your_telegram_bot_token
    channel = your_telegram_channel_id

    [YouTube]
    api_key = your_youtube_api_key

    [RSS]
    feeds = rss_feed_1,rss_feed_2,...,rss_feed_n
    ```

    Replace `your_telegram_bot_token` with your Telegram bot's token, `your_telegram_channel_id` with the ID of your Telegram channel, `your_youtube_api_key` with your YouTube Data API v3 key, and `rss_feed_1,rss_feed_2,...,rss_feed_n` with the RSS feeds you wish to monitor.

3. **Build the Docker image:**

    ```console
    docker build -t rss_to_telegram .
    ```

4. **Run the Docker containers:**

    For `config_template.ini`:

    ```console
    docker run -d -v $(pwd)/configurations/config_template.ini:/app/configurations/config.ini rss_to_telegram python rss_to_telegram.py --config /app/configurations/config.ini
    ```

Please ensure to replace `/path/to/config_template.ini` with the actual paths of your configuration files.

## How it Works

The bot periodically fetches the RSS feeds and checks for new updates. If it finds new entries, it sends them to the specified Telegram channel. The bot uses multi-threading to handle multiple feeds concurrently. It also makes sure that the same entry is not posted more than once by keeping track of the history of posted entries.
