import configparser

config = configparser.ConfigParser()

config['slack'] = {'slack_key': input('enter slack api key: '),
                   'bot_name': input('enter slackbot name: ')
                   }

config['sonarr'] = {'sonarr_host_url': input('enter sonarr host url: '),
                    'sonarr_api_key': input('enter sonarr api key: ')
                    }

config['schedule'] = {
                    'schedule_path': 'app/lib/schedule.json'
                     }

with open('app/settings.ini', 'w') as cfgfile:
    config.write(cfgfile)
