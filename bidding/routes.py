import json
import logging
import os
import re
import secrets
import socket
import time
from copy import deepcopy
import timeago
from datetime import timedelta
import requests
import socketio
from dateutil import parser
from flask import render_template, url_for, flash, redirect, request, abort, jsonify, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from flask_sqlalchemy import sqlalchemy
from PIL import Image
from bidding import app, db, bcrypt, image_path
from bidding.forms import (RegisterForm, LoginForm, PostItemForm)
from bidding.models import User, UserSchema, ItemSchema, Item, BidSchema, Bid
from bidding.utility import email
from werkzeug.utils import secure_filename

user_schema = UserSchema()
users_schema = UserSchema(many=True)


@app.route("/")
def home():
    items = Item.query.filter_by(sold=False).all()
    final = []
    for item in items:
        winning = Bid.query.filter_by(item=item.id).order_by(Bid.price.desc()).first()
        x = {
            "winning": winning,
            "item": item,
        }
        final.append(x)
    return render_template("home.html", items=final)


@app.route("/item/all")
@login_required
def my_items():
    sold = Item.query.filter_by(sold=True).filter_by(user=current_user.get_id()).all()
    instock = Item.query.filter_by(sold=False).filter_by(user=current_user.get_id()).all()
    final_winning = []
    for item in sold:
        winning = Bid.query.filter_by(item=item.id).order_by(Bid.price.desc()).first()
        x = {
            "winning": winning,
            "item": item
        }
        final_winning.append(x)

    final_instock = []
    for item in instock:
        winning = Bid.query.filter_by(item=item.id).order_by(Bid.price.desc()).first()
        x = {
            "winning": winning,
            "item": item
        }
        final_instock.append(x)

    return render_template("my_items.html", sold=final_winning, instock=final_instock)


@app.route("/item/sell/upload", methods=["GET", "POST"])
@login_required
def sell_item():
    form = PostItemForm()
    if request.method == "POST":
        if form.validate_on_submit():
            user_logged_in = current_user.get_id()
            name = form.name.data
            image = form.image.data
            description = form.description.data
            item = Item(user_logged_in, name, image.filename, description)
            db.session.add(item)
            db.session.commit()
            # save file
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.root_path, "static", 'images', filename))
            flash("Items added successfully", "success")
            return redirect(url_for("my_items"))
    return render_template("sell_item.html", form=form)


@app.route("/item/view/<int:id>", methods=["GET", "POST"])
@login_required
def view_item_single(id):
    this_user = current_user.get_id()
    item = Item.query.get(id)
    if item:
        user = User.query.get(this_user)
        last_bid = Bid.query.filter_by(user=this_user).filter_by(item=id).order_by(Bid.date_added.desc()).first()
        winning_bid = Bid.query.filter_by(item=id).order_by(Bid.price.desc()).first()
        winner = []
        if item.sold:
            winner = User.query.get(winning_bid.user)
        return render_template("item_view.html", item=item, current_bid=last_bid, winning_bid=winning_bid,user=user,winner=winner)
    else:
        flash("Error, Item not found", "danger")
        return redirect(url_for("home"))


@app.route("/item/bid/<int:id>", methods=["GET", "POST"])
@login_required
def bid_higher(id):
    item = Item.query.get(id)
    if item:
        this_user = current_user.get_id()
        last_bid = Bid.query.filter_by(user=this_user).filter_by(item=id).order_by(Bid.date_added.desc()).first()
        if last_bid:
            last_bid = last_bid.price
            last_bid = int(last_bid) + 1
            bid = Bid(this_user, item.id, last_bid)
            db.session.add(bid)
            db.session.commit()
            flash(f"A bid of £{last_bid} was successful. ","success")
        else:
            bid = Bid(this_user, item.id, 1)
            db.session.add(bid)
            db.session.commit()
    else:
        flash("Error, Item not found", "danger")
    return redirect(url_for("view_item_single", id=id))


@app.route("/item/mark/sold/<int:id>", methods=["GET", "POST"])
@login_required
def mark_as_sold(id):
    item = Item.query.get(id)
    if item:
        this_user = current_user.get_id()
        last_bid = Bid.query.filter_by(user=this_user).filter_by(item=id).order_by(Bid.date_added.desc()).first()
        last_bid = last_bid.price
        item.sold = True
        db.session.commit()
        flash(f"Item was sold at the price of £{last_bid}.00 .","info")
    else:
        flash("Error, Item not found", "danger")
    return redirect(url_for("my_items"))


def log(msg):
    print(f"{datetime.now().strftime('%d:%m:%Y %H:%M:%S')} — {msg}")
    return True


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/login", methods=["POST", "GET"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    login = LoginForm()
    if login.validate_on_submit():
        user = User.query.filter_by(email=login.email.data).first()
        if user and bcrypt.check_password_hash(user.password, login.password.data):
            next_page = request.args.get("next")
            login_user(user)
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash("Login unsuccessful Please Check Email and Password", "danger")
    return render_template("login.html", form=login)


@app.route("/register", methods=["GET", "POST"])
def register():
    # checking if the current user is logged
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    register = RegisterForm()
    if register.validate_on_submit():
        try:
            name = register.name.data
            email = register.email.data
            phone = register.phone.data
            password = register.password.data
            hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
            user = User(name, email, phone, hashed_password)
            db.session.add(user)
            db.session.commit()
        except sqlalchemy.exc.IntegrityError:
            flash("User By That Email Exists", "warning")
        flash(f"Account Created successfully", "success")
        return redirect(url_for('login'))
    return render_template("register.html", form=register)


# error handling

@app.route("/404")
def review_404():
    # work on the payments templates
    return render_template("payments_reports.html")


@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 404


@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404
