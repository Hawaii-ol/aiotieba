import ml
import binascii
import logging
from flask import Flask
from flask import request

app = Flask(__name__)
antispammer = ml.AntiSpammer()
antispammer.train()
antifraud = ml.AntiFraud()
antifraud.train()

@app.route('/predict/spam', methods=['POST'])
def api_predict_ads():
    text = request.form.get('text')
    result = antispammer.predict(text)
    if result == 'spam':
        print("Possible spam: " + text)
    return result

@app.route('/predict/fraud', methods=['POST'])
def api_predict_fraud():
    text = request.form.get('text')
    result = antifraud.predict(text)
    if result == 'spam':
        print("Possible fraud: " + text)
    return result
