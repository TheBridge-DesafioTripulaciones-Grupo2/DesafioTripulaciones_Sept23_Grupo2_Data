<<<<<<< HEAD
from flask import Flask, jsonify, request
from datos_dummy import books

app = Flask(__name__)
app.config["DEBUG"] = True



@app.route('/', methods=['GET'])
def home():
    return "<h1>Api test</h1><p>This site is just a test for </p>"

# 1.Ruta para obtener todos los libros
@app.route('/v0/books', methods=['GET'])
def all_books():
    return jsonify(books)
    
# 2.Ruta para obtener un libro concreto mediante su id como parámetro en la llamada
@app.route('/v0/book_id', methods=['GET'])
def book_id():
    id = int(request.args['id'])
    results = [book for book in books if book["id"]==id]
    return results


# 3.Ruta para obtener un libro concreto mediante su título como parámetro en la llamada de otra forma
@app.route('/v0/book/<string:title>', methods=["GET"])
def book_title(title):
    results = [book for book in books if book["title"].lower()==title.lower()]
    return results


# 4.Ruta para obtener un libro concreto mediante su titulo dentro del cuerpo de la llamada  
@app.route('/v1/book', methods=["GET"])
def book_title_body():
    title = request.get_json().get('title', None)
    if not title:
        return "Not a valid title in the request", 400
    else:
        results = [book for book in books if book["title"].lower()==title.lower()]
        if results == []:
            return "Book not found" , 400
        else:
            return results

# 5.Ruta para añadir un libro mediante un json en la llamada
@app.route('/v1/add_book', methods=["POST"])
def post_books():
    data = request.get_json()
    books.append(data)
    return books


# 6.Ruta para añadir un libro mediante parámetros
@app.route('/v2/add_book', methods=["POST"])
def post_books_v2():
    book = {}
    book['id'] = int(request.args['id'])
    book['title'] = request.args['title']
    book['author'] = request.args['author']
    book['first_sentence'] = request.args['first_sentence']
    book['published'] = request.args['published']
    books.append(book)
    return books

app.run()



"""def home():
    return render_template('index.html')"""

"""@app.route('/ingest', methods=['POST'])
def ingest():
    data = request.get_json()
    new_data = data.get('data', None)
    if not new_data:
        return {"error":"No se proporcionaron datso para agregar a la bbdd"}, 400

    try:
        connection = sqlite3.connect('data/advertising.db')
        cursor = connection.cursor()
        query = "INSERT INTO campañas VALUES (?,?,?,?)"
        for valor in new_data:
            cursor.execute(query, valor)
        connection.commit()
        connection.close()
        return {'message': 'Datos ingresados correctamente'}, 200
    except Exception as e:
        return {'error':str(e)}, 500"""

"""@app.route('/retrain', methods=['POST'])
def retrain():
    try:
        connection = sqlite3.connect('data/advertising.db')
        cursor = connection.cursor()
        query = '''SELECT * FROM campañas'''
        result = cursor.execute(query).fetchall()
        df = pd.DataFrame(result)
        model.fit(df.iloc[:,:-1], df.iloc[:,-1])
        with open('data/new_advertising_model.pkl', 'wb') as file:
            pickle.dump(model, file)
        return {'message': 'Modelo reentrenado correctamente.'}, 200
    except Exception as e:
        return {'error':str(e)}, 500"""

=======
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
>>>>>>> branch_Agui
