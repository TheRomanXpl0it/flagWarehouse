class Config(object):

	# Ooisv4YG7zw6wa9f

	# CHANGE THIS
	TEAM = 0
	TEAM_TOKEN = '' # team token for flag submission

	WEB_PASSWORD = 'password'
	API_TOKEN = 'custom_token'
	SECRET_KEY = 'not_secret_key'

	# Teams
	YOUR_TEAM = f'10.60.{TEAM}.1'
	TEAMS = [f'10.60.{i}.1' for i in range(1, 87)] # number of teams
	TEAMS.remove(YOUR_TEAM)

	ROUND_DURATION = 120
	FLAG_ALIVE = 5 * ROUND_DURATION
	FLAG_FORMAT = r'[A-Z0-9]{31}=' # /^[A-Z0-9]{31}=$/

	FLAGID_URL = 'http://10.10.0.1:8081/flagIds' # flag_ids endpoint, leave blank if none

	SUB_PROTOCOL = 'ccit' # submitter protocol. Valid values are 'dummy', 'ccit', 'faust'
	SUB_LIMIT = 1 # number of requests per interval
	SUB_INTERVAL = 5 # interval duration
	SUB_PAYLOAD_SIZE = 100 # max flag per request
	SUB_URL = 'http://10.10.0.1:8080/flags'

	# Don't worry about this
	DB_NSUB = 'NOT_SUBMITTED'
	DB_SUB = 'SUBMITTED'
	DB_SUCC = 'SUCCESS'
	DB_ERR = 'ERROR'
	DB_EXP = 'EXPIRED'


	DATABASE = 'instance/flagWarehouse.sqlite'
	#################
