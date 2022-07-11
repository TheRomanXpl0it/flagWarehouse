#!/usr/bin/env python3
import os
import sys
sys.path.insert(1, '../imports/')
sys.path.insert(1, 'imports/')

import utils
import requests
import json
from bs4 import BeautifulSoup
from pwn import *

# Use this function to print stuff to client
def log(message):
    print(message, flush=True)

IP_ADDRESS = sys.argv[1]
dir_path = os.path.dirname(os.path.realpath(__file__)) + '/../'
flag_ids = {}
with open(dir_path + 'flag_ids.json', 'r', encoding='utf-8') as f:
    flag_ids = json.loads(f.read())
    #log(flag_ids)

  
# Adjust if needed
headers = { 
    'User-Agent': utils.user_agent(),
    }
data = {
    'email' : utils.email(),
    'username' : utils.username(max=12),
    'password' : utils.password(max=12)
}


# Adjust if needed
SERVICE = "TEST"
PORT = 1234
TARGET_URL = f'http://{IP_ADDRESS}:{PORT}'

valid_users = flag_ids.get('services', {}).get(SERVICE, {}).get(IP_ADDRESS, [])
#print(valid_users)

for user in valid_users:

    s = requests.Session()
    res = s.get(TARGET_URL + '/register', headers=headers, data=data)
    res = s.get(TARGET_URL + '/login', headers=headers, data=data)


    soup = BeautifulSoup(res, features="html5lib")
    print(soup)

