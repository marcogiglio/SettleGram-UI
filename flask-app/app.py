from pymongo import MongoClient
import os
from flask import flash, Flask, render_template, redirect, url_for, request
from flask_login import UserMixin, LoginManager, login_required, current_user, login_user, logout_user
from flask_bootstrap import Bootstrap
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hmac, hashes
from utils import get_balance, generate_list_payments

client = MongoClient('mongodb', 27017)
db = client.settlegram
groups = db.groups
users = db.frontend_users
app = Flask(__name__)
Bootstrap(app)


class User(UserMixin):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def get_id(self):
        return str(self.telegram_id)


flask_env = os.getenv('FLASK_ENV')
secret_key = os.getenv('SECRET_KEY')
if flask_env == 'development':
    app.config.update(
        SECRET_KEY=b'XYZ',
        SERVER_NAME='test.settlegram.app',
        PREFERRED_URL_SCHEME='https'
    )
else:
    app.config.update(
        SECRET_KEY=secret_key,
        SERVER_NAME='settlegram.app',
        PREFERRED_URL_SCHEME='https'
    )

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "sign_in"


@app.route('/')
def index():
    if os.getenv('FLASK_ENV') == 'development':
        data_auth_url = 'https://test.settlegram.app/sign_in'
    else:
        data_auth_url = 'https://settlegram.app/sign_in'

    return render_template('login.html', data_auth_url=data_auth_url)


@app.route('/sign_in', methods=['GET', 'POST'])
def sign_in():
    kv_login_info = list(request.args.items())
    telegram_login = request.args
    # Get string to verify
    kv_login_info.sort()
    del kv_login_info[2]
    concat_kv = map(lambda kv: '='.join(kv), kv_login_info)
    str_login_info = '\n'.join(concat_kv)

    # Verify HMAC Signature over parameters
    bot_token = bytearray(os.getenv('TOKEN_KEY'), 'utf-8')
    key = hashes.Hash(hashes.SHA256(), backend=default_backend())
    key.update(bot_token)
    key = key.finalize()

    h = hmac.HMAC(key, hashes.SHA256(), backend=default_backend())
    h.update(bytearray(str_login_info, 'utf-8'))
    h.verify(bytes.fromhex(telegram_login['hash']))
    user = User(telegram_id=telegram_login['id'],
                first_name=telegram_login['first_name'],
                username=telegram_login['username'])

    does_user_exist = users.find_one({'username': telegram_login['username']})
    if not does_user_exist:
        users.insert_one(user.__dict__)
    login_user(user)
    return redirect(url_for('set_groups', username=telegram_login['username'], _external=True))


@app.route('/set_groups/<username>')
@login_required
def set_groups(username):
    # Render only authorize
    if current_user.username != username:
        return render_template('login.html')

    group_list = list(groups.find({'members.username': username}))
    return render_template('groups.html', group_list=group_list)


@app.route('/group/<group_name>')
@login_required
def group_details(group_name):
    
    group = groups.find_one({'name': group_name})
    is_member = next(
            filter(lambda x: x['username'] == current_user.username, 
                group['members']), None)
    if not is_member:
        flash(u'Unauthorized','danger')
        return render_template('login.html')
    total_expenses = sum(map(lambda x: x['amount'], group['expenses']))
    group_balance = get_balance(group['expenses']).items()
    return render_template('details.html', group=group, total_expenses=total_expenses, balances=group_balance)


@app.route('/member/<username>')
@login_required
def member(username):
    group_list = list(groups.find({'members.username': username}))
    # Show only groups where current_user and the inspected user are both members
    filtered_group_list = []
    for group in group_list:
        for member in group['members']:
            if member['username'] == current_user.username:
                filtered_group_list.append(group)
     
    print(filtered_group_list, flush=True)
    total_paid = 0
    for group in filtered_group_list:
        paid_expenses = list(filter(lambda x: x['who_paid']['username'] == username, group['expenses']))
        print(paid_expenses, flush=True)
        total_paid += sum(map(lambda x: x['amount'], paid_expenses))

    return render_template(
            'member_details.html', 
            username=username,
            group_list=filtered_group_list,
            total_paid=total_paid)

@login_manager.user_loader
def load_user(user_id):
    telegram_login = users.find_one({'telegram_id': user_id})
    user = User(telegram_id=telegram_login['telegram_id'],
                first_name=telegram_login['first_name'],
                username=telegram_login['username'])
    return user


if __name__ == "__main__":
    app.run()

# Login with Telegram Username
# View Table with Groups where @username is member 
# Get Group View with Expenses List
# Get payments info if group is closed
