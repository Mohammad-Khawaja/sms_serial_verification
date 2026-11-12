import os
import sqlite3
import re

from flask import Flask, jsonify, request, Response, redirect, url_for, session, abort
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user
import requests
from pandas import read_excel

import config
from sms_simulator.simulator_manager import run_sms_simulator

app = Flask(__name__)

app.config.update(
	SECRET_KEY = config.SECRET_KEY
)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin):
	def __init__(self, id):
		self.id = id

	def __repr__(self):
		return f"User({self.id})"
	
	def __str__(self):
		return f"{self.id}"
		
user = User(0)

@app.route("/")
@login_required
def home():
	return Response("hello home")

@app.route("/v1/ok")
def health_check():
	ret = {"message": "ok"}
	return jsonify(ret)

@app.route("/login", methods=["GET", "POST"])
def login():
	if request.method == "POST":
		username = request.form.get("username", "")
		password = request.form.get("password", "")
		if username == config.USERNAME and password == config.PASSWORD:
			login_user(user)
			return redirect(request.args.get("next"))
	return """
	<form method="post">
		<input name="username"><br>
		<input type="password" name="password"><br>
		<input type="submit">
	</form>
	"""
	
@app.route("/logout")
@login_required
def logout():
	logout_user()
	return Response("<h1>Logged out</h1>")

@app.errorhandler(401)
def page_not_found(error):
	return Response("<h1>Login failed</h1>")
	
@login_manager.user_loader
def load_user(userid):
	return User(userid)



def send_sms(message, receptor):
	url = f"https://tapi.bale.ai/bot{config.TOKEN}/sendMessage"
	data = {"text": str(message), "chat_id": receptor}
	r = requests.post(url, json=data)
	print("status code:", r.status_code)	
	
@app.route("/v1/process", methods=["POST"])
def process():
	message = normalize_string(request.form.get("message"))
	sender = request.form.get("from")
	print(f"message received. message is {message} and sender is {sender} ")
	
	answer = check_serial(message)
	
	send_sms(answer, sender)
	
	ret = {"message": "Processing completed."}
	return jsonify(ret), 200

def normalize_string(string: str):
	string = string.upper()
	table = str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789')
	string = string.translate(table)
	string = re.sub(r'[^a-zA-Z0-9]', '', string)
	return string

def import_database_from_exel(filepath):
	
	conn = sqlite3.connect(config.DATABASE_FILE_PATH)
	cur = conn.cursor()
	
	cur.execute("DROP TABLE IF EXISTS serials")
	cur.execute("CREATE TABLE serials(id INTEGER PRIMARY KEY, ref TEXT, desc TEXT, start_serial TEXT, end_serial TEXT, date DATE)")
	conn.commit()
	
	df0 = read_excel(filepath, 0) # contions lookup data
	
	for index, (line, ref, desc, start_serial, end_serial, date) in df0.iterrows():
		start_serial = normalize_string(start_serial)
		end_serial = normalize_string(end_serial)
		cur.execute("INSERT INTO serials VALUES (?, ?, ?, ?, ?, ?)", (line, ref, desc, start_serial, end_serial, str(date)))
	conn.commit()
	
	
	cur.execute("DROP TABLE IF EXISTS invalids")
	cur.execute("CREATE TABLE invalids(invalid_serial TEXT PRIMARY KEY)")
	conn.commit()
	
	df1 = read_excel(filepath, 1)
	
	for index, (faild_serial,) in df1.iterrows():
		faild_serial = normalize_string(faild_serial)
		cur.execute("INSERT INTO invalids VALUES(?)", (faild_serial,))
	conn.commit()
	
	conn.close()
	
	return len(df0), len(df1)
	
def check_serial(serial):
	with sqlite3.connect(config.DATABASE_FILE_PATH) as conn:
		cur = conn.cursor()
		result = cur.execute("SELECT 1 FROM invalids WHERE invalid_serial = ?", (serial,))
		if len(result.fetchall()) == 1:
			return "Invalid serial number"
		
		prefix = serial[:2]
		number = int(serial[2:])

		rows = cur.execute("SELECT start_serial, end_serial FROM serials WHERE substr(start_serial, 1, 2) = ?", (prefix,)).fetchall()
	
		for start, end in rows:
			start_number = int(start[2:])
			end_number = int(end[2:])
	
		if start_number <= number <= end_number:
			return "Serial number found"

		
		return "Serial number not found"
		
if __name__ == "__main__":
	if os.environ.get("WERKZEUG_RUN_MAIN") is None:	
		run_sms_simulator()
	import_database_from_exel("data.xlsx")
	app.run(debug=True, use_reloader=True, host="0.0.0.0")