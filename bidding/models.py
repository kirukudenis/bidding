from datetime import datetime
from flask_login import UserMixin
import secrets
from bidding import db, ma, login_manager
from dateutil import parser
import random
from flask import request, redirect, url_for


@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception:
        return redirect(url_for(request.url_rule.endpoint))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(100), unique=False, nullable=False)
    name = db.Column(db.String(100), unique=False, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, name, email, phone, password):
        self.name = name
        self.email = email
        self.phone = phone
        self.password = password


class UserSchema(ma.Schema):
    class Meta:
        fields = ("id", "name", "phone", "email", "image_file", "password")


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(250), nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default="default.jpg")
    sold = db.Column(db.Boolean, nullable=False, default=False)
    description = db.Column(db.Text, nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, user, name, image_file, description):
        self.user = user
        self.name = name
        self.image_file = image_file
        self.description = description


class ItemSchema(ma.Schema):
    class Meta:
        fields = ("user", "name", "image_file", "sold", "description", "date_added")


class Bid(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.ForeignKey('user.id'), nullable=False)
    item = db.Column(db.ForeignKey('item.id'), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, user, item, price):
        self.user = user
        self.item = item
        self.price = price


class BidSchema(ma.Schema):
    class Meta:
        fields = ("user", "item", "price", "date_added")
