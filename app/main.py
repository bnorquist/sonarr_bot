import pprint
import configparser
from app.sonarr_wrapper.sonarr.sonarr_api import SonarrAPI

if __name__ == "__main__":
    config = configparser.ConfigParser()

    config.read('settings.ini')
    print(config.sections())
    # sn = SonarrAPI(host_url='http://galileo.whatbox.ca:14212/api', api_key='61d044f4e99a43959598a1bedd0a0df9')
    # #pprint.pprint(sn.lookup_series('nathan for you'# )
    # print('here')
    # sn.get_system_status()
    # #series = sn.get_series()
    # #pprint.pprint(series)
    #
    # #print(sn.get_series_to_add(tvdbId=267002))
    # #pprint.pprint(sn.get_series_by_series_id(series_id='1'))
    # #pprint.pprint(sn.get_root_folder())
    # pprint.pprint(sn.get_quality_profiles())
    # #pprint.pprint(sn.add_series(267002))
    #

    #bot = b.Bot()
    #bot.get_shows()
