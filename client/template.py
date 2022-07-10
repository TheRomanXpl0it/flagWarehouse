#!/usr/bin/env python3
import sys
sys.path.insert(1, '../imports/')
sys.path.insert(1, 'imports/')

import utils
import requests
import json
from bs4 import BeautifulSoup
from pwn import *


IP_ADDRESS = sys.argv[1]

# MODIFY THIS PART !!!
SERVICE = "TEST"
PORT = 1234
# MODIFY THIS PART !!!
TARGET_URL = f'http://{IP_ADDRESS}:{PORT}'


res = requests.get('https://6.enowars.com/scoreboard/attack.json', timeout=10)
teams = json.loads(res.text)
#print(teams)


# Adjust if needed
valid_users = teams.get('services').get(SERVICE).get(IP_ADDRESS)
#print(valid_users)

headers = { 
    'User-Agent': utils.user_agent(),
    }
    
# Adjust if needed
data = {
    'email' : utils.email(),
    'username' : utils.username(max=12),
    'password' : utils.password(max=12)
}

for user in valid_users:

    s = requests.Session()
    res = s.get(TARGET_URL + '/register', headers=headers, data=data)
    res = s.get(TARGET_URL + '/login', headers=headers, data=data)


    soup = BeautifulSoup(res, features="html5lib")
    print(soup)

