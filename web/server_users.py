import os, hashlib, base64
from pymongo import MongoClient
from bson import ObjectId

from flask import Blueprint, request, render_template, redirect
from flask.ext.login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
)

users = Blueprint('users',
                  __name__,
                  template_folder='templates/login')

login_manager = LoginManager()

client = MongoClient()
db_users = client.news.users

class User(dict):
    def is_active(self):
        return self['is_active']

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return True

    def get_id(self):
        return unicode(self['_id'])

@users.record_once
def on_load(state):
    login_manager.init_app(state.app)

@login_manager.user_loader
def load_user(user_id):
    doc = db_users.find_one({'_id': ObjectId(user_id)})

    if doc is None:
        return None
    else:
        return User(doc)

def hash_pass(password, salt):
    m = hashlib.sha512()
    m.update(salt)
    m.update(password)
    #m.update(SECRET_KEY)
    return base64.b64encode(m.digest())

@users.route("/register", methods=["GET", "POST"])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    else:
        user_name = request.form.get('user_name').strip()
        password = request.form.get('password')
        email = request.form.get('email').lower()

        error_context = {'user_name': user_name,
                         'email': email,}

        if '@' not in email:
            return render_template("register.html",
                                   error="Please specify an email address.",
                                   **error_context)

        if len(user_name) < 1:
            return render_template("register.html",
                                   error="You must specify a username.",
                                   **error_context)
        
        if len(password) < 1:
            return render_template("register.html",
                                   error="You must specify a password.",
                                   **error_context)

        doc = db_users.find_one({'email': email})

        if doc is not None:
            return render_template("register.html",
                                   error="The email address {} is already registered.".format(email),
                                   **error_context)
        
        doc = db_users.find_one({'user_name': user_name})

        if doc is not None:
            return render_template("register.html",
                                   error="The user name {} is already registered.".format(user_name),
                                   **error_context)

        salt = os.urandom(8)
        password_hashed = hash_pass(password, salt)

        doc = {
            'user_name': user_name,
            'email': email,
            'salt': base64.b64encode(salt),
            'hashpass': password_hashed,
            'is_active': False,
        }

        user_id = db_users.save(doc)

        return render_template("register_thankyou.html")

@users.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'GET':
        return render_template("login.html")
    else:
        email = request.form.get('email')
        password = request.form.get('password')

        user_doc = db_users.find_one({'email': email})
       
        if user_doc is None:
            return render_template('login.html', error="Could not find user with email address {}.".format(email))

        user = User(user_doc)
    
        salt = base64.b64decode(user['salt'])
        password_hashed = hash_pass(password, salt)
        
        if password_hashed == user['hashpass']: 
            login_result = login_user(user)

            if login_result:
                return redirect(request.args.get("next") or "/")
            else:
                return render_template('login.html', error="User not active.")

        else:
            return render_template('login.html', error="Login failed.")

@users.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")

if __name__ == "__main__":
    from flask import Flask

    @users.route("/")
    def index():
        return render_template('login_index.html')

    app = Flask(__name__)

    app.secret_key='DEBUGGING'
    app.register_blueprint(users)

    app.run("0.0.0.0", debug=True)

