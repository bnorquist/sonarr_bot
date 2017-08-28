from sonarr_wrapper.sonarr.sonarr_api import SonarrAPI
import bot as b
import pprint, pdb

if __name__ == "__main__":
    sn = SonarrAPI(host_url='http://galileo.whatbox.ca:14212/api', api_key='01fbaa362c2343bd89f5884dd5fa2fac')
    #pprint.pprint(sn.lookup_series('nathan for you'# )
    print('here')
    sn.get_system_status()
    #series = sn.get_series()
    #pprint.pprint(series)

    #print(sn.get_series_to_add(tvdbId=267002))
    #pprint.pprint(sn.get_series_by_series_id(series_id='1'))
    #pprint.pprint(sn.get_root_folder())
    qual = sn.get_quality_profiles()
    pprint.pprint(sn.get_quality_profiles())
    #pdb.set_trace()
    #pprint.pprint(sn.add_series(267002))


    #bot = b.Bot()
    #bot.get_shows()
