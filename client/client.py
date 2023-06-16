#!/usr/bin/env python3
import argparse
import logging
import math
import os
import os.path
import re
import signal
import subprocess
import sys
import time
import random
from datetime import datetime
from multiprocessing import Pool
from threading import Timer

import requests
import json


END				= "\033[0m"

GREY			= "\033[30m"
RED				= "\033[31m"
GREEN			= "\033[32m"
YELLOW			= "\033[33m"
BLUE			= "\033[34m"
PURPLE			= "\033[35m"
CYAN			= "\033[36m"

HIGH_RED		= "\033[91m"



BANNER = '''
  ___ __               ________                    __
.'  _|  |.---.-.-----.|  |  |  |.---.-.----.-----.|  |--.-----.--.--.-----.-----.
|   _|  ||  _  |  _  ||  |  |  ||  _  |   _|  -__||     |  _  |  |  |__ --|  -__|
|__| |__||___._|___  ||________||___._|__| |_____||__|__|_____|_____|_____|_____|
               |_____|

          The perfect solution for running all your exploits in one go!

'''[1:]


def parse_args():
    # noinspection PyTypeChecker
    parser = argparse.ArgumentParser(description='''Run all the exploits in the specified
                                            directory against all the teams.''',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-s', '--server-url',
                        type=str,
                        metavar='URL',
                        default='http://localhost:5555',
                        help='The URL of your flagWarehouse server. Please specify the protocol')

    parser.add_argument('-u', '--user',
                        type=str,
                        metavar='USER',
                        required=True,
                        help='Your username')

    parser.add_argument('-t', '--token',
                        type=str,
                        metavar='TOKEN',
                        required=True,
                        help='The authorization token used for the flagWarehouse server API')

    parser.add_argument('-d', '--exploit-directory',
                        type=str,
                        metavar='DIR',
                        required=True,
                        help='The directory that holds all your exploits')

    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help='Verbose output')

    parser.add_argument('-n', '--num-threads',
                        type=int,
                        metavar='THREADS',
                        required=False,
                        default=64,
                        help='Maximum number of threads to spawn')

    return parser.parse_args()


def run_exploit(exploit: str, ip: str, round_duration: int, server_url: str, token: str, pattern, user: str):
    def timer_out(process):
        timer.cancel()
        process.kill()

    p = subprocess.Popen(
        [exploit, ip], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    timer = Timer(math.ceil(0.5 * round_duration), timer_out, args=[p])

    timer.start()
    while True:
        output = p.stdout.readline().decode().strip()
        if output == '' and p.poll() is not None:
            break
        if output:
            logging.debug(f'{os.path.basename(exploit)}@{ip} => {output}')
            flags = set(pattern.findall(output))
            if flags:
                exp = exploit.split('/')[-1][:-3]
                logging.info(f'Got {GREEN}{len(flags)}{END} flags with {BLUE}{exp}{END} from {ip}')
                msg = {'username': user, 'flags': []}
                t_stamp = datetime.now().replace(microsecond=0).isoformat(sep=' ')
                for flag in flags:
                    msg['flags'].append({'flag': flag,
                                         'exploit_name': os.path.basename(exploit),
                                         'team_ip': ip,
                                         'time': t_stamp})
                requests.post(server_url + '/api/upload_flags',
                              headers={'X-Auth-Token': token},
                              json=msg)
    p.stdout.close()
    return_code = p.poll()
    timer.cancel()
    if return_code == -9:
        logging.error(
            f'{RED}{os.path.basename(exploit)}{END}@{ip} was killed because it took too long to finish')
    elif return_code != 0:
        logging.error(
            f'{RED}{os.path.basename(exploit)}{END}@{ip} terminated with error code {HIGH_RED}{return_code}{END}')


def main(args):
    global pool
    print(BANNER)

    # Parse parameters
    server_url = args.server_url
    user = args.user
    token = args.token
    verbose = args.verbose
    exploit_directory = args.exploit_directory
    num_threads = args.num_threads

    logging.basicConfig(format='%(asctime)s %(levelname)s - %(message)s',
                        datefmt='%H:%M:%S', level=logging.DEBUG if verbose else logging.INFO)

    # Retrieve configuration from server
    logging.info('Connecting to the flagWarehouse server...')
    r = None
    try:
        r = requests.get(server_url + '/api/get_config',
                         headers={'X-Auth-Token': token})
        if r.status_code == 403:
            logging.error('Wrong authorization token.')
            logging.info('Exiting...')
            sys.exit(0)

        if r.status_code != 200:
            logging.error(f'GET {server_url}/api/get_config responded with [{r.status_code}].')
            logging.info('Exiting...')
            sys.exit(0)

    except requests.exceptions.RequestException as e:
        logging.error(f'Could not connect to {server_url}: ' +
                      e.__class__.__name__)
        logging.info('Exiting...')
        sys.exit(0)

    # Parse server config
    config = r.json()
    # Print server config
    if verbose:
        logging.debug(json.dumps(config, indent=4, sort_keys=True))
    flag_format = re.compile(config['format'])
    round_duration = config['round']
    teams = config['teams']
    flagid_url = config.get('flagid_url', '')
    logging.info('Client correctly configured.')

    # MAIN LOOP
    while True:
        try:
            requests.head(server_url)
            s_time = time.time()

            # Retrieve flag_ids
            if flagid_url:
                try:
                    r = requests.get(flagid_url, timeout=15)

                    if r.status_code != 200:
                        logging.error(
                            f'{flagid_url} responded with {r.status_code}: Retrying in 5 seconds.')
                        time.sleep(5)
                        continue

                    dir_path = os.path.dirname(os.path.realpath(__file__))
                    with open(f'{dir_path}/flag_ids.json', 'w', encoding='utf-8') as f:
                        f.write(r.text)
                except TimeoutError:
                    logging.error(
                        f'{flagid_url} timed out: Retrying in 5 seconds.')
                    time.sleep(5)
                    continue

            # Load exploits
            try:
                scripts = [os.path.join(exploit_directory, s) for s in os.listdir(exploit_directory) if
                           os.path.isfile(os.path.join(exploit_directory, s)) and not s.startswith('.')]

                # Filter non executable
                for s in scripts:
                    if not os.access(s, os.X_OK):
                        logging.warning(f'{os.path.basename(s)} is not executable, hence it will be skipped...')

                # Remove non executable scripts
                scripts = list(filter(lambda script: os.access(script, os.X_OK), scripts))

                # Check for shebang
                no_shbang = []
                for s in scripts:
                    with open(s, 'r', encoding='utf-8') as f:
                        if not f.read(2) == '#!':
                            logging.warning(f'{os.path.basename(s)} no shebang #!, hence it will be skipped...')
                            no_shbang.append(s)

                # Remove scripts without shebang
                scripts = list(filter(lambda script: script not in no_shbang, scripts))

            except FileNotFoundError:
                logging.error('The directory specified does not exist.')
                logging.info('Exiting...')
                sys.exit(0)
            except PermissionError:
                logging.error(
                    'You do not have the necessary permissions to use this directory.')
                logging.info('Exiting')
                sys.exit(0)
            if scripts:
                logging.info(
                    f'Starting new round. Running {len(scripts)} exploits.')
                logging.debug(f"Exploits: [{', '.join(map(lambda script: os.path.basename(script), scripts))}]")
            else:
                logging.info('No exploits found: retrying in 15 seconds')
                time.sleep(15)
                continue

            original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
            pool = Pool(min(num_threads, len(scripts) * len(teams)))
            signal.signal(signal.SIGINT, original_sigint_handler)

            # Run exploits
            random.shuffle(scripts)
            random.shuffle(teams)
            for script in scripts:
                for team in teams:
                    pool.apply_async(
                        run_exploit, (script, team, round_duration, server_url, token, flag_format, user))
            pool.close()
            pool.join()

            duration = time.time() - s_time
            logging.debug(f'round took {round(duration, 1)} seconds')

            if duration < round_duration:
                logging.debug(f'Sleeping for {round(round_duration - duration, 1)} seconds')
                time.sleep(round_duration - duration)

        # Exceptions
        except KeyboardInterrupt:
            logging.info('Caught KeyboardInterrupt. Bye!')
            pool.terminate()
            break
        except requests.exceptions.RequestException:
            logging.error(
                'Could not communicate with the server: retrying in 5 seconds.')
            time.sleep(5)
            continue


if __name__ == '__main__':
    main(parse_args())
