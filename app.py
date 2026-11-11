import os

from flask import Flask, jsonify, request
import requests

from config import TOKEN
from sms_simulator.simulator_manager import run_sms_simulator

app = Flask(__name__)

@app.route("/")
def main_page():
	return "hello"

def send_sms(message, receptor):
	url = f"https://tapi.bale.ai/bot{TOKEN}/sendMessage"
	data = {"text": "hi "+message, "chat_id": receptor}
	r = requests.post(url, json=data)
	print("status code:", r.status_code)	
	
@app.route("/v1/process", methods=["POST"])
def process():
	message = request.form.get("message")
	sender = request.form.get("from")
	print(f"message received. message is {message} and sender is {sender} ")
	
	send_sms(message, sender)
	
	ret = {"message": "Processing completed."}
	return jsonify(ret), 200

def check_serial():
	pass
	
if __name__ == "__main__":
	if os.environ.get("WERKZEUG_RUN_MAIN") is None:	
		run_sms_simulator()
	app.run(debug=True, use_reloader=True, host="0.0.0.0")
