from flask import Flask, request, jsonify
import os
import pickle
import pandas as pd
import sqlite3

# os.chdir(os.path.dirname(__file__)) # da error en terminal
app = Flask(__name__)
# app.config['DEBUG'] = True
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

@app.route("/", methods=['GET'])
def hello():
    return "Bienvenid@ a nuestra app de Several Energy"

# 1

@app.route('/predict', methods=['GET'])
def predict_list():
    model = pickle.load(open('data/advertising_model','rb'))
    data = request.get_json()   #{"data": [[100, 100, 200]]}

    input_values = data['data'][0]
    tv, radio, newspaper = map(int, input_values)

    prediction = model.predict([[tv, radio, newspaper]])
    return jsonify({'prediction': round(prediction[0], 2)})


#2

@app.route('/ingest', methods=['POST'])
def add_data():
    data = request.get_json()

    for row in data.get('data', []):
        tv, radio, newspaper, sales = row
        query = "INSERT INTO Advertising (tv, radio, newspaper, sales) VALUES (?, ?, ?, ?)"
        connection = sqlite3.connect('data/Advertising.db')
        crsr = connection.cursor()
        crsr.execute(query, (tv, radio, newspaper, sales))
        connection.commit()
        connection.close()

    return jsonify({'message': 'Datos ingresados correctamente'})

#3

@app.route('/retrain', methods=['POST'])
def retrain():
    conn = sqlite3.connect('data/Advertising.db')
    crsr = conn.cursor()
    query = "SELECT * FROM Advertising;"
    crsr.execute(query)
    ans = crsr.fetchall()
    conn.close()
    names = [description[0] for description in crsr.description]
    df = pd.DataFrame(ans, columns=names)
    model = pickle.load(open('data/advertising_model', 'rb'))
    X = df[["TV", "newspaper", "radio"]]
    y = df["sales"]
    model.fit(X, y)
    pickle.dump(model, open('data/advertising_model', 'wb'))

    return jsonify({'message': 'Modelo reentrenado correctamente.'})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)