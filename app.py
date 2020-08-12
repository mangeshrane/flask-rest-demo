from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from flask_marshmallow import Marshmallow
from marshmallow import Schema, fields
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from werkzeug.exceptions import HTTPException
import os
import json

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'books_store.db')
app.config['JWT_SECRET_KEY'] = 'super-secret'

db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)

@app.cli.command('db_drop')
def db_drop():  
    db.drop_all()

@app.cli.command('db_create')
def db_create():
    db.create_all()

@app.cli.command('db_seed')
def db_seed():
    mangesh = Author(first_name='Mangesh',
                    last_name='Rane',
                    email='test@test.com',
                    password='xscdjf')
    alex = Author(first_name='alex',
                    last_name='alex',
                    email='test@test.com',
                    password='xscdjf')
    june = Author(first_name='june',
                    last_name='ohm',
                    email='test@test.com',
                    password='xscdjf')
    book = Books(book_name='Harry Potter', isbn='ANAF14816C')
    book1 = Books(book_name='Fantastic beasts', isbn='ANAF14916C')
    mangesh.books.append(book)
    mangesh.books.append(book1)
    db.session.add(mangesh)
    db.session.add(book)
    db.session.add(alex)
    db.session.add(june)
    db.session.commit()


    print(Author.query.all())


@app.route('/')
@jwt_required
def hello_world():
    return "Hello World "

@app.route('/message')
def some_route():
    return jsonify(message="some message")

@app.route('/not_found')
def not_found():
    return jsonify(message='resource not found'), 404

@app.route('/query')
def query_params():
    return jsonify(message='requested data', **request.args)

@app.route('/path/<string:name>/<int:age>')
def path_param(name: str, age: int):
    return jsonify(name=name, age=age)

@app.route('/author', methods=['GET'])
def authors():
    authors = Author.query.all()
    resp = authors_schema.dump(authors)
    return jsonify(resp)

@app.route('/author/<int:id>', methods=['GET'])
def authors_by_id(id):
    authors = Author.query.get(id)
    if not authors:
        return jsonify(message="Requested author does not exist")
    resp = author_schema.dump(authors)
    return jsonify(resp)

@app.route('/author/<int:id>', methods=['DELETE'])
def delete_author(id):
    author = Author.query.get(id)
    if not author:
        return jsonify(message="Requested author does not exist")
    db.session.delete(author)
    db.session.commit()
    resp = author_schema.dump(author)
    return jsonify(resp)

@app.route('/author/<int:id>', methods=['PUT'])
def update_author(id):
    req = request.json
    author = Author.query.get(id)
    if not author:
        return jsonify(message="Requested author does not exist")
    if req.get('first_name'):
        author.first_name = req.get('first_name')
    if req.get('last_name'):
        author.last_name = req.get('last_name')
    if req.get('email'):
        author.email = req.get('email')
    db.session.add(author)
    db.session.commit()
    resp = author_schema.dump(author)
    return jsonify(resp)

@app.route('/book')
def get_books():
    book = Books.query.all()
    if book:
        return jsonify(books_schema.dump(book))
    else:
        return jsonify(message='No books found')


@app.route('/register', methods=['POST'])
def register():
    first_name = request.form.get('firstName')
    last_name = request.form.get('lastName')
    email = request.form.get('email')
    password = request.form.get('password')
    if Author.query.filter_by(email=email).first():
        return jsonify(message='User already registered with ' + email)
    else:
        db.session.add(Author(first_name=first_name, last_name=last_name, email=email, password=password))
        db.session.commit()
        return jsonify(message='user successfully registered')

@app.route('/login', methods=['POST'])
def login():
    if request.json:
        email = request.json['email']
        password = request.json['password']
    elif request.form.get('email') and request.form.get('password'):
        email = request.form.get('email')
        password = request.form.get('password')
    else:
        return jsonify(message='valid username/ password is required')
    if Author.query.filter_by(email=email, password=password).first():
        token = create_access_token(email)
        return jsonify(message='Login successful !', token=token)
    else:
        return jsonify(message='Please provide valid username/ password')


@app.errorhandler(HTTPException)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        "name": e.name,
        "description": e.description,
    })
    response.content_type = "application/json"
    return response

# @app.errorhandler(Exception)
# def handle_exception(e):
#     # pass through HTTP errors
#     if isinstance(e, HTTPException):
#         return e
#     print(e)
#     return jsonify(message=" An error occured while processing request"), 500

# models
class Author(db.Model):
    __tablename__ = 'author'
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String)
    password = Column(String)
    books = relationship("Books", back_populates='author')

    def create(self):
        db.session.add(self)
        db.session.commit()
        return self

class Books(db.Model):
    __tablename__ = 'books'
    id = Column(Integer, primary_key=True)
    book_name = Column(String(100))
    isbn = Column(String(10))
    author_id = Column(ForeignKey('author.id'))
    author = relationship("Author", back_populates='books')

class AuthorsSchema(ma.Schema):
    class Meta:
        fields = ('id', 'first_name', 'last_name', 'email')

class BookSchema(ma.Schema):
    id = fields.Integer()
    book_name = fields.String()
    isbn = fields.String()
    author = fields.Nested(AuthorsSchema)


authors_schema = AuthorsSchema(many=True)
author_schema = AuthorsSchema()
books_schema = BookSchema(many=True)