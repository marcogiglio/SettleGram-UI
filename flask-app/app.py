from pymongo import MongoClient
import os
from flask import Flask, render_template, redirect, url_for
from flask_login import UserMixin, LoginManager, login_required, current_user, login_user, logout_user
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hmac, hashes

client = MongoClient('mongodb', 27017)
db = client.settlegram
groups = db.groups
users = db.frontend_users
app = Flask(__name__)

flask_env = os.getenv('FLASK_ENVIRONMENT')
if flask_env == 'development':
    app.config.update(
        SECRET_KEY=b'XYZ',
        SERVER_NAME='localhost',
        PREFERRED_URL_SCHEME='http'
    )
else:
    app.config.update(
        SECRET_KEY=b'XyZ',
        SERVER_NAME='settlegram.app',
        PREFERRED_URL_SCHEME='https'
    )

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "sign_in"


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/sign_in', methods=['GET', 'POST'])
def sign_in():
    kv_login_info = list(request.args.items())
    telegram_login = request.args
    # Get string to verify
    kv_login_info.sort()
    del kv_login_info[2]
    print(kv_login_info, flush=True)
    concat_kv = map(lambda kv: '='.join(kv), kv_login_info)
    str_login_info = '\n'.join(concat_kv)
    print(bytearray(str_login_info, 'utf-8'), flush=True)

    # Verify HMAC Signature
    bot_token = os.getenv('TOKEN_KEY')
    key = hashes.Hash(hashes.SHA256(), backend=default_backend())
    key.update(bot_token)
    key = key.finalize()
    h = hmac.HMAC(key, hashes.SHA256(), backend=default_backend())
    h.update(bytearray(str_login_info, 'utf-8'))
    print(telegram_login['hash'], flush=True)
    h.verify(bytes.fromhex(telegram_login['hash']))

    user = User(telegram_id=telegram_login['id'],
                first_name=telegram_login['first_name'],
                username=telegram_login['username'])

    does_user_exist = users.find_one({'username': telegram_login['username']})
    if not does_user_exist:
        users.insert_one(user.__dict__)
    login_user(user)
    return redirect(url_for('groups', _external=True))


@app.route('/groups')
@login_required
def index():
    return render_template('groups.html')


@app.route('/groups/<group_id>')
@login_required
def group_details():
    return render_template('details.html')


@login_manager.user_loader
def load_user(user_id):
    telegram_login = users.find_one({'telegram_id': user_id})
    user = User(telegram_id = telegram_login['telegram_id'],
         first_name = telegram_login['first_name'],
         username = telegram_login['username'])
    return user


if __name__ == "__main__":
    app.run()

# Login with Telegram Username
# View Table with Groups where @username is member 
# Get Group View with Expenses List
# Get payments info if group is closed


