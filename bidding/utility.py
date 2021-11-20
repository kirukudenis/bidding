import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bidding.models import User, UserSchema
from bidding import db, project_dir
from flask import jsonify, request
import sqlalchemy
from werkzeug.utils import secure_filename
import os
from bidding import app
from youtube_search import YoutubeSearch
import json
import random
import requests
from requests.auth import HTTPBasicAuth
from base64 import b64encode
from datetime import datetime
from PIL import Image, ImageFilter
import re

from datetime import datetime
from collections import namedtuple
from dateutil import parser

user_schema = UserSchema()
users_schema = UserSchema(many=True)


def email(_to, subject, body):
    _from = "admin@bidding.com"
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = _from
    message["To"] = _to

    # Turn these into plain/html MIMEText objects
    part = MIMEText(body, "html")
    # Add HTML/plain-text parts to MIMEMultipart message
    message.attach(part)
    # Create secure connection with server and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("mail.bidding.com", 465, context=context) as server:
        server.login(_from, "Japanitoes")
        if server.sendmail(_from, _to, message.as_string()):
            return True
        else:
            return False
