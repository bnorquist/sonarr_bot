from sonarr_wrapper.sonarr.sonarr_api import SonarrAPI
import bot as b
import pprint

if __name__ == "__main__":
    sn = SonarrAPI(host_url='http://galileo.whatbox.ca:14212/api', api_key='61d044f4e99a43959598a1bedd0a0df9')
    pprint.pprint(sn.lookup_series('nathan for you'))

    #series = sn.get_series()
    #pprint.pprint(series)

    #print(sn.get_series_to_add(tvdbId=267002))
    #pprint.pprint(sn.get_series_by_series_id(series_id='1'))
    #pprint.pprint(sn.get_root_folder())
    #pprint.pprint(sn.get_quality_profiles())
    #pprint.pprint(sn.add_series(267002))


    #bot = b.Bot()
    #bot.get_shows()
