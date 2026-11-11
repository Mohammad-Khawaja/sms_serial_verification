import os
import sqlite3

from flask import Flask, jsonify, request
import requests
from pandas import read_excel

import config
from sms_simulator.simulator_manager import run_sms_simulator

app = Flask(__name__)

@app.route("/")
def main_page():
	return "hello"

def send_sms(message, receptor):
	url = f"https://tapi.bale.ai/bot{config.TOKEN}/sendMessage"
	data = {"text": "hi "+message, "chat_id": receptor}
	r = requests.post(url, json=data)
	print("status code:", r.status_code)	
	
@app.route("/v1/process", methods=["POST"])
def process():
	message = normalize_string(request.form.get("message"))
	sender = request.form.get("from")
	print(f"message received. message is {message} and sender is {sender} ")
	
	send_sms(message, sender)
	
	ret = {"message": "Processing completed."}
	return jsonify(ret), 200

def normalize_string(string: str):
	from_char = "۰۱۲۳۴۵۶۷۸۹"
	to_char = "0123456789"
	for i in range(len(from_char)):
		string.replace(from_char[i], to_char[i])
	
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
	
def check_serial():
	pass
	
if __name__ == "__main__":
	if os.environ.get("WERKZEUG_RUN_MAIN") is None:	
		run_sms_simulator()
	app.run(debug=True, use_reloader=True, host="0.0.0.0")