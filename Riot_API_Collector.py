from datetime import datetime
import time
import json
import requests
from ratelimit import limits, sleep_and_retry, RateLimitException


SERVER = 'NA1'
KEY = 'RGAPI-d4495cef-6c85-48f2-b601-4c679374a312'
BATCH_NUM = 0


class RiotAPI():
    URL = {
        'base': 'https://{region}.api.riotgames.com/{url}',
        'tft_challenger': '/tft/league/v1/challenger',
        'tft_grandmaster': '/tft/league/v1/grandmaster',
        'tft_master': '/tft/league/v1/master',
        'tft_summoner_by_summonerId': '/tft/summoner/v1/summoners/{encryptedSummonerId}',
        'tft_summoner_by_summonerName': '/tft/summoner/v1/summoners/by-name/{summonerName}',
        'tft_match_by_puuid': 'tft/match/v1/matches/by-puuid/{puuid}/ids',
        'tft_match_by_matchId': 'tft/match/v1/matches/{matchId}'
    }

    REGIONS = {
        'NA1': 'americas',
        'EUN1': 'europe',
        'EUW1': 'europe',
        'KR': 'asia'
    }

    def __init__(self, api_key, api_region):
        self.api_key = api_key
        self.region = api_region

    @sleep_and_retry
    @limits(calls=4, period=5)
    def _request(self, api_url, region, params={}):
        args = {
            'api_key': self.api_key
        }

        for key, val in params.items():
            if key not in args:
                args[key] = val

        request_success = False
        while not request_success:

            response = requests.get(
                self.URL['base'].format(
                    region=region,
                    url=api_url
                ),
                params=args
            )

            if response.status_code == 200:
                request_success = True
            elif response.status_code == 429:
                print("Riot API - {} Rate limit exceeded".format(response.status_code))
                print('Retry in 125s')
                time.sleep(125)
            elif response.status_code == 503:
                print("Riot API - {} Service unavailable".format(response.status_code))
                print('Sleep for 30s')
                time.sleep(30)
            else:
                print('Riot API request failed:', response.status_code)
                raise Exception('API response: {} URL: {}'.format(
                    response.status_code, response.url))

        return response.json()

    def get_tft_challenger(self):
        api_url = self.URL['tft_challenger']
        return self._request(api_url, self.region)

    def get_tft_grandmaster(self):
        api_url = self.URL['tft_grandmaster']
        return self._request(api_url, self.region)

    def get_tft_master(self):
        api_url = self.URL['tft_master']
        return self._request(api_url, self.region)

    def get_summoner_by_summonerId(self, summonerId):
        api_url = self.URL['tft_summoner_by_summonerId'].format(
            encryptedSummonerId=summonerId
        )
        return self._request(api_url, self.region)

    def get_summoner_by_summonerName(self, summonerName):
        api_url = self.URL['tft_summoner_by_summonerName'].format(
            summonerName=summonerName
        )
        return self._request(api_url, self.region)

    def get_matchId_by_puuid(self, puuid, match_cnt=20):
        api_url = self.URL['tft_match_by_puuid'].format(
            puuid=puuid
        )
        return self._request(api_url, self.REGIONS[self.region])

    def get_match_by_matchId(self, matchId):
        api_url = self.URL['tft_match_by_matchId'].format(
            matchId=matchId
        )
        return self._request(api_url, self.REGIONS[self.region])


class TFTSummonerCollector(RiotAPI):
    def __init__(self, region):
        DEVELOPMENT_API_KEY = 'RGAPI-a0a2db5c-7bbb-423c-95d4-cbdbb2254ccc'
        super().__init__(api_key=DEVELOPMENT_API_KEY, api_region=region)
        self.region = region
        self.date = datetime.today().strftime("%m%d%Y")

    def add_summoner_puuid(self, player_list):
        puuid_list = []
        for entry in player_list:
            try:
                puuid_list.append(RiotAPI.get_summoner_by_summonerId(
                    self, entry['summonerId'])['puuid'])
            except:
                print("Get puuid failed, one summoner is skipped!")
                continue
        return puuid_list

    def get_challengers(self):
        self.challenger_list = self.add_summoner_puuid(
            RiotAPI.get_tft_challenger(self)["entries"])
        with open('tft_challenger_list_{0}_{1}.json'.format(self.region, self.date), 'w') as f:
            json.dump(self.challenger_list, f)
        print("------------------------------")
        print("Retrieved {} challenger ids".format(len(self.challenger_list)))
        print("------------------------------")

    def get_grandmasters(self):
        self.grandmaster_list = self.add_summoner_puuid(
            RiotAPI.get_tft_grandmaster(self)["entries"])
        with open('tft_grandmaster_list_{0}_{1}.json'.format(self.region, self.date), 'w') as f:
            json.dump(self.grandmaster_list, f)
        print("------------------------------")
        print("Retrieved {} grandmaster ids".format(len(self.grandmaster_list)))
        print("------------------------------")

    def get_masters(self):
        self.master_list = self.add_summoner_puuid(
            RiotAPI.get_tft_master(self)["entries"])
        with open('tft_master_list_{0}_{1}.json'.format(self.region, self.date), 'w') as f:
            json.dump(self.master_list, f)
        print("------------------------------")
        print("Retrieved {} master ids".format(len(self.master_list)))
        print("------------------------------")


class TFTMatchCollector(RiotAPI):
    def __init__(self, region):
        DEVELOPMENT_API_KEY = KEY
        super().__init__(api_key=DEVELOPMENT_API_KEY, api_region=region)
        self.date = datetime.today().strftime("%m%d%Y")
        self.region = region

        with open('tft_challenger_list_{}_12062020.json'.format(self.region), 'r') as f:
            self.challenger_list = json.load(f)
        with open('tft_grandmaster_list_{}_12062020.json'.format(self.region), 'r') as f:
            self.grandmaster_list = json.load(f)
        with open('tft_master_list_{}_12062020.json'.format(self.region), 'r') as f:
            self.master_list = json.load(f)

    def get_recent_matchIds(self):
        self.matchIds = set()

        retrival_cnt = 0
        failure_cnt = 0

        for player_id in self.challenger_list+self.grandmaster_list+self.master_list:
            try:
                tmp_matchIds = RiotAPI.get_matchId_by_puuid(self, player_id)
                retrival_cnt += 1
            except:
                failure_cnt += 1
                continue
            self.matchIds = self.matchIds.union(set(tmp_matchIds))

            if retrival_cnt % 500 == 0:
                print("[{}]: retrieved: {} players, failed: {}".format(
                    datetime.now().strftime("%d/%m/%Y-%H:%M:%S"), retrival_cnt, failure_cnt))
                with open('tmp_tft_collected_match_ids_{}_{}.json'.format(self.region, self.date), 'w') as f:
                    json.dump(list(self.matchIds), f)

        with open('tft_collected_match_ids_{}_{}.json'.format(self.region, self.date), 'w') as f:
            json.dump(list(self.matchIds), f)

        print("------------------------------")
        print("Retrieved {} match ids, valid: {}".format(
            retrival_cnt*20, len(self.matchIds)))
        print("Failed to retrieve: {}".format(failure_cnt*20))
        print("------------------------------")

    def get_match_info(self, batch_num):
        with open('tft_collected_match_ids_{}_12082020_batch_{}.json'.format(self.region, batch_num), 'r') as f:
            self.matchIds = json.load(f)

        retrival_cnt = 0
        failure_cnt = 0
        self.match_info = []
        for matchId in self.matchIds:
            try:
                match = RiotAPI.get_match_by_matchId(self, matchId)
                self.match_info.append(match['info'])
                retrival_cnt += 1
            except:
                failure_cnt += 1
                continue

            if retrival_cnt % 500 == 0:
                print("[{}]: retrieved: {} matches, failed: {}".format(
                    datetime.now().strftime("%d/%m/%Y-%H:%M:%S"), retrival_cnt, failure_cnt))
                with open('tmp_tft_match_info_{}_{}_batch_{}.json'.format(self.region, self.date, batch_num), 'w') as f:
                    json.dump(self.match_info, f)

        with open('tft_match_info_{}_{}_batch_{}.json'.format(self.region, self.date, batch_num), 'w') as f:
            json.dump(self.match_info, f)

        print("------------------------------")
        print("Retrieved {} matches with info".format(retrival_cnt))
        print("Failed to retrieve: {}".format(failure_cnt))
        print("------------------------------")

    def load_matchIds(self):
        with open('tft_collected_match_ids_{}_12082020.json'.format(self.region), 'r') as f:
            self.matchIds = json.load(f)

    def load_match_info(self):
        with open('tft_match_info_{}_{}.json'.format(self.region, self.date), 'r') as f:
            self.match_info = json.load(f)

    def create_batches(self, key_number=5):
        self.load_matchIds()

        matchId_size = len(self.matchIds)
        trunck_size = matchId_size//key_number + 1

        print("MatchId size:", matchId_size)
        print("API key number:", key_number)
        for num in range(key_number):
            arr_start = num*trunck_size
            arr_end = (num+1)*trunck_size
            batch = self.matchIds[arr_start:arr_end]
            with open('tft_collected_match_ids_{}_{}_batch_{}.json'.format(self.region, self.date, num+1), 'w') as f:
                json.dump(batch, f)
        print("Completed splitting {} matchIds into {} batches".format(
            matchId_size, key_number))


summoner_collector = TFTSummonerCollector(SERVER)
summoner_collector.get_challengers()
summoner_collector.get_grandmasters()
summoner_collector.get_masters()

match_collector = TFTMatchCollector(SERVER)
match_collector.get_recent_matchIds()
match_collector.get_match_info(BATCH_NUM)
match_collector.load_match_info()

match_collector = TFTMatchCollector(SERVER)
match_collector.create_batches(5)

with open('tft_match_info_NA1_12082020_batch_1.json', 'r') as f:
    match_info_batch_1 = json.load(f)

with open('tft_match_info_NA1_12082020_batch_2.json', 'r') as f:
    match_info_batch_2 = json.load(f)

with open('tft_match_info_NA1_12082020_batch_3.json', 'r') as f:
    match_info_batch_3 = json.load(f)

with open('tft_match_info_NA1_12082020_batch_4.json', 'r') as f:
    match_info_batch_4 = json.load(f)

with open('tft_match_info_NA1_12082020_batch_5.json', 'r') as f:
    match_info_batch_5 = json.load(f)

print("Batch 1 retrieved cnt:", len(match_info_batch_1))
print("Batch 2 retrieved cnt:", len(match_info_batch_2))
print("Batch 3 retrieved cnt:", len(match_info_batch_3))
print("Batch 4 retrieved cnt:", len(match_info_batch_4))
print("Batch 5 retrieved cnt:", len(match_info_batch_5))

all_match_info = match_info_batch_1+match_info_batch_2 + \
    match_info_batch_3+match_info_batch_4+match_info_batch_5

with open('tft_match_info_NA1_12082020.json', 'w') as f:
    json.dump(all_match_info, f)
