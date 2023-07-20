import sys
if __name__=='__main__':
    sys.path.insert(0,r'C:\Users\godin\Python\planny\src')

import json
import random
import string
import requests
from typing import Optional, Dict, Any, List, Tuple
from typing import OrderedDict as tOrderedDict
from collections import OrderedDict

from planny.parser import search_and_consume, DURATION_MIN_PAT, parse_time
from planny.task import Task, TASK_DEFAULT_DURATION

JSON_Dict = Dict[str, Any]
PLANNY = 'planny'
STAGE1 = 'Stage 1'
COMPLETED = 'Completed'


IdList = str
IdTask = str
Name = str

def parse_card_name(card_dict):
    snew, d = parse_time(card_dict['name'])
    # duration_match, name = search_and_consume(DURATION_MIN_PAT, card_dict['name'])
    # duration = int(duration_match.group("minutes")) if duration_match else TASK_DEFAULT_DURATION
    card_dict['name'] = snew

    card_dict['duration'] = d.get('duration', TASK_DEFAULT_DURATION)
    return card_dict

class Trello:
    def __init__(self, json_path: str):
        with open(json_path) as f:
            d = json.load(f)
        self._key = d['key']
        self._token = d['token']
        self.base_url = 'https://api.trello.com/1'
        self.board_name_to_id = self.get_board_name_to_id()
        self.fantasies_id = '5d01dee644c2972d040647d4'
        self.planny_id = '61273246e757845c685fc6a5'

    ######### BOARDS ###########
    def get_board_name_to_id(self) -> tOrderedDict[Name, IdList]:
        """ maps between boards names and boards ids"""
        endpoint = f'members/me/boards'
        data = {'fields':'name,id'}
        list_of_board_dicts = self._call(endpoint, data)
        board_name_to_id = OrderedDict()
        for d in list_of_board_dicts:
              board_name_to_id [ d['name'] ] = d['id']
        return board_name_to_id

    def get_board(self, board_name="", board_id="") -> JSON_Dict:
        if not board_id:
            board_id = self.board_name_to_id[board_name]
        endpoint = f"boards/{board_id}"
        res = self._call(endpoint, method="GET")
        board_dict = {key: res[key] for key in ['id','name']}
        return board_dict
    
    def create_board(self, board_name):
        """ returns board_dict {'id', 'name'}"""
        endpoint = 'boards/'
        data = {'name': board_name}
        res = self._call(endpoint, data, method="POST")
        board_dict = {key: res[key] for key in ['id','name']}
        self.board_name_to_id[board_name] = res['id']
        return board_dict

    def create_temp_board(self):
        board_name = "".join(random.choices(string.ascii_lowercase, k=10))
        return self.create_board(board_name)
    
    def delete_board(self, board_name="", board_id=""):
        assert board_name or board_id
        board_dict = self.get_board(board_name,board_id)
        board_id, board_name = board_dict['id'], board_dict['name']
        endpoint = f"boards/{board_id}"
        res = self._call(endpoint, method="DELETE")
        del self.board_name_to_id[board_name]
        return res

    def get_board_total_completed_cards(self, board_name) -> Tuple[int, int]:
        """ returns # of cards in board + # of completed cards in board"""
        board_id = self.board_name_to_id[board_name]
        endpoint = f"boards/{board_id}/cards"
        fields = {"fields":["id"]} # [{'id':213}, {}]
        cards = self._call(endpoint, fields)
        total_num_of_cards = len(cards)
        # completed cards
        completed_list_id = self.get_list_id_from_name(board_name, COMPLETED)
        endpoint = f"lists/{completed_list_id}/cards"
        fields = {"fields":["id"]} # [{'id':, 123}, {}]
        list_completed_cards_res = self._call(endpoint, fields)
        num_completed_cards = len(list_completed_cards_res)
        return total_num_of_cards, num_completed_cards

    ######### LISTS ###########
    
    def get_lists_name_id(self, board_name) -> tOrderedDict:
        """ returns mapping between lists names and ids"""
        board_id = self.board_name_to_id[board_name]
        endpoint = f"boards/{board_id}/lists"
        list_of_lists_dicts  = self._call(endpoint,{'fields':'name,id'}) # [{'id':"", 'name':""}, {},...]
        lists_name_id = OrderedDict()
        for d in list_of_lists_dicts:
            lists_name_id[ d['name'] ] = d['id']
            lists_name_id[ d['id'] ] = d['name']
        return lists_name_id
    
    def get_first_list_name_id(self, board_name) -> Tuple[Name, IdList]:
        """ returns first_list_name and first_list_id if exists, empty strings otherwise"""
        lists_name_id_list = list(self.get_lists_name_id(board_name).items()) # [('board1',1), (1,'board1'), ('board2',2),...]
        if not lists_name_id_list:
            return "", ""
        if lists_name_id_list[0][0] == COMPLETED:
            return lists_name_id_list[2][0], lists_name_id_list[2][1]
            # if len (lists_name_id_list) <= 2:
            #     return COMPLETED, lists_name_id_list[0][1]

        return lists_name_id_list[0][0], lists_name_id_list[0][1]
    
    def get_list_id_from_name(self, board_name, list_name) -> IdList:
        " returns empty str if list_name doesn't exist"
        lists_name_to_id = self.get_lists_name_id(board_name)
        return lists_name_to_id.get(list_name, "")

    def get_list_name_from_id(self, board_name, list_id) -> Name:
        lists_name_to_id = self.get_lists_name_id(board_name)
        return lists_name_to_id.get(list_id, "")
    
    def get_list_cards(self, board_name, list_name="", list_id="") -> List[JSON_Dict]:
        """ returns an ordered list containing dicts of all the list cards
        where card={'id', 'name', 'pos', 'idList', 'due', 'desc', 'list_name'}"""
        assert list_name or list_id
        if not list_id: list_id = self.get_list_id_from_name(board_name, list_name)
        elif not list_name: list_name = self.get_list_name_from_id(board_name, list_id)

        endpoint = f"lists/{list_id}/cards"
        data = {"fields":["id", "name", "pos", "idList", "due", "desc"]} # [{'id':, 'name':, "pos"}, {}]
        list_cards_res = self._call(endpoint, data=data) # [{'id':, 'name':, "pos"}, {}]
        for card in list_cards_res: 
            card['list_name'] = list_name
        return list_cards_res
    
    def add_list(self, board_name, list_name, pos="top") -> JSON_Dict:
        board_id = self.board_name_to_id[board_name]
        data = {'name':list_name,'pos':pos}
        endpoint = f"boards/{board_id}/lists"
        res = self._call(endpoint,data=data, method="POST")
        new_list = {'id': res['id'], 'pos': res['pos']}
        return new_list
    
    def prepend_list(self,board_name, list_name) -> JSON_Dict: return self.add_list(board_name, list_name, pos="top")
    def append_list(self,board_name, list_name) -> JSON_Dict: return self.add_list(board_name, list_name, pos="bottom")
    
    def add_list_if_needed(self, board_name, list_name) -> IdList:
        """ creates list if one doesn't exist. returns idList"""
        list_id = self.get_list_id_from_name(board_name, list_name)
        if list_id == "": # list doesn't exist
            list_id = self.add_list(board_name, list_name)['id']
        return list_id

    def move_list(self, list_id, new_board_id):
        endpoint = f"lists/{list_id}/idBoard"
        data = {'value':new_board_id}
        return self._call(endpoint,data, method="PUT")
    
    def delete_list(self, board_name, list_name="", list_id=""):
        assert list_name or list_id
        if not list_id:
            list_id = self.get_list_id_from_name(board_name, list_name)
        if not list_id:
            print(f"trello::delete_list({board_name},{list_name}), {list_name} doesn't exist")
        
        temp_board_dict = self.create_temp_board()
        self.move_list(list_id, temp_board_dict['id'])
        self.delete_board(board_name=temp_board_dict['name'])

    ######### CARDS ###########
    def get_all_board_cards(self, board_name):
        board_id = self.board_name_to_id[board_name]
        endpoint = f"boards/{board_id}/cards"
        fields = {"fields":["id", "name", "pos", "idList", "due"]} # [{'id':, 'name':, "pos"}, {}]
        cards = self._call(endpoint, fields)
        return cards

    def get_first_list_cards(self, board_name) -> List[JSON_Dict]:
        """ returns a list of dicts + first_list_name + id, each dict a card,
        where card={'id', 'name', 'pos', 'idList', 'due', 'desc', 'list_name'}"""
        first_list_name, first_list_id = self.get_first_list_name_id(board_name)
        if not first_list_name or first_list_name == COMPLETED:
            return None # type: ignore
        return self.get_list_cards(board_name, list_id=first_list_id)
   
    def get_first_card(self, board_name) -> Task:
        """ returns first task on first list, or empty dict if board has no cards. """
        first_list_cards = self.get_first_list_cards(board_name)
        num_cards_in_list = len (first_list_cards)
        first_card = parse_card_name(first_list_cards[0])
        # num_total_cards, num_completed_cards = self.get_board_total_completed_cards(board_name)
        task = Task(name=first_card['name'],
                    duration=first_card['duration'],
                    description=first_card['desc'],
                    project=board_name,
                    list=first_card['list_name'],
                    num_cards_in_list=num_cards_in_list,
                    origin='trello',
                    trello_id=first_card['id'])
        task.next_event_name = first_list_cards[1]['name'] if num_cards_in_list > 1 else 'List end'
        return task
    
    def switch_first_and_second_cards(self, board_name) -> Task:
        """ switches between first and second cards on first list of board, returns the new top (original second)"""
        first_list_cards = self.get_first_list_cards(board_name)
        num_cards_in_list = len (first_list_cards)
        # get first card
        first_card = first_list_cards[0]
        second_card = parse_card_name(first_list_cards[1])
        # switch positions
        midpos = (float(first_card['pos']) + float(second_card['pos'])) / 2
        self.update_card(first_card['id'], data={'pos': midpos})
        self.update_card(second_card['id'], data={'pos': first_card['pos']})

        # num_total_cards, num_completed_cards = self.get_board_total_completed_cards(board_name)
        task = Task(name = second_card['name'],
                    duration = second_card['duration'],
                    description = second_card['desc'],
                    project = board_name,
                    list = second_card['list_name'],
                    num_cards_in_list = num_cards_in_list,
                    origin = 'trello',
                    trello_id = second_card['id'],
                    next_event_name = first_card['name'])        
        return task
    
    def add_card(self, board_name, list_name, name, desc='', pos="top") -> JSON_Dict:
        """ add cards to list in board. creates list if one doesn't exist"""
        list_id = self.add_list_if_needed(board_name, list_name)
        return self.add_card_by_list_id(list_id, name, pos)

    def add_card_by_list_id(self, list_id, name, desc='', pos="top") -> JSON_Dict:
        endpoint = "cards"
        data = {'name':name, 'pos': pos, 'idList':list_id}
        if desc: data['desc'] = desc
        res = self._call(endpoint, data, method="POST")
        card_dict = { key:res[key] for key in ['id', 'idList', 'idBoard']}
        return card_dict
    
    def prepend_card(self, board_name, list_name, name): return self.add_card(board_name, list_name, name, desc='', pos="top")
    def append_card(self, board_name, list_name, name): return self.add_card(board_name, list_name, name, desc='', pos="bottom")

    def prepend_second_card_to_board(self, board_name: str, name: str, desc: str=''):
        """ add card to first list, in second place"""
        # get first list cards
        first_list_cards = self.get_first_list_cards(board_name)
        if first_list_cards is None: # if board has no first list / only Complete
            list_dict = self.add_list(board_name, 'misc')
            first_list_id = list_dict['id']
            pos = "top"
        elif len(first_list_cards) == 0: # there's a first list but it's empty
            first_list_id = self.get_first_list_name_id(board_name)[1]
            pos = "top"
        elif len(first_list_cards) == 1: # only one card
            first_list_id = first_list_cards[0]['idList']
            pos = "bottom"
        else:
            first_list_id = first_list_cards[0]['idList']
            pos = (float(first_list_cards[0]['pos']) + float(first_list_cards[1]['pos'])) / 2

        self.add_card_by_list_id(list_id=first_list_id, name=name, desc=desc, pos=pos)
        
    def update_card(self, card_id, data):
        endpoint = f"cards/{card_id}"
        self._call(endpoint, data, method="PUT")
    
    def prepend_card_to_board(self, board_name: str, name: str):
        first_list_name, first_list_id = self.get_first_list_name_id(board_name)
        if not first_list_name or first_list_name == COMPLETED:
            first_list_id = self.add_list(board_name, STAGE1, pos="top")
        return self.add_card_by_list_id(first_list_id, name, pos="top")

    def delete_first_card(self, board_name):
        first_card = self.get_first_card(board_name)
        if first_card:    
            endpoint = f"cards/{first_card.trello_id}"
            return self._call(endpoint, method="DELETE")
    
    def complete_first_card(self, board_name):
        first_list_cards = self.get_first_list_cards(board_name)
        if not first_list_cards:
            return
        first_card_dict = first_list_cards[0]
        complete_list_id = self.add_list_if_needed(board_name, COMPLETED)
        self.update_card(first_card_dict['id'], {'idList': complete_list_id})
        # if this was last card on first playlist, delete this list
        if len (first_list_cards) == 1:
            first_list_id = first_card_dict['idList']
            self.delete_list(board_name, list_id=first_list_id)
    
    ######### GENERAL ###########
    
    def _call(self, endpoint: str,
                    data: Optional[JSON_Dict] = None,
                    method: str = 'GET'):
        if not data: data = {}
        data['key'] = self._key
        data['token'] = self._token
        
        url = f'{self.base_url}/{endpoint}'
        
        if method== 'GET':
            result = requests.get(url, data)
        elif method == 'POST':
            result = requests.post(url, data)
        elif method == 'PUT':
            result = requests.put(url, data)
        elif method =='DELETE':
            result = requests.delete(url, data=data)
        else: # method 
            raise Exception(f'_call(), unknown method: {method}')
        
        if not result.status_code == requests.codes.ok:
            raise Exception(f'Trello API failed with code {result.status_code}: {result.text}, {method} {url}')

        return result.json()

def main():
    json_path = r'C:\Users\godin\Python\planny\src\credentials\trello.json'
    t = Trello(json_path)
    for i in range(19,5-1, -1):
        name = f'pg. {i} 5min'
        t.add_card(board_name="Stats", list_name="Rethinking",name=name)
    print('finished')

if __name__=='__main__':
    main()