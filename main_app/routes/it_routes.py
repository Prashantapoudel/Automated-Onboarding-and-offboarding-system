from flask import Blueprint, render_template

it_bp = Blueprint('it_routes', __name__)


@it_bp.route('/it')
def it_dashboard():
    return render_template('main/it_dashboard.html')
