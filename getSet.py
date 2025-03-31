from flask import Flask, request, jsonify

app = Flask(__name__)

# Endpoint to get a default message
@app.route('/get', methods=['GET'])
def get_message():
    return jsonify({'message': 'Hello !'})

# Endpoint to set a custom message with the user's name
@app.route('/set', methods=['POST'])
def set_message():
    data = request.json
    name = data.get('name', 'there')
    return jsonify({'message': f'Hello {name}'})

if __name__ == '__main__':
    app.run(port=5000, host='0.0.0.0')