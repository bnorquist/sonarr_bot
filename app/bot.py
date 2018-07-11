import logging
import pprint
import time
import configparser
import os

from slackclient import SlackClient

from app.sonarr_wrapper.sonarr.sonarr_api import SonarrAPI

# create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

config = configparser.ConfigParser()
config.read('settings.ini')


class Bot(object):

    def __init__(self):
        # slack things
        self.slack_client = SlackClient(config['slack']['slack_key'])
        self.bot_name = config['slack']['bot_name']
        self.connection = self.connect_to_slack()
        self.bot_id = self.get_bot_id()
        self.at_bot = '<@{}>'.format(self.bot_id)
        self.websocket_delay = 1 # 1 second delay between reading from firehose
        self.listen_time = 10 # bot will listen for number of seconds difference between websocket_delay & listen_time

        # slack commands & definitions
        self.help_command = 'help'
        self.get_shows_command = 'get shows'
        self.get_shows_definition = 'Posts message showing which shows & seasons are already subscribed in Sonarr'
        self.add_show_command = 'add show'
        self.add_show_definition = 'Adds show to sonarr'

        # sonarr things
        self.sonarrAPI = SonarrAPI(host_url=config['sonarr']['sonarr_host_url'],
                                   api_key=config['sonarr']['sonarr_api_key']
                                   )
        # reminders
        self.schedule_json_path = config['schedule']['schedule_path']
        self.schedule_modified_timestamp = os.path.getmtime(self.schedule_json_path)

    def connect_to_slack(self):
        if self.slack_client.rtm_connect():
            logger.info("{} connected and running!".format(self.bot_name))
            return True
        else:
            logger.warning('{} not connected to slack :('.format(self.bot_name))
            return False

    def get_shows(self, channel):
        """Post what shows are already available"""
        logger.debug('retrieving shows...')
        series = self.sonarrAPI.get_series()
        shows = {}
        for show in series:
            title = show['title']
            seasons = []
            for season in show['seasons']:
                if season['monitored'] is True:
                    seasons.append(season['seasonNumber'])
            shows[title] = seasons
        # message generator
        block = '\n'.join([key + ' - Seasons: ' + ', '.join([str(number) for number in value]) for key, value in shows.items()])
        message = "Already Subscribed to:\n```{}```".format(block)
        logger.debug('get show message sent to slack: {}'.format(message))

        # post to slack
        self.slack_client.api_call("chat.postMessage", channel=channel, text=message, as_user=True)

    @staticmethod
    def sonarr_response_handler(response):
        shows = []
        if type(response) is list and len(response) > 1:
            for show in response:
                shows.append(show['title'])
        else:
            shows.append(response[0]['title'])
        return shows

    @staticmethod
    def get_sonarr_poster(response, show_number):
        show = response[show_number]
        image_url = ''
        for image in show['images']:
            if image['coverType'] == 'poster':
                image_url = image['url']
        if len(image_url) > 0:
            return image_url
        else:
            return show['images'][0]['url']

    @staticmethod
    def is_number_between(num, start, end):
        try:
            int(num)
            if end >= int(num) >= start:
                return True
        except ValueError:
            return False

    def listen_for_response(self, user_id, channel):
        logger.debug('Listening for responses from user: {} in channel: {}'.format(user_id, channel))
        for x in range(self.websocket_delay, self.listen_time):
            output_list = bot.slack_client.rtm_read()
            if output_list and len(output_list) > 0:
                for output in output_list:
                    # print(output)
                    if 'user' and 'text' in output and output['user'] == user_id and output['channel'] == channel:
                        return output

            time.sleep(self.websocket_delay)
        return None

    def get_quality_names(self):
        """prompt user to choose a quality profile"""
        profiles = self.sonarrAPI.get_quality_profiles()

        if len(profiles) == 1:
            logger.debug('One quality profile detected, returned profile {}'.format(profiles[0]['id']))
            return {profiles[0]['name']: profiles[0]['id']}, len(profiles)

        elif len(profiles) > 1:
            profile_names = {}
            for profile in profiles:
                profile_names[profile['name']] = profile['id']
            logger.debug('{} profiles found'.format(len(profiles)))
            return profile_names, len(profiles)
        else:
            logger.debug('No profiles detected')

    def confirm_show(self, show_number, json, sender):
        show_list = self.sonarr_response_handler(json)
        message = 'Do you want to subscribe to `{}`?'.format(show_list[show_number])
        image_url = self.get_sonarr_poster(json, show_number=show_number)
        attachment = [
                        {
                        "title": show_list[show_number],
                        "image_url": "{}".format(image_url)
                        }
                    ]
        self.slack_client.api_call("chat.postMessage", channel=channel, text=message, as_user=True, attachments=attachment)

        # listen for response and add show if response is yes
        user_decision = self.listen_for_response(user_id=sender, channel=channel)
        logger.debug('Add show user decision slack response: {}'.format(user_decision))

        if user_decision is not None and user_decision['text'].lower() == 'yes':
            logger.info('User chose to subscribe')
            message = 'Subscribing to `{}`...'.format(show_list[show_number])
            result = True
        elif user_decision is not None:
            logger.info('User chose not to subscribe')
            message = 'I did not subscribe to `{}`'.format(show_list[show_number])
            result = False
        else:
            logger.info('User did not respond')
            message = 'No response detected...'
            result = False

        self.slack_client.api_call("chat.postMessage", channel=channel, text=message, as_user=True)
        return result

    def add_show_interaction(self, channel, command, sender):
        logger.debug('Adding show')

        show_parameter = command.split(self.add_show_command)[1]
        response = self.sonarrAPI.lookup_series(query=show_parameter)

        shows = self.sonarr_response_handler(response)

        # respond based on whether one or multiple shows were returned
        show_range = [1, 4]

        # if more than 1 show is returned provide a choice of what to subscribe to
        if 1 < len(shows) <= show_range[1]:
            logger.debug('Less than 4 shows, providing list choice')
            block = []
            for index, show in enumerate(shows):
                block.append('({}) - {}'.format(str(index + 1), show))

            message = 'The following shows were found: \n ```{}```\n ' \
                      'Respond with the number next to the show to subscribe.'.format('\n'.join(block))
            self.slack_client.api_call("chat.postMessage", channel=channel, text=message, as_user=True)

            # listen for response and add show if number is returned
            user_decision = self.listen_for_response(user_id=sender, channel=channel)
            logger.debug('range choice add_show() user decision {}'.format(user_decision))
            if user_decision is not None and \
                    self.is_number_between(user_decision['text'], start=show_range[0], end=show_range[1]):
                logger.debug('User chose valid show number to add: {}'.format(user_decision['text']))

                show_number = int(user_decision['text']) - 1
                result = self.confirm_show(show_number=show_number, json=response, sender=sender)
            else:
                # re-try
                self.add_show_interaction(channel, command, sender)

        elif len(shows) > show_range[1]:
            block = [x for x in shows]
            message = 'The following shows were found: \n ```{}```\n Please refine your search.'.format(', '.join(block))
            # post to slack
            self.slack_client.api_call("chat.postMessage", channel=channel, text=message, as_user=True)
            result = False
            show_number = 0

        else:
            show_number = 0
            result = self.confirm_show(show_number=show_number, json=response, sender=sender)

        # choose quality profile if necessary
        quality_profiles, profile_count = self.get_quality_names()

        if profile_count > 1:
            # choose profile
            message = "Please choose a quality profile to use, here are your options: \n ```{}``` \n " \
                      "paste the name of the profile you choose and I'll select it"\
                        .format(', '.join([key for key, value in quality_profiles.items() ]))
            self.slack_client.api_call("chat.postMessage", channel=channel, text=message, as_user=True)

            user_decision = self.listen_for_response(user_id=sender, channel=channel)
            logger.info('user chose {}'.format(user_decision))

            if user_decision['text'] in [key for key, value in quality_profiles.items()]:
                quality_profile_id = quality_profiles[user_decision['text']]

            else:
                # error message and retry
                self.slack_client.api_call("chat.postMessage", channel=channel,
                                           text='invalid entry, try again', as_user=True)
        else:
            # default to one quality profile if there is only one
            quality_profile_name = [key for key, value in quality_profiles.items()][0]
            quality_profile_id = [value for key, value in quality_profiles.items()][0]
            logger.debug('Discovered one quality profile: {}'.format(quality_profile_name))

        return result, response[show_number], quality_profile_id

    def add_show(self, channel, command, sender):
        result, show_dict, quality_profile_id = self.add_show_interaction(channel, command, sender)
        series_id = show_dict['tvdbId']
        if result is True:
            logger.info('Adding {} to Sonarr'.format(show_dict['title']))
            json = self.sonarrAPI.add_series(self.sonarrAPI.constuct_series_json(tvdbId=series_id,
                                                                                 quality_profile=quality_profile_id))
            # pprint.pprint(json)
            message = 'Successfully subcribed to {}'.format(show_dict['title'])
            self.slack_client.api_call("chat.postMessage", channel=channel, text=message, as_user=True)
        else:
            pass

    def get_bot_id(self):
        """get slack user id for bot"""

        users = self.slack_client.api_call("users.list")

        for user in users['members']:
            if user['name'] == self.bot_name:
                bot_id = user['id']
                break
            else:
                bot_id = False

        if bot_id is not False:
            logger.debug('Bot_ID found for: {} with id: {}'.format(self.bot_name, bot_id))
            return bot_id
        else:
            logger.debug('Bot_ID not found with name: {}'.format(self.bot_name))

    def help(self):
        """help command"""
        methods = {}
        methods[self.get_shows_command] = self.get_shows_definition
        methods[self.add_show_command] = self.add_show_definition

        block = []
        for command, definition in methods.items():
            block.append("`{}` - {}".format(command, definition))
        response = "Here is what I can do: \n{}".format('\n'.join(block))

        self.slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)

    def handle_command(self, channel, command, sender):
        """
            Receives commands directed at the bot and determines if they
            are valid commands. If so, then acts on the commands. If not,
            returns back what it needs for clarification.
        """
        logger.debug('Handling command: {} in channel: {}'.format(command, channel))
        if command.startswith(self.help_command):
            self.help()
        elif command.lower() == self.get_shows_command:
            self.get_shows(channel=channel)

        elif command.lower().startswith(self.add_show_command):
            self.add_show(channel=channel, command=command, sender=sender)

        elif command.lower() == 'quality_profiles':
            self.test_sn_command(channel=channel, command=command, sender=sender)

        else:
            pass

    def test_sn_command(self, channel, command, sender):

        if command.lower() == 'quality_profiles':
            logger.info('Getting quality profiles')
            response = self.sonarrAPI.get_quality_profiles()
            pprint.pprint(response)
            self.slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)
        else:
            logger.info('{} command not added yet'.format(command))
            pass


def parse_slack_output(slack_rtm_output, AT_BOT):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                # return text after the @ mention, whitespace removed
                print(output)
                command = output['text'].split(AT_BOT)[1].strip().lower()
                channel = output['channel']
                sender = output['user']
                return command, channel, sender

    return None, None, None


def scheduler(bot_instance):
    """open config if file has changed"""
    if bot_instance.schedule_modified_timestamp == os.path.getmtime(bot_instance.schedule_json_path):
        # check if it is time to post calender, otherwise do nothing
        pass
    else:
        # reload schedule
        pass


if __name__ == "__main__":

    bot = Bot()

    while True:
        command, channel, sender = parse_slack_output(bot.slack_client.rtm_read(), bot.at_bot)

        if command and channel:
            bot.handle_command(channel, command, sender)

        time.sleep(bot.websocket_delay)
        scheduler(bot)


#screen -dmS sbot bash -c 'python ~/files/code/sonarr_bot/bot.py'