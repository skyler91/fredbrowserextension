from flask import Flask, request, jsonify
from firebase_admin import credentials, firestore, initialize_app
from datetime import datetime
import os
import sys,traceback
import requests
import random
import string
import json
import urllib.parse

app = Flask(__name__)

# Initialize firestore
cred = credentials.Certificate('key.json')
default_app = initialize_app(cred)
db = firestore.client()
todo_ref = db.collection('todos')
users = db.collection('users')
CLIENT_ID = ""
CLIENT_SECRET = ""
WEBHOOK_ID = ""
WEBHOOK_TOKEN = ""
BASE_URI = ""
DISCORD_API_URI = ""
DISCORD_API_WEBHOOK = ""
AVATAR_URL = ""
LOGFILE = "flaskapp.log"

def log_message(msg, sender=None):
    outMsg = str(datetime.now()) + " "
    if sender :
        outMsg = outMsg + sender + " "
    outMsg = outMsg + msg
    app.logger.info(outMsg)
    with open(LOGFILE, 'a') as f:
        f.write(outMsg + "\n")
        f.close()

@app.route('/')
def hello_world():
    return "Hello world!"

@app.route('/success')
def success_auth():
    return "Successfully authenticated!"

@app.route('/genstate', methods=['GET'])
def generate_state():
    # TODO: VALIDATE UID!!
    uid = request.args.get('uid')
    if (uid != None) :
        state = "".join(random.choices(string.ascii_letters + string.digits, k = 16))
        # TODO: Dont overrite existing values, just set state
        users.document(uid).set({"state": state})
        log_message(f"Created new state {state} for uid {uid}", request.environ['REMOTE_ADDR'])
        return state, 200
    else :
        return "UID value must be set!", 401

@app.route('/discord', methods=['GET'])
def handle_discord():
    code = request.args.get('code')
    state = request.args.get('state')
    try:
        if state:
            matches = users.where("state", "==", state).stream()
            uid = None
            for m in matches :
                log_message("{} => {}".format(m.id, m.to_dict()), request.environ['REMOTE_ADDR'])
                uid = m.id
                users.document(uid).set({"code": code}, merge=True)
                break
            getAndStoreUserIdentity(uid)
            return "Authentication successful!", 200
            #return jsonify(users.document(uid).get().to_dict()), 200
        else :
            raise Exception("no state!")
    except Exception as e:
        stacktrace = traceback.format_exc()
        return f"State: {state}, Code: {code}. An error occurred: {e}\n{stacktrace}", 401

def getAndStoreUserIdentity(uid) :
    # TODO: exception handling here
    userInfo = users.document(uid).get().to_dict()
    if userInfo :
        token = getDiscordAccessToken(uid, userInfo['code'])
        users.document(uid).set({"token": token['access_token'], "token_type": token['token_type'],
                                 "refresh_token": token['refresh_token']}, merge=True)
        log_message(f"token: {token}")
        getAndStoreUserInfo(uid, token['access_token'])

def getAndStoreUserInfo(uid, token):
    headers = {"Authorization" : f"Bearer {token}"}
    r = requests.get(DISCORD_API_URI + "/users/@me", headers=headers)
    r.raise_for_status()
    info = r.json()
    log_message(f"Got user info: {r.text}")
    users.document(uid).set({"discord_id" : info['id'],
                             "username" : info['username'],
                             "avatar" : info['avatar'],
                             "discriminator" : info['discriminator']}, merge=True)

def getDiscordAccessToken(uid, code) :
    data = {'client_id' : CLIENT_ID,
            'client_secret' : CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'scope': 'identify',
            'redirect_uri': BASE_URI + "/discord"}
    headers = { "content-type": "application/x-www-form-urlencoded"}
    r = requests.post(DISCORD_API_URI + "/oauth2/token", data=data, headers=headers)
    log_message(f"Sending {data} to {DISCORD_API_URI}/oauth2/token")
    log_message(f"Result: {r.text}")
    r.raise_for_status()
    log_message(r.text)
    return r.json()

@app.route("/play", methods=["POST"])
def play_music():
    #TODO: Validation!!
    try :
        uid = request.json['uid']
        songUrl = request.json['songurl']
        userObj = users.document(uid).get().to_dict()
        data = {"username": userObj['username'],
                "avatar_url": AVATAR_URL,
                "content": f"!play {songUrl} [{userObj['discord_id']}]"}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        log_message(f"Playing song {songUrl} requested by {userObj['username']}")
        r = requests.post(f"{DISCORD_API_WEBHOOK}/{WEBHOOK_ID}/{WEBHOOK_TOKEN}", headers=headers, data=data)
        return r.text, r.status_code
    except Exception as e:
        log_message(f"Exception in play_music: {e}")
        return f"An error occurred: {e}"

@app.route('/check_auth', methods=['GET'])
def check_user_auth():
    try:
        userid = request.args.get('uid')
        log_message(f"userid = {userid}")
        if userid:
            userObj = users.document(userid).get().to_dict()
            if userObj and userObj.get('token') :
                return jsonify({"auth": "success"}), 200
        return jsonify({"auth" : "failed"}), 200
    except Exception as e:
        return f"Failed to check authentication for {userid}: {e}"


@app.route('/discord_view', methods=['GET'])
def view_discord_all():
    try:
        userid = request.args.get('uid')
        if userid:
            return jsonify(users.document(userid).get().to_dict()), 200
        else :
            #all_entries = [doc.to_dict() for doc in users.stream()]
            docs = users.stream()
            #return jsonify(all_entries), 200
            ret = ''
            for doc in docs :
                ret = ret + u'{} => {}'.format(doc.id, doc.to_dict()) + "<br />"
            return ret, 200
    except Exception as e:
        return f"An error occurred: {e}"

@app.route('/add', methods=['POST'])
def create_todo():
    try:
        id = request.json['id']
        todo_ref.document(id).set(request.json)
        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An error Occurred: {e}"

@app.route("/list", methods=['GET'])
def read_todos():
    try:
        todo_id = request.args.get('id')
        if todo_id:
            todo = todo_ref.document(todo_id).get()
            return jsonify(todo.to_dict()), 200
        else :
            all_todos = [doc.to_dict() for doc in todo_ref.stream()]
            return jsonify(all_todos), 200
    except Exception as e:
        return f"An error occurred: {e}"

@app.route("/update", methods=["POST", "PUT"])
def update_todos():
    try:
        id = request.json['id']
        todo_ref.document(id).update(request.json)
        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An error occurred: {e}"

@app.route("/delete", methods=["GET", "DELETE"])
def delete_users():
    try:
        userid = request.args.get('uid')
        log_message(f"deleting userid {userid}")
        users.document(userid).delete()
        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An error occurred: {e}"


port = int(os.environ.get("PORT", 8080))
if __name__ == '__main__':
    with open('config.json', 'r') as config_file:
        data = json.load(config_file)
        CLIENT_ID = data['discord_plugin_client_id']
        CLIENT_SECRET = data['discord_plugin_client_secret']
        BASE_URI = data['base_uri']
        DISCORD_API_URI = data['discord_api_endpoint']
        DISCORD_API_WEBHOOK = data['discord_api_webhooks']
        WEBHOOK_ID = data['discord_server_webhook_id']
        WEBHOOK_TOKEN = data['discord_server_webhook_token']
        AVATAR_URL = data['avatar_url']
    app.run(debug=True, host='0.0.0.0', port=port)
