import logging
import time
from datetime import datetime, timedelta
from queue import Queue
import json
from typing import List

import requests
from flask import Flask, current_app
from ordered_set import OrderedSet

from . import db


class Submitter:
    def submit_flags(self, flags: List[str]):
        """
        Should return
        [
            {"flag":"<flag1>","msg":"status from server"},
            {"flag":"<flag2>","msg":"status from server"},
            ...
        ]
        """
        raise NotImplementedError()

class DummySubmitter(Submitter):
    SUB_ACCEPTED = 'accepted'
    SUB_INVALID = 'invalid'
    SUB_OLD = 'too old'
    SUB_YOUR_OWN = 'your own'
    SUB_STOLEN = 'already stolen'
    SUB_NOP = 'from NOP team'
    SUB_NOT_AVAILABLE = 'is not available'

    def submit_flags(self, flags):
        res = []
        for flag in flags:
            current_app.logger.debug(f'Dummy submitter: submitting {flag}')
            res.append({"flag":flag,"msg":self.SUB_ACCEPTED})
        return res

class CCITSubmitter(Submitter):
    SUB_ACCEPTED = 'accepted'
    SUB_INVALID = 'invalid'
    SUB_OLD = 'too old'
    SUB_YOUR_OWN = 'your own'
    SUB_STOLEN = 'already stolen'
    SUB_NOP = 'from NOP team'
    SUB_NOT_AVAILABLE = 'is not available'

    def submit_flags(self, flags):
        res = requests.put(current_app.config['SUB_URL'],
                            headers={'X-Team-Token': current_app.config['TEAM_TOKEN']},
                            json=flags,
                            timeout=(current_app.config['SUB_INTERVAL'] / current_app.config['SUB_LIMIT']))

        # Check if the gameserver sent a response about the flags or if it sent an error
        if res.headers['Content-Type'] == 'application/json; charset=utf-8':
            return json.loads(res.text)
        else:
            current_app.logger.error(f'Received this response from the gameserver:\n\n{res.text}\n')
            return []

from pwnlib.tubes.remote import remote
import urllib.parse

class FaustSubmitter(Submitter):
    """
    https://ctf-gameserver.org/submission/
    SUB_URL should be of this format: tcp://submission.faustctf.net:666/
    """
    SUB_ACCEPTED = 'OK'
    SUB_INVALID = 'INV'
    SUB_OLD = 'OLD'
    SUB_YOUR_OWN = 'OWN'
    SUB_STOLEN = 'DUP'
    SUB_NOP = 'INV'
    SUB_NOT_AVAILABLE = 'ERR'

    def __init__(self):
        url = urllib.parse.urlsplit(current_app.config['SUB_URL'])
        self.host = url.hostname
        self.port = url.port
        current_app.logger.info(f'{self.host}, {self.port}')

    def submit_flags(self, flags):
        flags = set(flags)

        try:
            s = remote(self.host, self.port, timeout=current_app.config['SUB_INTERVAL'] / current_app.config['SUB_LIMIT'])
            line = s.recvline()
            while line.strip() != b'':
                line = s.recvline()

            res = []
            for flag in flags:
                s.sendline(flag.encode())
                line = s.recvline().decode()

                line = line.split()
                if len(line) < 1 or line[0] not in flags:
                    print('submitter: skipping response line', line)
                    continue

                res.append({'flag':line[0], 'msg':line[1]})
                print(res)

            return res

        except Exception as e:
            print(e)
            return []

submitters = {
    'dummy': DummySubmitter,
    'ccit': CCITSubmitter,
    'faust': FaustSubmitter
}


class OrderedSetQueue(Queue):
    """Unique queue.

    Elements cannot be repeated, so there's no need to traverse it to check.
    LIFO ordered and thread-safe.
    """

    def _init(self, maxsize):
        self.queue = OrderedSet()

    def _put(self, item):
        self.queue.add(item)

    def _get(self):
        return self.queue.pop()


def loop(app: Flask):
    with app.app_context():
        logger = current_app.logger  # Need to get it before sleep, otherwise it doesn't work. Don't know why.

        if current_app.config["SUB_PROTOCOL"] not in submitters.keys():
            logger.error(f"Invalid SUB_PROTOCOL {current_app.config['SUB_PROTOCOL']}. Valid values are {list(submitters.keys())}")
            return
        submitter = submitters[current_app.config["SUB_PROTOCOL"]]()

        # Let's not make it start right away
        time.sleep(5)
        logger.info('starting.')
        database = db.get_db()
        queue = OrderedSetQueue()
        while True:
            s_time = time.time()
            expiration_time = (datetime.now() - timedelta(seconds=current_app.config['FLAG_ALIVE'])).replace(microsecond=0).isoformat(sep=' ')
            cursor = database.cursor()
            cursor.execute('''
            SELECT flag
            FROM flags
            WHERE time > ? AND status = ? AND server_response IS NULL
            ORDER BY time DESC
            ''', (expiration_time, current_app.config['DB_NSUB']))
            for flag in cursor.fetchall():
                queue.put(flag[0])
            i = 0
            queue_length = queue.qsize()
            try:
                # Send N requests per interval
                while i < min(current_app.config['SUB_LIMIT'], queue_length):
                    # Send N flags per request
                    flags = []
                    for _ in range(min(current_app.config['SUB_PAYLOAD_SIZE'], queue_length)):
                        flags.append(queue.get())

                    submit_result = submitter.submit_flags(flags)

                    # executemany() would be better, but it's fine like this.
                    for item in submit_result:
                        if (submitter.SUB_INVALID.lower() in item['msg'].lower() or
                                submitter.SUB_YOUR_OWN.lower() in item['msg'].lower() or
                                submitter.SUB_STOLEN.lower() in item['msg'].lower() or
                                submitter.SUB_NOP.lower() in item['msg'].lower()):
                            cursor.execute('''
                            UPDATE flags
                            SET status = ?, server_response = ?
                            WHERE flag = ?
                            ''', (current_app.config['DB_SUB'], current_app.config['DB_ERR'], item['flag']))
                        elif submitter.SUB_OLD.lower() in item['msg'].lower():
                            cursor.execute('''
                            UPDATE flags
                            SET status = ?, server_response = ?
                            WHERE flag = ?
                            ''', (current_app.config['DB_SUB'], current_app.config['DB_EXP'], item['flag']))
                        elif submitter.SUB_ACCEPTED.lower() in item['msg'].lower():
                            cursor.execute('''
                            UPDATE flags
                            SET status = ?, server_response = ?
                            WHERE flag = ?
                            ''', (current_app.config['DB_SUB'], current_app.config['DB_SUCC'], item['flag']))
                        i += 1
            except requests.exceptions.RequestException:
                logger.error('Could not send the flags to the server, retrying...')
            except TypeError:
                # logger.info(str(submit_result))
                logger.error('Limit Rate exceeded, retrying...')
                time.sleep(current_app.config['SUB_INTERVAL'])
            finally:
                # At the end, update status as EXPIRED for flags not sent because too old
                cursor.execute('''
                                    UPDATE flags
                                    SET server_response = ?
                                    WHERE status LIKE 'NOT_SUBMITTED' AND time <= ?
                                    ''', (current_app.config['DB_EXP'], expiration_time))
                database.commit()
                duration = time.time() - s_time
                if duration < current_app.config['SUB_INTERVAL']:
                    time.sleep(current_app.config['SUB_INTERVAL'] - duration)
