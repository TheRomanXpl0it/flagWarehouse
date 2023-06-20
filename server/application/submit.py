from flask import Blueprint, render_template
from .auth import login_required
from .home import gzipped

bp = Blueprint('submit', __name__)

@bp.route('/submit', methods=['GET'])
@login_required
@gzipped
def submitManually():
    return render_template('submit.html')