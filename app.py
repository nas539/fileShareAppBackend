from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from flask_heroku import Heroku
from flask_bcrypt import Bcrypt
import io

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgres://iozprlkgpixzbx:d3ac6929f6ebc621a5ef36f597a2dedc96347670dc0d5a2f44188710c3bd8e6a@ec2-3-216-129-140.compute-1.amazonaws.com:5432/d5g69tfq3bbplh"

db = SQLAlchemy(app)
ma = Marshmallow(app)

heroku = Heroku(app)
CORS(app)
bcrypt = Bcrypt(app)

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    file_type = db.Column(db.String(), nullable=False)
    data = db.Column(db.LargeBinary, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    def __init__(self, name, file_type, data, user_id):
        self.name = name
        self.file_type = file_type
        self.data = data
        self.user_id = user_id

class FileSchema(ma.Schema):
    class Meta:
        fields = ("id", "name", "file_type")

file_schema = FileSchema()
files_schema = FileSchema(many=True)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(), nullable=False)
    files = db.relationship("File", cascade="all,delete", backref="user", lazy=True)

    def __init__(self, username, password):
        self.username = username
        self.password = password

class UserSchema(ma.Schema):
    class Meta:
        fields = ("id", "username", "password")

user_schema = UserSchema()
users_schema = UserSchema(many=True)




@app.route("/file/add", methods=["POST"])
def add_file():
    name = request.form.get("name")
    file_type = request.form.get("type")
    data = request.files.get("data")

    new_file = File(name, file_type, data.read())
    db.session.add(new_file)
    db.session.commit()

    return jsonify("File added!")

@app.route("/file/get/data", methods=["GET"])
def get_file_data():
    file_data = db.session.query(File).all()
    return jsonify(files_schema.dump(file_data))


@app.route("/file/get/<id>", methods=["GET"])
def get_file(id):
    file_data = db.session.query(File).filter(File.id == id).first()
    return send_file(io.BytesIO(file_data.data), 
                     attachment_filename=file_data.name,
                     mimetype=file_data.file_type)

@app.route("/file/delete/<id>", methods=["DELETE"])
def delete_file(id):
    file_data = db.session.query(File).filter(File.id == id).first()
    db.session.delete(file_data)
    db.session.commit()
    return jsonify("FileDeleted")

@app.route("/user/create", methods=["POST"])
def create_user():
    if request.content_type != "application/json":
        return jsonify("Error")

    post_data = request.get_json()
    username = post_data.get("username")
    password = post_data.get("password")

    username_check = db.session.query(User.username).filter(User.username = username).first()
    if username_check is not None:
        return jsonify("Username taken")

    hashed_password = bcrypt.generate_password_hash(password).decode("utf8")

    record = User(username, hashed_password)
    db.session.add(record)
    db.session.commit()

    return jsonify("User created")

@app.route("/user/get", methods=["GET"])
def get_all_users():
    all_users = db.session.query(User).all()
    return jsonify(users_schema.dump(all_users))

@app.route("/user/get/<id>", methods=["GET"])
def get_user_by_id(id):
    user = db.session.query(User).filter(User.id == id).first()
    return jsonify(user_schema.dump(user))

@app.route("/user/verification", methods=["POST"])
def verify_user():
    if request.content_type != "application/json":
        return jsonify("Error, data must be sent as json")

    post_data = request.get_json()
    username = post_data.get("username")
    password = post_data.get("password")

    stored_password = db.session.query(User.password).filter(User.username == username).first()
    print(stored_password)
    print(password)

    if stored_password is None:
        return jsonify("User not Verified")

    valid_password_check = bcrypt.check_password_hash(stored_password[0], password)

    if valid_password_check == False:
        return jsonify("User not Verified")

    return jsonify("User verified")
   
if __name__ == "__main__":
    app.run(debug=True)