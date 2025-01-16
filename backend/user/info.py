from flask import Blueprint, g, jsonify

from backend.auth.decorators import login_required, admin_required
from backend.models import User

user_bp = Blueprint('user', __name__)


# fetch information about me
@user_bp.route('/user', methods=['GET'])
@login_required
def user():
    user = g.user
    data = userData(user)
    return jsonify(data), 200


# fetch info about a selected user
@user_bp.route('/user/<int:user_id>', methods=['GET'])
@admin_required
def user_by_id(user_id):
    user = User.query.get_or_404(user_id)
    user_data = userData(user)
    return jsonify(user_data), 200


def userData(user):
    return {
        'id': user.id,
        'username': user.username,
        'used_space': user.used_space,
        'quota': user.quota,
        'admin': user.is_admin
    }
