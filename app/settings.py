from dotenv import load_dotenv, find_dotenv
import os
import logging

load_dotenv(find_dotenv())

SLACK_KEY = os.getenv('SLACK_KEY')
BOT_NAME = os.getenv('BOT_NAME')
SONARR_HOST_URL = os.getenv('SONARR_HOST_URL')
SONARR_API_KEY = os.getenv('SONARR_API_KEY')
LOG_FORMAT = '%(asctime)s - %(name)-4s - %(levelname)-4s - %(message)s'

# logging setup
if not os.path.exists('../log/bot.log'):
    os.mkdir('../log/')
logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT, filename='../log/bot.log', filemode='a')
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter(LOG_FORMAT)
ch.setFormatter(formatter)
logging.getLogger('').addHandler(ch)