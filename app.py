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



class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

