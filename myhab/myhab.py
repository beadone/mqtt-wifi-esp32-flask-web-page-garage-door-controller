from flask import Flask, render_template, url_for, redirect, flash,jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
import os
from datetime import datetime, timezone
from queue import Queue
from paho.mqtt import client as mqtt_client
import time
import json

basedir = os.path.abspath(os.path.dirname(__file__))
port = 1883
#MqttTopicIn = "esp-8266-in"
#topic = "garage/door"
#msg = "status2"

client_id = 'web'
username = 'ralph'
password = 'Batman07!'

q=Queue()
messages=[]
broker = '192.168.1.18'



def on_connect(client, userdata, flags, rc):
    if rc==0:
        client.connected_flag=True #set flag
        print("in callback, connected OK",rc)
    else:
        print("Bad connection Returned code=",rc)
        client.bad_connection_flag=True




def publish(client,topic,msg):
    result = client.publish(topic, msg)
        # result: [0, 1]
    mqttstatus = result[0]
    if mqttstatus == 0:
        print(f"Send `{msg}` to topic `{topic}`")
    else:
        print(f"Failed to send message to topic {topic}")
    return result


#def on_message(client, userdata, msg):
#    x = datetime.now()
#    print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic  at '{x}'")
#    m=str(msg.payload.decode("utf-8"))
#    messages.append(m)#put messages in list
#    q.put(m) #put messages on queue
#    client.loop_stop()
#    client.disconnect()
#    print("mqtt disconnected")

def subscribe(client: mqtt_client,mqtttopic):
    def on_message(client, userdata, msg):
        x = datetime.now()
        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic  at '{x}'")

    #global messages
        #m="message received  "  ,str(msg.payload.decode("utf-8"))
        m=str(msg.payload.decode("utf-8"))
        messages.append(m) #put messages in list
        q.put(m) #put messages on queue
        print("message received  ",m)
        client.loop_stop()
        client.disconnect()

    client.subscribe(mqtttopic)
    client.on_message = on_message


myhab = Flask(__name__)


#myhab.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///myhab.db'

myhab.config['SQLALCHEMY_DATABASE_URI'] ='sqlite:///' + os.path.join(basedir, 'myhab.db')
myhab.config['SECRET_KEY'] = 'mykey'

bcrypt = Bcrypt(myhab)

db = SQLAlchemy(myhab)
login_manager = LoginManager()
login_manager.init_app(myhab)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@myhab.before_request
def before_request():
    if current_user.is_authenticated:
        #current_user.last_seen = datetime.now(timezone.utc)
        current_user.last_seen = datetime.now()
        db.session.commit()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    last_seen = db.Column(db.DateTime, nullable=True)

class Sensordata(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    DeviceName = db.Column(db.String(50), nullable=False)
    SensorType = db.Column(db.String(80), nullable=False)
    Value = db.Column(db.String(80), nullable=False)
    Timestamp = db.Column(db.DateTime, nullable=True)




class RegisterForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Register')

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(
            username=username.data).first()
        if existing_user_username:
            raise ValidationError(
                'That username already exists. Please choose a different one.')


class LoginForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Login')

@myhab.route('/')
@myhab.route('/home')
@myhab.route('/index')
@login_required
def home():
   
    return render_template('home.html', title='Home')

@myhab.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not bcrypt.check_password_hash(user.password, form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user)
        return redirect(url_for('home'))

    return render_template('login.html', form=form, title='Login')


@myhab.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    
    return render_template('register.html', form=form, title='Register')

@myhab.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@myhab.route('/getstatus', methods=['GET', 'POST'])
@login_required
def getstatus():
    print ("In get status")
    if request.method == "POST":
        print ("method is POST")
        datain1 = request.values
        #print(len(datain1))
        for item in datain1:
            topicin = item
            print (topicin)
            msg = request.values.get(topicin)
            print (msg)
            #if (msg == "status") or (msg == "press"):
            #    topic = "garage/door"
        #topic = "garage/door"
        client = mqtt_client.Client(client_id)
        client.username_pw_set(username, password)
        x = datetime.now() 
        mqttstatus = client.connect(broker, port,60)
        print (mqttstatus,x)
        if mqttstatus != 0:
            print ("Couldn't connect to the mqtt broker")
        else:
            topic = "garage/door"
            
            #MqttTopicIn = "esp-8266-in"
            MqttTopicIn = topicin
            #msg = "status"
            time.sleep(1)
            x = datetime.now()
            print ("MQTT connected",x)
            result = client.publish(MqttTopicIn,msg )
            status = result[0]
            x = datetime.now()
            if status == 0:
                print (f"Send `{msg}` to topic `{MqttTopicIn}` at '{x}'")
                print ("loop started")
                subscribe(client,topic)
                x = datetime.now()
                print ("subscribed", x)
                client.loop_forever()
            else:
                print (f"Failed to send message to topic {MqttTopicIn}")


        while q.empty():
            print ("waiting for reply")
            time.sleep(1)

        while not q.empty():
            message = q.get()
            print ("queue: ",message)
            return jsonify({'output':message})

        q.queue.clear()

        #return jsonify({'output':'OPEN'})
        #return jsonify({'output':message})
    else:
        print ("not post")

        return render_template('home.html',title='Home')


if __name__ == "__main__":
    myhab.run(host='0.0.0.0')
    #myhab.run(host='0.0.0.0',ssl_context='adhoc')
   
    #myhab.run(debug=True)



