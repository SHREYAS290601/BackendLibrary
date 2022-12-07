from flask import Flask,session,redirect,request,jsonify
from flask_pymongo import PyMongo,pymongo
from flask_mail import Mail,Message
from flask_cors import CORS,cross_origin
from flask_bcrypt import Bcrypt
from bson.json_util import dumps
from pymongo import MongoClient
import json
import time
import datetime
import secrets
app=Flask(__name__)

# !DONT EVEN TOUCH THIS 
with open('./imp.json') as important:
    imp=json.load(important)['params']
connection_string=imp['connections']

# ** VERY IMPORTANT DONT TOUCH
app.config['SECRET_KEY'] = 'f16bbd80d59404'
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = imp['account']
app.config['MAIL_PASSWORD'] = imp['password']
bcrypt = Bcrypt(app)
mail = Mail(app)

# ? This is pymongo to atlas
client=MongoClient(connection_string,connect=True)
db=client['Flask_book_system']

@app.route("/hello")
def check():
    return jsonify(db.flask_login.find().next())

# ** LOGIN ROUTE
@app.route('/login',methods=['GET','POST'])
@cross_origin()
def login():
  my_val=(json.loads(request.data.decode('utf-8')))
  values=db.signup.find_one({'email': my_val['email']})
  if request.method=='POST':
    time_passed=values['time']
    paswd=values['password']
    if (bcrypt.check_password_hash(paswd, my_val['password']) and time_passed==0):
      return {"status": 200}
    elif time_passed!=0:
      time_remaining=time.time()
      if time_remaining-values['time'] >= 86400:
        return "DONE AND VALID"
      else:
        remain=86400+values['time']-time_remaining
        return jsonify({"Time till retry is :":str(time.strftime("%H:%M:%S", time.gmtime(remain)))})
    else:
      session['attempt'] += 1
      # print(session['counter'])
      if session['attempt'] >= 3:
        session['attempt'] = 0
        db.signup.update_one({"email": my_val['email']}, {"$set":{"time":time.time()}})
        return ("You have tried more than 3 times!")
      incorrect={
            "Number of tries remaining":3-session['attempt']
        }
      return jsonify(incorrect)

@app.route('/signup',methods=['GET','POST'])
def sigup():
  my_val=(json.loads(request.data.decode('utf-8')))
  if(db.signup.find_one({'email': my_val['email']})):
    n={
        'Warning':"An account already exists with the same email!Try another one"
    }
    return jsonify(n)
  else:
    password = bcrypt.generate_password_hash(
        my_val['password']).decode('UTF-8')
    db.signup.insert_one(
        {'name': my_val['name'], 'password': password, 'email': my_val['email'], 'phone': my_val['phone'],'address':my_val['address'],'time':0})

    # return (redirect(url_for('home')))
    account=request.form
    return (jsonify(account))

@app.route('/forget-pass',methods=['GET','POST'])
def forgetpass():
  my_val=request.form.get('email')
  print(my_val)#change this later
  if request.method=='POST':
    if db.signup.find_one({'email':my_val}):
      msg = Message('This is your verification code!!',sender=imp['account'], recipients=[my_val])#change this later
      password_length = 13
      password_to_email = (secrets.token_urlsafe(password_length))
      msg.body = f"Here is your verification code.Verify and dont share this code (shuush!!): {password_to_email}"
      # print(type(msg.body))
      mail.send(msg)
      db.signup.find_one_and_update({"email":my_val},{"$set":{"verification":password_to_email}})
      msg={
             'Message':"Kindly check your email for the verification Code!"
         }
      return msg
    else:
      return ("Wrong verification!!")

@app.route('/password-change',methods=['GET','POST'])
def paswword_change():
  if request.method=='POST':
    if(db.signup.find({"verification":request.form.get('verification')})):
      password=bcrypt.generate_password_hash(request.form.get('newpass')).decode('UTF-8')
      verification=request.form.get('verification')
      db.signup.update_one({'verification':verification},{"$set":{'password':password}})
      return ("Password changed")
    else:
      return ('Wrong Verification!')

@app.route('/book/<isbn>',methods=['POST', 'GET'])
def isbn_display(isbn):
  my_val=db.books.find_one({"isbn":isbn})
  print(my_val)
  return my_val

@app.route('/admin',methods=['GET','POST'])
def admin():
  pass

@app.route('/books',methods=['GET','POST'])
def books():
  store=[]
  for post in db.books.find({"longDescription":{"$exists":"true"}}):
    store.append(post)
  return store[0:100]

if __name__=="__main__":
    app.run(debug=True)