import os, time
from flask import Flask, request
from flask_cors import CORS, cross_origin

if not os.path.exists("requests"):
    os.makedirs("requests")

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route("/body", methods=["POST"])
@cross_origin()
def save_request_body():
    with open(f"requests/{time.time()}.txt", "wb") as f:
        f.write(request.data)
    return "OK"

app.run(host='0.0.0.0', port=5031)