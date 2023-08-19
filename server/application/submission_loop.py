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


END				= "\033[0m"

BLACK			= "\033[30m"
GREY			= "\033[90m"
RED				= "\033[31m"
GREEN			= "\033[32m"
YELLOW			= "\033[33m"
BLUE			= "\033[34m"
PURPLE			= "\033[35m"
CYAN			= "\033[36m"

HIGH_RED		= "\033[91m"
HIGH_GREEN		= "\033[92m"
HIGH_YELLOW		= "\033[93m"
HIGH_BLUE		= "\033[94m"
HIGH_PURPLE		= "\033[95m"
HIGH_CYAN		= "\033[96m"



class CustomFormatter(logging.Formatter):

	fmt = "[%(asctime)s] %(levelname)s: %(message)s"

	FORMATS = {
		logging.DEBUG: GREY + fmt + END,
		logging.INFO: GREY + "[%(asctime)s]" + END + " %(levelname)s: %(message)s",
		logging.WARNING: YELLOW + "[%(asctime)s] %(levelname)s: " + HIGH_YELLOW + "%(message)s" + END,
		logging.ERROR: RED + fmt + END,
		logging.CRITICAL: HIGH_RED + fmt + END,
	}

	def format(self, record):
		log_fmt = self.FORMATS.get(record.levelno)
		formatter = logging.Formatter(log_fmt)
		return formatter.format(record)




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
	SUB_STOLEN = 'already claimed'
	SUB_NOP = 'from NOP team'
	SUB_NOT_AVAILABLE = 'is not available'

	def submit_flags(self, flags):
		res = requests.put(current_app.config['SUB_URL'],
							headers={'X-Team-Token': current_app.config['TEAM_TOKEN']},
							json=flags,
							timeout=(current_app.config['SUB_INTERVAL'] / current_app.config['SUB_LIMIT']))

		# Check if the gameserver sent a response about the flags or if it sent an error
		if 'application/json' in res.headers['Content-Type']:
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

		logger.handlers.clear()
		custom_handler = logging.StreamHandler()
		custom_handler.setLevel(logging.DEBUG)
		custom_handler.setFormatter(CustomFormatter())
		logger.addHandler(custom_handler)

		if current_app.config["SUB_PROTOCOL"] not in submitters.keys():
			logger.error(f"Invalid SUB_PROTOCOL {current_app.config['SUB_PROTOCOL']}. Valid values are {list(submitters.keys())}")
			return
		submitter = submitters[current_app.config["SUB_PROTOCOL"]]()

		# Let's not make it start right away
		time.sleep(5)
		logger.info(f'{GREEN}starting.{END}')
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

					if type(submit_result) == dict:
						# {'code': 'RATE_LIMIT', 'message': '[RATE_LIMIT] Rate limit exceeded'}
						if submit_result.get('code', '') == 'RATE_LIMIT':
							msg = submit_result.get('message', '')
							if msg:
								logger.warning(f'{msg}')
							else:
								logger.error(f'Submit result: {submit_result}')
						else:
							logger.error(f'Submit result: {submit_result}')
						time.sleep(current_app.config['SUB_INTERVAL'])
						break

					# executemany() would be better, but it's fine like this.
					accepted = 0
					old = 0
					nop = 0
					yours = 0
					invalid = 0
					update_flag = '''
					UPDATE flags
					SET status = ?, server_response = ?
					WHERE flag = ?
					'''

					for item in submit_result:
						if submitter.SUB_INVALID.lower() in item['msg'].lower():
							cursor.execute(update_flag, (current_app.config['DB_SUB'], current_app.config['DB_ERR'], item['flag']))
							invalid += 1
						elif submitter.SUB_YOUR_OWN.lower() in item['msg'].lower():
							cursor.execute(update_flag, (current_app.config['DB_SUB'], current_app.config['DB_ERR'], item['flag']))
							yours += 1
						elif submitter.SUB_NOP.lower() in item['msg'].lower():
							cursor.execute(update_flag, (current_app.config['DB_SUB'], current_app.config['DB_ERR'], item['flag']))
							nop += 1
						elif submitter.SUB_OLD.lower() in item['msg'].lower():
							cursor.execute(update_flag, (current_app.config['DB_SUB'], current_app.config['DB_EXP'], item['flag']))
							old += 1
						elif (submitter.SUB_ACCEPTED.lower() in item['msg'].lower() or
								submitter.SUB_STOLEN.lower() in item['msg'].lower()):
							cursor.execute(update_flag, (current_app.config['DB_SUB'], current_app.config['DB_SUCC'], item['flag']))
							accepted += 1
						else:
							logger.error(f'{item}')
						i += 1

					msg = f'Submitted {GREEN}{len(flags)}{END} flags: {GREEN}{accepted} Accepted{END}'
					if old:
						msg += f' {CYAN}{old} Old{END}'
					if nop:
						msg += f' {HIGH_PURPLE}{nop} NOP{END}'
					if yours:
						msg += f' {HIGH_YELLOW}{yours} Yours{END}'
					if invalid:
						# logger.warning(f'{submit_result}')
						msg += f' {RED}{invalid} Invalid{END}'
					logger.info(msg)


			except requests.exceptions.RequestException as e:
				logger.warning('Could not send the flags to the server, retrying...')
				logger.warning(f'{e}')
			except Exception as e:
				logger.critical(f'{e}')
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
