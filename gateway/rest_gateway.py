#!/usr/bin/env python
from flask import Flask, jsonify
from flask import make_response, abort, request
import pika
import time
import sys
import json
import uuid

app = Flask(__name__)

eval_requests = [
     {
      "id": 1,
      "seller_no": 1234,
      "seller_name": "Wells Fargo Retail",
      "request_id": 12345,
      "ulad": {}
    },
    {
      "id": 2,
      "seller_no": 1234,
      "seller_name": "Wells Fargo Retail",
      "request_id": 12345,
      "ulad": {}
    }
]

eval_requests[0]["request_id"] = uuid.uuid4().hex
eval_requests[1]["request_id"] = uuid.uuid4().hex

# http://[hostname]/loaneval/api/v1.0/requests

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

@app.route('/')
def hello():
    return 'Hello World! I have been seen %s times.' % 24

@app.route('/loaneval/api/v1.0/requests', methods=['GET'])
def get_requests():
    return jsonify({'requests': eval_requests})

@app.route('/loaneval/api/v1.0/requests/<int:request_id>', methods=['GET'])
def get_request(request_id):
    request = [request for request in eval_requests if request['request_id'] == request_id]
    if len(request) == 0:
        abort(404)
    return jsonify({'request': request[0]})

@app.route('/loaneval/api/v1.0/requests', methods=['POST'])
def create_request():
    if not request.json or not 'seller_no' in request.json:
        abort(400)
    id = uuid.uuid4()
    eval_request = {
      'id': eval_requests[-1]['id'] + 1,
      'seller_no': request.json['seller_no'],
      'seller_name': request.json['seller_name'],
      'request_id': id.hex,
      'ulad': {}
    }
    eval_requests.append(eval_request)
    eval_request['timestamp'] = time.time()
    publish_eval_request(eval_request)
    return jsonify({'request': eval_request}), 201

def publish_eval_request(eval_request):
    publish_key = 'pml.eval.request'
    eval_request["timestamp"]=time.time()
    print "rest gateway publishing pml.eval.request: %r:%r" % (eval_request["request_id"], eval_request["timestamp"])
    message = json.dumps(eval_request)
    channel.basic_publish(exchange='topic_loan_eval',
                          routing_key=publish_key,
                          body=message)

@app.route('/loaneval/api/v1.0/send/<int:count>', methods=['POST'])
def publish_requests(count):
  if count > len(eval_requests):
    return jsonify({'error': "count > rows in database"})
  for i in range(count):
    publish_eval_request(eval_requests[i])

  return jsonify({'sent': count})

@app.route('/loaneval/api/v1.0/send/', methods=['GET'])
def count_requests():
    return jsonify({'count': len(eval_requests)})

if __name__ == "__main__":
  try:
    mq_host = sys.argv[1]
  except IndexError:
    mq_host = 'localhost'

  connection = pika.BlockingConnection(pika.ConnectionParameters(host=mq_host))
  channel = connection.channel()
  channel.queue_declare(queue='pml.eval.request')


  app.run(host="0.0.0.0", debug=True)