import ml
import binascii
import logging
from flask import Flask
from flask import request

app = Flask(__name__)
antispammer = ml.AntiSpammer()
antispammer.train()

@app.route('/predict', methods=['POST'])
def api_predict():
    text = request.form.get('text')
    result = antispammer.predict(text)
    if result == 'spam':
        print("Possible spam: " + text)
    return result
