import os
import base64
import re #import re
import webview
import requests
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
login_manager.init_app(app)

cred = credentials.Certificate(os.path.join(os.path.dirname(__file__),'db.json'))
firebase_admin.initialize_app(cred)
db = firestore.client()


class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

def prayatna_api_hit():
    url = 'http://13.48.136.54:8000/api/api-code/'
    api = "6e115e80-aff0-4174-9222-e5a7a37ce35b"
    bearer = "Bearer " + api

    headers = {"Authorization": bearer,
            'Content-Type': 'application/json'}
    
    response = requests.post(url, headers=headers)
    cont = response.content

    return cont

def add_record(user_id, bill_name, due_date, amount):
    if datetime.strptime(due_date, '%Y-%m-%d') < datetime.now():
        record_ref = db.collection('users').document(user_id).collection('records').document()
        record_ref.set({
            'Date': due_date,
            'type': 'debit',
            'amount': amount,
            'reason': bill_name,
            'description': "Automatically generated  record for bill: " + bill_name
        })

def send_email(username, email, password, totp_secret):
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']

    creds = None

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json')
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('mail.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    service = build('gmail', 'v1', credentials=creds)

    google_authy = "https://play.google.copm/store/apps/details?id=com.google.android.apps.authenticator2&hl=eng&gl=US"

    message = MIMEMultipart()
    message['to'] = email
    message['subject'] = 'Registration Details'
    email_body = f"Here Are Your Detailsfor the app, Keep them Safely: \nUsername: {username} \nEmail: {email} \nPassword: {password} \nTOTP Secret: {totp_secret} \n Use The above TOTP Secret with a Authenticator app like {google_authy}. IF this secret gets lost, You'll Lose Your 'Account'. "
    message.attach(MIMEText(email_body, 'plain'))

    raw_message = base64.urlsafe_b64encode(message.as_bytes())
    raw_message = raw_message.decode()

    service.users().messages().send(userId='me', body = {'raw': raw_message}).execute()

def totp_verify(otp, totp_secret):
    totp = pyotp.TOTP(totp_secret)
    return totp.verify(otp)

genai.configure(api_key="AIzaSyB5b3yOq6uW3V32P5WeCEDuU-KSGP1hfbU")  # Set the API key for the Generative AI service
generation_config = {
  "temperature": 1,
  "top_p": 1,
  "top_k": 1,
  "max_output_tokens": 4096,
}
safety_settings = [
  {
    "category": "HARM_CATEGORY_HARASSMENT",
    "threshold": "BLOCK_ONLY_HIGH"
  },
  {
    "category": "HARM_CATEGORY_HATE_SPEECH",
    "threshold": "BLOCK_ONLY_HIGH"
  },
  {
    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "threshold": "BLOCK_ONLY_HIGH"
  },
  {
    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    "threshold": "BLOCK_ONLY_HIGH"
  },
]
model = genai.GenerativeModel(model_name="gemini-1.0-pro-001", generation_config=generation_config, safety_settings=safety_settings)

@app.route('/')
def index():
    access = prayatna_api_hit()
    return render_template('index.html', access)


@app.route('/register', methods=['GET', 'POST'])
def register():
    access = prayatna_api_hit()
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
                'bank_balance': bank_balance,
                'totp_secret': totp_secret
            })

            send_email(username, email, password, totp_secret)

            return redirect(url_for('index'))
        else:
            return "Passwords Do Not Match, Please Try Again"
        
    return render_template('register.html', access)
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    access = prayatna_api_hit()
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
    return render_template('login.html', access=access)

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    access = prayatna_api_hit()
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
    return render_template('forgotpassword.html', access)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required 
def dashboard():
    
    user_id = current_user.id
    records_ref = db.collection('users').document(user_id).collection('records')    
    records = records_ref.get()

    earnings = 0.0  
    expenses = 0.0  
    for record in records:  
        record_data = record.to_dict()
        if record_data['Date']: 
            if record_data['type'] == 'credit':   
                earnings += float(record_data['amount'])    
            elif record_data['type'] == 'debit':    
                expenses += float(record_data['amount'])    
    reminders_ref = db.collection('users').document(user_id).collection('bill_reminders').get()
    reminders = [reminder.to_dict() for reminder in reminders_ref]

    
    for reminder in reminders:  
        due_date_str = reminder['due_date'] 
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
        recurrence = reminder['recurrence']
        
        if due_date < datetime.now():   
            if recurrence == 'daily':   
                delta = timedelta(days=1)   
            elif recurrence == 'weekly':    
                delta = timedelta(weeks=1)  
            elif recurrence == 'monthly':   
                delta = timedelta(days=30)   
            else:   
                delta = None    
            
            if delta:   
                while due_date < datetime.now():
                    due_date += delta   
                reminder_ref = db.collection('users').document(user_id).collection('bill_reminders').document(reminder['bill_name'])
                reminder_ref.update({'due_date': due_date.strftime('%Y-%m-%d')})    

    goals_ref = db.collection('users').document(user_id).collection('goals').get()
    goals = [goal.to_dict() for goal in goals_ref]  

    balance_ref = db.collection('users').document(user_id)  
    current_balance = balance_ref.get().to_dict().get('bank_balance', 0)    

    if goals_ref != []: 
        earnings_goal = 0.0 
        expenses_goal = 0.0 
        for record in records:  
            record_data = record.to_dict()
            if record_data['Date']: 
                if record_data['type'] == 'credit':
                    earnings_goal += float(record_data['amount'])
                elif record_data['type'] == 'debit':
                    expenses_goal += float(record_data['amount'])
        
        goal_ref = db.collection('users').document(user_id).collection('goals').get()   
        for goal in goal_ref:   
            goal_data = goal.to_dict()  
            if goal_data['target_amount']:  
                goals_doc = float(goal_data['target_amount'])
                remaining_goal = goals_doc - current_balance if goals_doc is not None else None
    else:   
        remaining_goal = None   
        earnings_goal = None    
        expenses_goal = None    

    
    return render_template('dashboard.html', records=records, reminders=reminders, goals=goals, remaining_goal=remaining_goal, earnings_goal=earnings_goal, expenses_goal=expenses_goal, current_balance=current_balance, earnings=earnings, expenses=expenses) 


if __name__ == "__main__":
    app.run(debug=True)
