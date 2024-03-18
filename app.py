import os
import base64
import re
import webview
import pyotp
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
import google.generativeai as genai
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = "5#v:O(TMlwMv17sPT6Hh-.b+U}80jGt~MWEJnBWg8a/~.7QdXWO%`P5cYgCk-ci"

window = webview.create_window("Quad Binary Wealth AI", app)

login_manager = LoginManager()
login_required.init_app(app)

cred = credentials.Certificate(os.path.join(os.path.dirname(__file__),'db.json'))
firebase_admin.initialize_app(cred)
db = firestore.client()

def add_record(user_id, bill_name, due_date, amount):
    if datetime.strptime(due_date, '%Y-%m-%d') < datetime.now():
        record_ref = db.collection('users').document(user_id).collection('records').document()
        record_ref.set({
            'Date': due_date,
            'type': 'debit',
            'amount': amount
            'reason': bill_name,
            'description': "Automatically generated  record for bill: " + bill_name
        })

def send_email(username, email, password, totp_secret):
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']

    creds = None

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json')

    if not creds or not 

class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


def totp_verify(otp, totp_secret):
    totp = pyotp.TOTP(totp_secret)
    return totp.verify(otp)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        password_confirm = request.form['repeated_password']
        bank_balance = float(request.form['bank_balance'])

        pass64 = base64.b64encode(password.encode("utf-8"))

        totp_secret = pyotp.random_base32()

        if password == password_confirm:
            if db.collection("users").document(username).get().exists:
                return "Username Already Exists, Please Choose a Different Username"
            
            user_ref = db.collection("users").document(username)
            user_ref.set({
                'username': username,
                'email': email,
                'password': pass64,
                'bank_balance': bank_balance
                'totp_secret': totp_secret
            })

            send_email(username, email, password, totp_secret)

            return redirect(url_for('index'))
        else:
            return "Passwords Do Not Match, Please Try Again"
        
    return render_template('register.html')
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        pass64 = base64.b64encode(password.encode('utf-8'))

        user_ref = db.collection('users').document(username)
        user_doc = user_ref.get()

        if not user_doc.exists or user_doc.to_dict()['password'] != pass64:
            return "Invalid username or password"
        
        totp_secret = user_doc.to_dict()['totp_secret']

        if totp_verify(request.form['totp'], totp_secret):
            user = User(user_id=username)
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            return "Invalid OTP"
    return render_template('login.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        new_password = request.form['new_password']

        user_ref = db.collection('users').document(username)
        user_doc = user_ref.get()

        totp_secret = user_doc.to_dict()['totp_secret']

        if user_doc.exists:
            if user_doc.to_dict()['email'] == email:
                if totp_verify(request.form['totp'], totp_secret):
                    user_ref.update({
                        'password': base64.b64encode(new_password.encode('utf-8'))
                    })
                    return redirect(url_for('login'))
                else:
                    return "Invalid OTP"
            else:
                return "Invalid Email Address"
        else:
            return 'No User Found With Provided Username'
    return render_template('forgotpassword.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

