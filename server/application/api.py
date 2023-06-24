from flask import current_app, Blueprint, request, jsonify
import sqlite3
import time

from . import db
from .auth import api_auth_required

bp = Blueprint('api', __name__)


@bp.route('/api/get_config', methods=['GET'])
@api_auth_required
def get_config():
    config_dict = {
        'format': current_app.config['FLAG_FORMAT'],
        'round': current_app.config['ROUND_DURATION'],
        'teams': current_app.config['TEAMS'],
        'nop_team': current_app.config['NOP_TEAM'],
        'flagid_url': current_app.config['FLAGID_URL'],
    }
    return jsonify(config_dict)


@bp.route('/api/upload_flags', methods=['POST'])
@api_auth_required
def upload_flags():
    data = request.get_json()
    username = data.get('username')
    # current_app.logger.debug(f"{len(data.get('flags'))} flags received from user {username}")
    rows = []
    for item in data.get('flags'):
        rows.append((item.get('flag'), username, item.get('exploit_name'), item.get('team_ip'), item.get('time'),
                     current_app.config['DB_NSUB']))

    # Try multiple times before failing
    for i in range(5):
        try:
            database = db.get_db()
            database.executemany('INSERT OR IGNORE INTO flags (flag, username, exploit_name, team_ip, time, status) '
                                'VALUES (?, ?, ?, ?, ?, ?)', rows)
            database.commit()
            break
        except sqlite3.OperationalError:
            if i == 4:
                raise
            time.sleep(0.2)

    return 'Data received', 200
