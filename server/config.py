class Config(object):
    # WEB APPLICATION PASSWORD
    WEB_PASSWORD = 'password'

    # CLIENT API TOKEN
    API_TOKEN = 'token'

    YOUR_TEAM = '10.60.14.1'
    TEAM_TOKEN = '' # team token for flag submission
    TEAMS = ['10.60.{}.1'.format(i) for i in range(1, 35)]
    TEAMS.remove(YOUR_TEAM)

    ROUND_DURATION = 120
    FLAG_ALIVE = 5 * ROUND_DURATION
    FLAG_FORMAT = r'[A-Z0-9]{31}='

    
    FLAGID_URL = '' # flag_ids endpoint, leave blank if none

    SUB_LIMIT = 1 # number of requests per interval
    SUB_INTERVAL = 5 # interval duration
    SUB_PAYLOAD_SIZE = 100 # max flag per request
    SUB_URL = 'http://10.1.0.2/flags' # flag submission endpoint

    SUB_ACCEPTED = 'accepted'
    SUB_INVALID = 'invalid'
    SUB_OLD = 'too old'
    SUB_YOUR_OWN = 'your own'
    SUB_STOLEN = 'already stolen'
    SUB_NOP = 'from NOP team'
    SUB_NOT_AVAILABLE = 'is not available'

    # Don't worry about this
    DB_NSUB = 'NOT_SUBMITTED'
    DB_SUB = 'SUBMITTED'
    DB_SUCC = 'SUCCESS'
    DB_ERR = 'ERROR'
    DB_EXP = 'EXPIRED'

    SECRET_KEY = 'changeme'

    DATABASE = 'instance/flagWarehouse.sqlite'
    #################
