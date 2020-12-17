import time
import requests
from ratelimit import limits, sleep_and_retry

class RiotAPI():
    REGIONs = {
        'NA1': 'americas',
        'EUN1': 'europe',
        'EUW1': 'europe',
        'KR': 'asia'
    }

    URLs = {
        'base': 'https://{region}.api.riotgames.com/{url}',
        'tft_challenger': '/tft/league/v1/challenger',
        'tft_grandmaster': '/tft/league/v1/grandmaster',
        'tft_master': '/tft/league/v1/master',
        'tft_summoner_by_summonerId': '/tft/summoner/v1/summoners/{encryptedSummonerId}',
        'tft_match_by_puuid': 'tft/match/v1/matches/by-puuid/{puuid}/ids',
        'tft_match_by_matchId': 'tft/match/v1/matches/{matchId}'
    }

    def __init__(self, api_region, api_key):
        self.region = api_region
        self.api_key = api_key

    @sleep_and_retry
    @limits(calls=4, period=5)
    def _request(self, region, api_url, params={}):
        args = {
            'api_key': self.api_key
        }

        for key, val in params.items():
            if key not in args:
                args[key] = val

        request_success = False
        while not request_success:

            response = requests.get(
                self.URLs['base'].format(
                    region=region,
                    url=api_url
                ),
                params=args
            )

            if response.status_code == 200:
                request_success = True
            elif response.status_code == 403:
                print("Riot API - {} Forbidden".format(response.status_code))
                raise Exception('API response: {} URLs: {}\nPlease check your API key!'.format(
                    response.status_code, response.url))
            elif response.status_code == 429:
                print("Riot API - {} Rate limit exceeded".format(response.status_code))
                print('Retry in 125s')
                time.sleep(125)
            elif response.status_code == 503:
                print("Riot API - {} Service unavailable".format(response.status_code))
                print('Retry in 30s')
                time.sleep(30)
            else:
                print('Riot API request failed:', response.status_code)
                raise Exception('API response: {} URLs: {}'.format(
                    response.status_code, response.url))

        return response.json()

    def get_tft_challenger(self):
        api_url = self.URLs['tft_challenger']
        return self._request(self.region, api_url)

    def get_tft_grandmaster(self):
        api_url = self.URLs['tft_grandmaster']
        return self._request(self.region, api_url)

    def get_tft_master(self):
        api_url = self.URLs['tft_master']
        return self._request(self.region, api_url)

    def get_summoner_by_summonerId(self, summonerId):
        api_url = self.URLs['tft_summoner_by_summonerId'].format(
            encryptedSummonerId=summonerId
        )
        return self._request(self.region, api_url)

    def get_matchId_by_puuid(self, puuid, match_cnt=20):
        api_url = self.URLs['tft_match_by_puuid'].format(
            puuid=puuid,
            count=match_cnt
        )
        return self._request(self.REGIONs[self.region], api_url)

    def get_match_by_matchId(self, matchId):
        api_url = self.URLs['tft_match_by_matchId'].format(
            matchId=matchId
        )
        return self._request(self.REGIONs[self.region], api_url)