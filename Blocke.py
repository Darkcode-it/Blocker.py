import requests
import random
import time
import re
import logging
from typing import List, Dict, Optional
import json
import os

# تنظیمات لاگ‌گیری / Logging settings
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("report_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("InstagramReporter")  # تعیین نام برای لاگر / Set logger name

# تنظیمات پیکربندی / Configuration settings
CONFIG_FILE = "config.json"

class Config:
    """کلاس برای مدیریت تنظیمات پیکربندی / Class for managing configuration settings"""
    def __init__(self):  # تغییر از init به __init__ / Change from init to __init__
        self.api_url = ""
        self.block_endpoint = ""
        self.report_endpoint = ""
        self.api_token = ""
        self.proxy_list = []
        self.load_config()

    def load_config(self):
        """بارگذاری تنظیمات از فایل پیکربندی / Load settings from config file"""
        if not os.path.exists(CONFIG_FILE):
            logger.error(f"Config file '{CONFIG_FILE}' not found! Please create it.")
            raise FileNotFoundError(f"Config file '{CONFIG_FILE}' not found!")

        with open(CONFIG_FILE, "r") as file:
            config = json.load(file)
            self.api_url = config.get("api_url", "")
            self.block_endpoint = config.get("block_endpoint", "")
            self.report_endpoint = config.get("report_endpoint", "")
            self.api_token = config.get("api_token", "")
            self.proxy_list = config.get("proxy_list", [])

class InstagramReporter:
    """کلاس اصلی برای مدیریت گزارش‌دهی و مسدود کردن اکانت‌ها / Main class for managing reporting and blocking accounts"""
    def __init__(self, config: Config):  # تغییر از init به __init__ / Change from init to __init__
        self.config = config
        self.headers = {
            "Authorization": f"Bearer {self.config.api_token}",
            "Content-Type": "application/json",
        }
        self.current_proxy = None  # پراکسی فعلی / Current proxy

    @staticmethod
    def extract_username(url: str) -> Optional[str]:
        """استخراج نام کاربری از URL / Extract username from URL"""
        pattern = r"https?://www\.instagram\.com/([a-zA-Z0-9_.]+)/?"
        match = re.search(pattern, url)
        return match.group(1) if match else None

    def get_user_id(self, username: str) -> Optional[str]:
        """تبدیل نام کاربری به شناسه کاربری / Convert username to user ID"""
        url = f"https://www.instagram.com/{username}/?__a=1"
        try:
            response = requests.get(url, proxies=self.current_proxy, timeout=60)  # افزایش timeout به ۶۰ ثانیه
            if response.status_code == 200:
                data = response.json()
                return data["graphql"]["user"]["id"]
            else:
                logger.warning(f"Failed to fetch user ID for {username}. Status code: {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching user ID: {e}")
            return None

    def get_random_proxy(self) -> Dict[str, str]:
        """انتخاب تصادفی یک پراکسی از لیست / Select a random proxy from the list"""
        if not self.config.proxy_list:
            logger.warning("No proxies available in the config.")
            return {}
        return random.choice(self.config.proxy_list)

    def block_user(self, user_id: str) -> bool:
        """مسدود کردن اکانت با استفاده از پراکسی / Block account using proxy"""
        url = f"{self.config.api_url}{self.config.block_endpoint}"
        data = {"user_id": user_id}
        try:
            response = requests.post(url, headers=self.headers, json=data, proxies=self.current_proxy, timeout=60)  # افزایش timeout به ۶۰ ثانیه
            if response.status_code == 200:
                logger.info(f"User {user_id} blocked successfully using proxy {self.current_proxy}.")
                return True
            else:
                logger.warning(f"Failed to block user {user_id}. Status code: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Proxy {self.current_proxy} failed: {e}")
            return False

    def report_user(self, user_id: str, reason: str) -> bool:
        """گزارش دادن اکانت با استفاده از پراکسی / Report account using proxy"""
        url = f"{self.config.api_url}{self.config.report_endpoint}"
        try:
            data = {"user_id": user_id, "reason": reason}
            response = requests.post(url, headers=self.headers, json=data, proxies=self.current_proxy, timeout=60)  # افزایش timeout به ۶۰ ثانیه
            if response.status_code == 200:
                logger.info(f"User {user_id} reported successfully for: {reason} using proxy {self.current_proxy}.")
                return True
            else:
                logger.warning(f"Failed to report user {user_id}. Status code: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Proxy {self.current_proxy} failed: {e}")
            return False

    def run(self):
        """اجرای اصلی اسکریپت / Main script execution"""
        try:
            while True:
                # دریافت آدرس اکانت از کاربر / Get account URL from user
                profile_url = input("Enter Instagram account URL (or 'exit' to quit): ")
                if profile_url.lower() == "exit":
                    logger.info("Exiting script.")
                    break

                # استخراج نام کاربری از URL / Extract username from URL
                username = self.extract_username(profile_url)
                if not username:
                    logger.warning(f"Invalid URL: {profile_url}")
                    continue

                # انتخاب یک پراکسی تصادفی / Select a random proxy
                self.current_proxy = self.get_random_proxy()
                logger.info(f"Using proxy: {self.current_proxy}")

                # تبدیل نام کاربری به شناسه کاربری / Convert username to user ID
                user_id = self.get_user_id(username)
                if not user_id:
                    logger.warning(f"User ID not found for {username}.")
                    continue

                # مسدود کردن اکانت / Block account
                if not self.block_user(user_id):
                    logger.warning("Blocking failed. Changing proxy...")
                    continue  # تغییر پراکسی و شروع مجدد

                # گزارش دادن اکانت / Report account
                reason = "User request"  # دلیل گزارش / Reason for reporting
                if not self.report_user(user_id, reason):
                    logger.warning("Reporting failed. Changing proxy...")
                    continue  # تغییر پراکسی و شروع مجدد

                # تاخیر بین درخواست‌ها برای جلوگیری از تشخیص ربات / Delay between requests to avoid bot detection
                delay = random.randint(55, 65)  # تاخیر تصادفی بین ۵۵ تا ۶۵ ثانیه / Random delay between 55 to 65 seconds
                logger.info(f"Waiting for {delay} seconds before the next request...")
                time.sleep(delay)
        except KeyboardInterrupt:
            logger.info("Script stopped manually.")

if __name__ == "__main__":  # تغییر از name به __name__ / Change from name to __name__
    # بارگذاری تنظیمات و اجرای اسکریپت / Load settings and run script
    try:
        config = Config()
        reporter = InstagramReporter(config)
        reporter.run()
    except Exception as e:
        logger.error(f"An error occurred: {e}")