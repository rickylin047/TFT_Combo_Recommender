import gc
import json
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import tensorflow as tf

# Champion data
def loadChampionsList():
    with open('./set4/champions.json') as f:
        champions = json.load(f)
    champions_id = []
    champions_cost = []
    for i in champions:
        champions_id.append(i['championId'])
        champions_cost.append(i['cost'])
    return champions_id, champions_cost

# Item data
def loadItemsList():
    with open('./set4/items.json') as f:
        items = json.load(f)

    items_name = [i['name'] for i in items]
    items_id = [i['id'] for i in items]
    return items_name, items_id

def transformInput(units, is_train=True):
    N = len(units)
    X_tier = np.zeros((N, len(champions_id)))
    X_item = np.zeros((N, len(champions_id)))
    units = np.array(units)
    del_ls = []
    for i in range(N):
        if is_train:
            if len(units[i]) == 8:
                for j in units[i]:
                    X_tier[i, champions_id.index(
                        j['character_id'])] = j['tier']
                    # match item count
                    if len(j['items']) > 0:
                        X_item[i, champions_id.index(
                            j['character_id'])] = len(j['items'])
            else:
                del_ls.append(i)
        else:
            for j in units[i]:
                X_tier[i, champions_id.index(j['character_id'])] = j['tier']
                # match item count
                if len(j['items']) > 0:
                    X_item[i, champions_id.index(
                        j['character_id'])] = len(j['items'])

    X_con = np.append(X_tier, X_item, axis=1).astype('int')
    if not is_train:
        return X_con
    X_con = np.delete(X_con, del_ls, axis=0)
    return X_con, del_ls

def transformOutput(placement):
    placement = placement.astype(int)
    return np.delete(np.array((max(placement) - placement) / (max(placement) - min(placement))), del_ls)

def addNewChampions(test, items_num=0, cost_limit=5):
    ls = list(transformInput([test], is_train=False)[0])  # Format input
    arr_c = np.array([ls for i in range(len(champions_id))])
    for i in range(len(champions_id)):
        if arr_c[i, i] == 0 and champions_cost[i] <= cost_limit:
            arr_c[i, i] = 2
            arr_c[i, i+len(champions_id)] = items_num
    return arr_c
    
def completeChampions(test, items_num=1):
    while len(test) < 8:
        win_rate_old = model.predict(transformInput([test], is_train=False))
        arr_c = addNewChampions(test, items_num)
        win_rate = model.predict(arr_c)
        index = np.where(win_rate == max(win_rate))[0][0]
        print('-----------------------')
        print('Champion count:', len(test))
        print('Champions (before):', [i['character_id'] for i in test])
        print('New champion:', champions_id[index])
        test.append({'character_id': champions_id[index], 'tier': 2, 'items': []})
        print('Champions (after):', [i['character_id'] for i in test])
        print('Win rate:', win_rate_old[0], '-->', max(win_rate))

def findTestComboList(data, combo_cnt=20):
    # Find placement 1 data index
    cnt = 0
    combo_index = []
    for i in range(data.shape[0]):
        if data.iloc[i, 0] == 1 and len(data.iloc[i, 1]) == 8:
            combo_index.append(i)
            cnt += 1
        if (cnt == combo_cnt):
            break
    return combo_index

def getTestCombo(data, index):
    print("Test combo placement:", data['placement'][index])
    units = data['units'][index]
    print("Original test combo champions:",end=' ')
    for unit in units:
        print(unit['character_id'], end=' ')
    print()
    return units

if __name__ == "__main__":
    with open('tft_match_info_NA1_12082020.json', 'r') as f:
        data_na = json.load(f)

    df = pd.DataFrame(columns=(['companion', 'gold_left', 'last_round', 'level', 'placement',
                                'players_eliminated', 'puuid', 'time_eliminated', 'total_damage_to_players', 'traits', 'units']))

    all_participants = []
    for game in data_na:
        for player in game['participants']:
            all_participants.append(player)

    data = df.append(all_participants)
    data.drop(['companion', 'gold_left', 'last_round', 'level', 'puuid', 'players_eliminated',
            'time_eliminated', 'total_damage_to_players', 'traits'], axis=1, inplace=True)
    print(data)
    del data_na
    gc.collect() 

    champions_id, champions_cost = loadChampionsList()
    items_name, items_id = loadItemsList()

    X, del_ls = transformInput(data['units'])
    y = transformOutput(data['placement'])
    # print(X.shape)
    # print(y.shape)    

    X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=0)
    # print(X_train.shape)
    # print(y_train.shape)

    model = tf.keras.models.Sequential([
        tf.keras.layers.InputLayer(X.shape[1]),
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dense(1)
    ])

    model.compile(optimizer='adam',
                loss='mse',
                metrics=['accuracy'])

    model.summary()    

    tf.random.set_seed(0)
    model.fit(X_train, y_train, epochs=10, batch_size=64)
    model.evaluate(X_test, y_test)

    test_combo_list = findTestComboList(data, 10)
    print(test_combo_list)

    test_combo = getTestCombo(data, test_combo_list[0])

    completeChampions(test_combo[:6])