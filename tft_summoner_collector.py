import json
from datetime import datetime
from riotapi import RiotAPI

class TFTSummonerCollector(RiotAPI):
    def __init__(self, region, key):
        super().__init__(api_region=region, api_key=key)
        self.region = region
        self.date = datetime.today().strftime("%m%d%Y")

    def get_summoner_puuid(self, player_list):
        puuid_list = []
        for entry in player_list:
            try:
                puuid_list.append(RiotAPI.get_summoner_by_summonerId(
                    self, entry['summonerId'])['puuid'])
            except:
                print("Get puuid failed, one summoner is skipped!")
                continue
        return puuid_list

    def get_puuid_list(self, rank):
        try:
            rank = rank.lower()
        except:
            print("ERROR: Entered rank format is wrong!")
            exit()
        
        print("Started to collect {} puuids...".format(rank))

        if rank == 'challenger':            
            puuid_list = self.get_summoner_puuid(
                RiotAPI.get_tft_challenger(self)["entries"])
        elif rank == 'grandmaster':
            puuid_list = self.get_summoner_puuid(
                RiotAPI.get_tft_grandmaster(self)["entries"])            
        elif rank == 'master':
            puuid_list = self.get_summoner_puuid(
                RiotAPI.get_tft_master(self)["entries"])         
        else:
            print("ERROR: The puuids of the rank [{}] cannot be pulled".format(rank))
            exit() 
        
        file_name = 'tft_{0}_list_{1}_{2}.json'.format(rank, self.region, self.date)
        with open(file_name, 'w') as f:
            json.dump(puuid_list, f)
        print("------------------------------")
        print("Retrieved {} {} puuids".format(len(puuid_list), rank))
        print("Stored in {}".format(file_name))
        print("------------------------------")

if __name__ == "__main__":
    test_region = 'NA1'
    test_key = 'RGAPI-XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX'

    collector = TFTSummonerCollector(test_region, test_key)
    collector.get_puuid_list('challenger')