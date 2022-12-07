#!/usr/bin/python
'''
Attempt at using Functional Programming on simple code that accesss trello API
specifically use declarative approach with map/filter/reduce,
functions as first class citizens, partial application, and function composition
'''
import json
import os
import sys
import requests
import pdb
import pprint
from functools import reduce

url_prefix = 'https://api.trello.com/1/'
version = '1.3'

def get_creds(file_loc):
    ''' get api_key and token'''
    with open(os.path.expanduser(file_loc)) as json_file:
        creds = json.load(json_file)
    return (creds['api_key'], creds['token'])

def rest_request(full_url, req_type = 'get'):
    ''' make rest requests '''
    try:
        if req_type == 'get':
            res = requests.get(full_url)
        elif req_type == 'put':
            res = requests.put(full_url)
        elif req_type == 'post':
            res = requests.post(full_url)
        elif req_type == 'delete':
            res = requests.delete(full_url)
        else:
            print(f'wrong req_type: {req_type}')
            exit(1)
    except requests.exceptions.ConnectionError as er:
        print('Requests Connection error while talking to {}'.format(full_url))
        return 1
    if not '20' in str(res.status_code)[:2]:
        print('Incorrect return code: {}'.format(res.status_code))
    print('success, ret code: {}'.format(res.status_code))
    return res.json()

def append_trello_card(res_string, card):
    '''
    takes a trello card,
    uses its name and description,
    formats it into a multiline string
    and concatenates that onto previous string
    '''
    tmpname = f"        - {card['name']}\n"
    res_string += tmpname
    for onedesc_line in card.get('desc').split('\n'):
        tmpdesc = f"            {onedesc_line}\n"
        res_string += tmpdesc
    res_string += "\n"
    return res_string


def vpipe(list_of_funcs, coll):
    ''' attempt at implementing something like https://ramdajs.com/docs/#pipe '''
    res = list_of_funcs[0](coll)
    for counter, func in enumerate(list_of_funcs):
        if counter == 0:
            continue
        res = func(res)
    return res

def get_id(element):
    ''' self explanatory '''
    return element['id']

def find_by_name_closure(name):
    ''' takes elements and filters them by name '''
    def find_by_name_inner(coll):
        found = list(filter( lambda x: x.get('name').lower() == name.lower(), coll))[0]
        return found
    return find_by_name_inner

def rest_closure(pre, post):
    ''' wrapper around rest_request, adds pre, post and id '''
    def rest_inner(some_id):
        url = (f'{pre}{some_id}{post}')
        return rest_request(url)
    return rest_inner

def main():
    '''
    access trello via api to get cards we need and them print them out to a file
    and optionally archive them in trello
    '''
    api_key, token = get_creds('~/.trello_creds')
    idtoken = f"key={api_key}&token={token}"
    url_to_get_boards = f"{url_prefix}members/me/boards/?fields=name,id&key={api_key}&token={token}"
    #print(url_to_get_boards)
    trello_boards = rest_request(url_to_get_boards)

    '''
    Using functional paradigm, we feed results of one function into another
    in a consecutive "pipe" pattern. The result should be a list of trello cards
    in a specific trello list in a specific trello board.
    '''
    trello_cards = vpipe([
        find_by_name_closure('main'),
        get_id,
        rest_closure(f'{url_prefix}boards/', f'/lists?fields=name,id&key={api_key}&token={token}'),
        find_by_name_closure('INCOMING'),
        get_id,
        rest_closure(f'{url_prefix}lists/', f'/cards?fields=name,desc,id&{idtoken}'),
        ], trello_boards)

    # before trying functional approach with pipe
    '''
    board = list(filter( lambda x: x.get('name').lower() == board_name, trello_boards))[0]
    url_to_get_lists = f"{url_prefix}boards/{board['id']}/lists?fields=name,id&key={api_key}&token={token}"
    trello_lists = rest_request(url_to_get_lists)
    list_name = 'INCOMING'
    list_a = list(filter( lambda x: x.get('name') == list_name, trello_lists))[0]
    list_id = list_a['id']
    url_to_get_cards = f"{url_prefix}lists/{list_id}/cards?fields=name,desc,id&{idtoken}"
    # trello_cards has all cards in Incoming column
    trello_cards = rest_request(url_to_get_cards)
    print(f'INCOMING list has {len(trello_cards)} cards\n\n')
    #pprint.pprint(trello_cards)
    '''

    if len(sys.argv) <= 1 or 'print' in sys.argv[1]:
        res_string = reduce(append_trello_card, trello_cards, '')
        print(res_string)
        with open("resfile.txt", "w") as my_file:
            my_file.write(res_string)

    if len(sys.argv) > 1 and 'archive' in sys.argv[1]:
        for card in trello_cards:
            mod_url = f'{url_prefix}cards/{card["id"]}?&closed=true&{idtoken}'
            res_modify = rest_request(mod_url, 'put')


if __name__ == "__main__":
    main()
