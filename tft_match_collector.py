import json
from datetime import datetime
from riotapi import RiotAPI

class TFTMatchCollector(RiotAPI):
    def __init__(self, region, key):
        super().__init__(api_region=region, api_key=key)
        self.date = datetime.today().strftime("%m%d%Y")
        self.region = region
        
        self.puuid_list = []
        puuid_list_cnt = 0
        try:
            with open('tft_challenger_list_{}_{}.json'.format(self.region, self.date), 'r') as f:
                self.puuid_list += json.load(f)
            puuid_list_cnt+=1
            print("Loaded [challenger] puuid list")
        except:
            print("No existing [challenger] puuid list!")
        
        try:
            with open('tft_grandmaster_list_{}_{}.json'.format(self.region, self.date), 'r') as f:
                self.puuid_list = json.load(f)
            puuid_list_cnt+=1 
            print("Loaded [grandmaster] puuid list")  
        except:
            print("No existing [grandmaster] puuid list!")

        try:     
            with open('tft_master_list_{}_{}.json'.format(self.region, self.date), 'r') as f:
                self.puuid_list = json.load(f)
            puuid_list_cnt+=1  
            print("Loaded [master] puuid list")  
        except:
            print("No existing [master] puuid list!")
       
        if puuid_list_cnt == 0:
            print("ERROR: No puuids are imported, please check the filename!")
            exit()

    def get_recent_matchIds(self, match_cnt=20):
        print("Started to retrieve matchIds...")
        file_name = 'tft_match_ids_{}_{}.json'.format(self.region, self.date)
        self.matchIds = set()

        retrival_cnt = 0
        failure_cnt = 0

        for player_id in self.puuid_list:
            try:
                tmp_matchIds = RiotAPI.get_matchId_by_puuid(self, player_id, match_cnt)
                retrival_cnt += 1
            except:
                failure_cnt += 1
                continue
            self.matchIds = self.matchIds.union(set(tmp_matchIds))

            if retrival_cnt % 500 == 0:
                print("[{}]: retrieved: {} players, failed: {}".format(
                    datetime.now().strftime("%d/%m/%Y-%H:%M:%S"), retrival_cnt, failure_cnt))
                with open('tmp_'+file_name, 'w') as f:
                    json.dump(list(self.matchIds), f)

        with open(file_name, 'w') as f:
            json.dump(list(self.matchIds), f)

        print("------------------------------")
        print("Retrieved {} match ids, valid: {}".format(
            retrival_cnt*20, len(self.matchIds)))
        print("Failed to retrieve: {}".format(failure_cnt*20))
        print("Stored in {}".format(file_name))
        print("------------------------------")

    def get_match_info(self, batch_num=0):
        print("Started to retrieve match in-game data...")
        file_name = 'tft_match_ids_{}_{}'.format(self.region, self.date)
        file_format = '.json'

        if batch_num != 0:
            batch_name = '_batch_{}'.format(batch_num)
            try:
                with open(file_name+batch_name+file_format, 'r') as f:
                    self.matchIds = json.load(f)
            except:
                print("ERROR: Loading batch [{}] matchIds file failed!".format(batch_num))
                return
        else:
            try:
                with open(file_name+file_format, 'r') as f:
                    self.matchIds = json.load(f)
            except:
                print("ERROR: Failed to open the match id file!")            
                return

        file_name = 'tft_match_info_{}_{}'.format(self.region, self.date)
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
                if batch_num != 0:                    
                    with open('tmp_'+file_name+batch_name+file_format, 'w') as f:
                        json.dump(self.match_info, f)
                else:
                    with open('tmp_'+file_name+file_format, 'w') as f:
                        json.dump(self.match_info, f)
                        
        if batch_num != 0:                    
            with open(file_name+batch_name+file_format, 'w') as f:
                json.dump(self.match_info, f)
        else:
            with open(file_name+file_format, 'w') as f:
                json.dump(self.match_info, f)

        print("------------------------------")
        print("Retrieved {} matches with corresponding in-game data".format(retrival_cnt))
        print("Failed to retrieve: {}".format(failure_cnt))
        print("Stored in {}".format(file_name+file_format))
        print("------------------------------")

    def load_matchIds(self):
        file_name = 'tft_match_ids_{}_{}.json'.format(self.region, self.date)
        with open(file_name, 'r') as f:
            self.matchIds = json.load(f)

    def create_batches(self, key_number=5):
        try:
            self.load_matchIds()
        except:
            print("ERROR: Failed to open the match id file!")
            return

        matchId_size = len(self.matchIds)
        trunck_size = matchId_size//key_number + 1

        print("MatchId size:", matchId_size)
        print("API key number:", key_number)
        for num in range(key_number):
            arr_start = num*trunck_size
            arr_end = (num+1)*trunck_size
            batch = self.matchIds[arr_start:arr_end]
            with open('tft_match_ids_{}_{}_batch_{}.json'.format(self.region, self.date, num+1), 'w') as f:
                json.dump(batch, f)
        print("Completed splitting {} matchIds into {} batches!".format(
            matchId_size, key_number))

if __name__ == "__main__":
    test_region = 'NA1'
    test_key = 'RGAPI-XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX'

    collector = TFTMatchCollector(test_region, test_key)
    collector.get_recent_matchIds()
    collector.get_match_info()
    # collector.create_batches(key_number=5)