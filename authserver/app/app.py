from flask import Flask, request, jsonify
from firebase_admin import credentials, firestore, initialize_app
import os
import sys,traceback
import requests
import random
import string

app = Flask(__name__)

# Initialize firestore
cred = credentials.Certificate('key.json')
default_app = initialize_app(cred)
db = firestore.client()
todo_ref = db.collection('todos')
users = db.collection('users')

@app.route('/')
def hello_world():
    return "Hello world!"

@app.route('/genstate', methods=['GET'])
def generate_state():
    state = "".join(random.choices(string.ascii_letters + string.digits, k = 16))
    users.document(state).set({"configured": False})
    print(f"Created new state {state}")
    return state, 200

@app.route('/discord', methods=['GET'])
def handle_discord():
    code = request.args.get('code')
    state = request.args.get('state')
    try:
        if state:
            todo_ref.document(state).set({"state": state, "code": code})
            return jsonify({"success": True}), 200
        else :
            raise Exception("no state!")
    except Exception as e:
        stacktrace = traceback.format_exc()
        return f"State: {state}, Code: {code}. An error occurred: {e}\n{stacktrace}"

@app.route('/discord_view', methods=['GET'])
def view_discord_all():
    try:
        userid = request.args.get('id')
        if userid:
            return jsonify(users.document(userid).get().to_dict()), 200
        else :
            all_entries = [doc.to_dict() for doc in users.stream()]
            return jsonify(all_entries), 200
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
def delete_todos():
    try:
        todo_id = request.args.get('id')
        todo_ref.document(todo_id).delete()
        return jsonify({"success", True}), 200
    except Exception as e:
        return f"An error occurred: {e}"

port = int(os.environ.get("PORT", 8080))
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=port)
