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
from fuprox import app, db, bcrypt, image_path

from fuprox.forms import (RegisterForm, LoginForm, TellerForm, ServiceForm, SolutionForm, EditUsers,
                          ActivateForm, AddUser, PasswordCode, Passwords, Code, WallpaperForm, LogoForm,
                          DeleteWallpaper)

from fuprox.models import User, Company, Branch, Service, Help, BranchSchema, CompanySchema, ServiceSchema, Mpesa, \
    MpesaSchema, Booking, BookingSchema, ImageCompanySchema, Teller, TellerSchema, ServiceOffered, Icon, \
    PhraseSchema, Phrase, ServiceOfferedSchema, VideoSchema, Video, ResetOption, ResetOptionSchema, \
    TellerBooking, Recovery, Wallpaper, WallpaperSchema, LogoSchema, Logo, UserSchema,Day

from fuprox.utility import reverse, add_teller, create_service, upload_video, get_single_video, get_all_videos, \
    get_active_videos, toggle_status, upload_link, delete_video, save_icon_to_service, has_vowels, get_youtube_links, \
    save_code, code_exists, email, password_code_request, blur_image, get_ticket_time, todays_bookings, seed_days, \
    add_schedule_db, schedule_overlap, service_by_unique, service_schedule, days, users,schedule_by_unique, \
    delete_schedule, service_by_schedule,get_schedule,edit_schedule_db

teller_schema = TellerSchema()
tellers_schema = TellerSchema(many=True)

# socket_link = "http://localhost:5000/"
socket_link = "http://159.65.144.235:5000/"
local_socket = "http://localhost:5500/"

sio = socketio.Client()
local = socketio.Client()

# rendering many route to the same template
branch_schema = BranchSchema()

service_schema = ServiceSchema()
services_schema = ServiceSchema(many=True)

service_offered_schema = ServiceOfferedSchema()
services_offered_schema = ServiceOfferedSchema(many=True)

company_schema = CompanySchema()

wallpaper_schema = WallpaperSchema()
logo_schema = LogoSchema()

mpesa_schema = MpesaSchema()
mpesas_schema = MpesaSchema(many=True)

bookings_schema = BookingSchema(many=True)

comapny_image_schema = ImageCompanySchema()
comapny_image_schemas = ImageCompanySchema(many=True)

user_schema = UserSchema()
users_schema = UserSchema(many=True)

videos_schema = VideoSchema(many=True)

phrase_schema = PhraseSchema()
reset_option_schema = ResetOptionSchema()


def get_part_of_day(hour):
    return (
        "morning" if 5 <= hour <= 11
        else
        "afternoon" if 12 <= hour <= 17
        else
        "evening"
    )


from datetime import datetime

time = int(datetime.now().strftime("%H"))




def app_is_activated():
    lookup = Branch.query.first()
    return lookup


@app.route("/seed/vids", methods=["POST"])
def seed_videos():
    terms = request.json["term"]
    data = get_youtube_links(terms)
    return jsonify(data)


@app.route("/")
@app.route("/dashboard")
@login_required
def home():
    # date
    date = datetime.now().strftime("%A, %d %B %Y")
    # report form
    bookings = len(Booking.query.all())
    tellers = len(Teller.query.all())
    service_offered = len(ServiceOffered.query.all())
    videos = len(videos_schema.dump(Video.query.all()))
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        server_address = (s.getsockname()[0])
        s.close()
    except Exception:
        server_address = "127.0.0.1"

    types = {"links": 0, "files": 0}
    if videos:
        videos_ = Video.query.all()
        for video in videos_:
            if video.type == 1:
                types["files"] = types["files"] + 1
            else:
                types["links"] = types["links"] + 1

    links = f"{types['links']} {'Link' if types['links'] == 1 else 'Links'}" if types['links'] else "No Link"
    files = f"{types['files']} {'File' if types['files'] == 1 else 'Files'}" if types['files'] else "No File"

    dash_data = {
        "bookings": f"{bookings} {'booking' if bookings == 1 else 'Bookings'}" if bookings else "No Bookings",
        "tellers": f"{tellers} {'Teller' if tellers <= 1 else 'Tellers'}" if tellers else "No Tellers",
        "services": f"{service_offered} {'Service' if service_offered <= 1 else 'Services'}" if service_offered else
        "No Services",
        "statement": get_part_of_day(time).capitalize(),
        "user": (current_user.username).capitalize(),
        "video": f"{videos} {'Video' if videos <= 1 else 'Videos — ' + links + ' • ' + files}" if videos else "No Videos",
        "server_address": server_address,
        "todays_bookings": todays_bookings()
    }
    branch = Branch.query.first()
    return render_template("dashboard.html", today=date, dash_data=dash_data, branch=branch,
                           server_address=server_address)


@app.route("/doughnut/data", methods=["GET"])
def _doughnut_data():
    open_lookup = Booking.query.filter_by(serviced=False).all()
    open_data = bookings_schema.dump(open_lookup)
    closed_lookup = Booking.query.filter_by(serviced=True).all()
    closed_data = bookings_schema.dump(closed_lookup)

    return jsonify({"open": len(open_data), "closed": len(closed_data)})



@app.route("/bar/data", methods=["GET"])
def last_fifteen_data():
    data = get_issue_count()
    return jsonify(data["result"])


file_name = str()
dir = str()


@app.route("/video/link", methods=["POST"])
def upload_link_():
    link_ = request.json["link"]
    type_ = request.json["type"]
    msg = upload_link(link_, type_)
    local.emit("update_vids", {})
    return msg


@app.route("/dashboard/reports", methods=["POST"])
def daily():
    secrets.token_hex()
    duration = request.json["duration"]  # daily monthly
    kind = request.json["kind"]  # booking / branch
    date = request.json["date"]  # date
    # getting the current path

    # FILE BASED REPORTS
    # import os
    # global file_name,dir
    #
    # # file_name = f"{int(datetime.timestamp(datetime.now()))}_report..xlsx"
    # file_name = "report.xlsx"
    # dir = os.path.join(os.getcwd(),"fuprox","reports")
    # root_file = os.path.join(dir,file_name)
    # # TEST
    # headers = ("firstname","lastname")
    # data = [("Denis", "Wambui"), ("Mark", "Kiruku")]
    # data_ = tablib.Dataset(*data, headers=headers)
    # with open(root_file, 'wb') as f:
    #     f.write(data_.export('xlsx'))
    # # send_file(file)

    booking_data = list()
    if duration and kind and date:
        kind_ = 1001 if kind == 0 else 2001
        duration_ = 1001 if duration == 'day' else 2001
        if duration_ == 1001:
            # daily
            date = "%{}%".format(date)
            lookup = Booking.query.filter(Booking.date_added.like(date)).all()
            booking_data = bookings_schema.dump(lookup)
        else:
            # monthly
            date_ = date.split("-")
            date = f"{date_[0]}-{date_[1]}"
            date = "%{}%".format(date)
            lookup = Booking.query.filter(Booking.date_added.like(date)).all()
            booking_data = bookings_schema.dump(lookup)
    return jsonify(booking_data)


'''mpesa report '''


@app.route("/mpesa/reports", methods=["POST"])
def mpesa_reports():
    kind = request.json["kind"]
    if int(kind) == 1:
        lookup = Mpesa.query.filter(Mpesa.amount.contains(5.0)).all()
    elif int(kind) == 2:
        lookup = Mpesa.query.filter(Mpesa.amount.contains(10.0)).all()
    elif int(kind) == 3:
        lookup = Mpesa.query.all()
    return jsonify(mpesas_schema.dump(lookup))


"""
function to get issue count >>>>
"""


def get_issue_count():
    data = db.session.execute("SELECT COUNT(*) AS issuesCount, DATE (date_added) AS issueDate FROM booking GROUP BY "
                              "issueDate LIMIT 15")
    return {'result': [dict(row) for row in data]}


"""
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::working with all forms of payments linking to the database::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
"""


@app.route("/bookings")
@login_required
def payments():
    bookings_ = Booking.query.order_by(Booking.date_added.desc()).all()
    bookings = list()
    for booking in bookings_:
        service = ServiceOffered.query.filter_by(unique_id=booking.service_name).first()
        booking.start = service.code
        booking.date_term = timeago.format(booking.date_added, datetime.now())
        bookings.append(booking)
    return render_template("payment.html", bookings=bookings)


@app.route("/bookings/all", methods=["POST"])
def all_bookings():
    bookings_ = Booking.query.order_by(Booking.date_added.desc()).all()
    bookings__ = bookings_schema.dump(bookings_)
    bookings = list()
    for booking in bookings__:
        service = ServiceOffered.query.filter_by(unique_id=booking["service_name"]).first()
        booking["start"] = service.code
        for booking in bookings:
            booking["start"] = service.code
            for lookup in bookings_:
                if booking["unique_id"] == lookup.unique_id:
                    booking["date_term"] = timeago.format(lookup.date_added, datetime.now())
        bookings.append(booking)
    return jsonify(bookings)


@app.route("/booking/search", methods=["POST"])
def search__():
    term = request.json["term"]
    lst = re.findall(r'\d+', term)
    ss = list(term)
    try:
        ints = [x for x in lst[0]]
    except IndexError:
        ints = []

    final = [x for x in ss if x not in ints]
    real_code = "".join(final)
    numbers = "".join(lst)
    code = f"SELECT * FROM service_offered WHERE code LIKE '{real_code}%'"
    name = f"SELECT * FROM service_offered WHERE name LIKE '{term}%'"
    code_ = [dict(x) for x in db.session.execute(code)]
    name_ = [dict(x) for x in db.session.execute(name)]
    service_one = code_ if code_ else name_

    final = list()
    if service_one:
        service = service_one[0]
        code = service['code']
        name = service['name']
        serv_unique_id = service["unique_id"]
        bnk_number = is_ticket(term)
        if ints:
            query_offline = f"SELECT * FROM booking WHERE service_name='{serv_unique_id}' and ticket={numbers} ORDER BY date_added DESC"
            query_online = f"SELECT * FROM booking WHERE service_name='{serv_unique_id}' and kind={numbers} ORDER BY date_added DESC"
            online = [dict(zip(x.keys(), x)) for x in db.session.execute(query_online)]
            offline = [dict(zip(x.keys(), x)) for x in db.session.execute(query_offline)]
            q_final = online if online else offline
            for booking in q_final:
                booking["start"] = service['code']
                booking["date_term"] = timeago.format(booking["date_added"], datetime.now())
                final.append(booking)
        else:
            # log(f"Denis ... {bnk_number}")
            query_offline = f"SELECT * FROM booking WHERE service_name='{serv_unique_id}' ORDER BY date_added DESC"
            offline = [dict(zip(x.keys(), x)) for x in db.session.execute(query_offline)]
            for booking in offline:
                booking["start"] = service['code']
                booking["date_term"] = timeago.format(booking["date_added"], datetime.now())
                final.append(booking)
    return jsonify(final)


@app.route("/booking/search/filters", methods=["POST"])
def filters():
    pass


def is_ticket(term):
    log(f"in function {term}")
    lst = re.findall(r'\d+', term)
    final = "".join(lst)
    return final


def get_service(name):
    return ServiceOffered.query.filter_by(name=name).first()


@app.route("/booking/search/name", methods=["POST"])
def search_by_service_name():
    service_name = request.json["service"]
    data = get_service(service_name)
    bookings = list()
    if data:
        bookings = Booking.query.filter_by(service_name=data.name).all()

    return jsonify(bookings_schema.dump(bookings))


@app.route("/bookings/search/service/date", methods=["POST"])
def search_by_service_name_date():
    service_name = request.json["service"]
    dates = request.json["dates"]
    data = get_service(service_name)
    bookings = list()
    if data:
        bookings = get_bookings_by_date(data.name, dates)
    return bookings


def parse_date(date):
    try:
        final = parser.parse(date)
    except Exception:
        final = None
    return final


def get_bookings_by_date(service_name, date):
    dates = date.split("$$")
    if len(dates) > 1:
        # date ranges
        start = parse_date(dates[0])
        end = parse_date(dates[1])
        bookings = Booking.query.filter_by(service_name=service_name).filter(Booking.date_added > start).filter(
            Booking.date_added < end).all()
    else:
        # single date
        start = parse_date(dates[0])
        end = start + timedelta(hours=24)
        bookings = Booking.query.filter_by(service_name=service_name).filter(Booking.date_added > start).filter(
            Booking.date_added < end).all()
    return bookings


@app.route("/bookings/details/<int:id>")
@login_required
def booking_info(id):
    try:
        booking = Booking.query.get(id)
        booking.is_instant_ = "Instant" if booking.is_instant else "Not Instant"
        booking.is_synced_ = "Synced" if booking.is_synced else "Not Synced"
        booking.serviced_ = "Closed" if booking.serviced else "Open"
        booking.forwarded_ = "Forwarded" if booking.forwarded else "Not Forwarded"
        booking.is_emergency_ = "Emergency" if booking.is_emergency else "Not Emergency"
        history = TellerBooking.query.filter_by(booking_id=id).order_by(TellerBooking.date_added.asc()).all()

        statements = list()
        service = ServiceOffered.query.filter_by(unique_id=booking.service_name).first()
        icon = Icon.query.get(service.icon)
        booking.service = service
        booking.icon = icon

        for x in history:
            from_ = "Booking" if x.teller_from == 0 else f" From teller {x.teller_from} "
            preq = "with no mandatory teller" if x.pre_req == 0 else f" with mandatory to teller {x.pre_req} "
            statements.append(f"{from_} to teller {x.teller_to} on {x.date_added} {preq}")

        booking_time = get_ticket_time(booking.id)
    except AttributeError:
        abort(404)
    return render_template("payment_card.html", booking=booking, statements=statements, metrics=booking_time)


@app.route("/reverse", methods=["POST"])
def reverse_():
    """ PARAMS
    'Initiator' => 'testapi',
    'SecurityCredential' => 'eOvenyT2edoSzs5ATD0qQzLj/vVEIAZAIvIH8IdXWoab0NTP0b8xpqs64abjJmM8+cjtTOfcEsKfXUYTmsCKp5X3iToMc5xTMQv3qvM7nxtC/SXVk+aDyNEh3NJmy+Bymyr5ISzlGBV7lgC0JbYW1TWFoz9PIkdS4aQjyXnKA2ui46hzI3fevU4HYfvCCus/9Lhz4p3wiQtKJFjHW8rIRZGUeKSBFwUkILLNsn1HXTLq7cgdb28pQ4iu0EpVAWxH5m3URfEh4m8+gv1s6rP5B1RXn28U3ra59cvJgbqHZ7mFW1GRyNLHUlN/5r+Zco5ux6yAyzBk+dPjUjrbF187tg==',
    'CommandID' => 'TransactionReversal',
    'TransactionID' => 'NGE51H9MBP',
    'Amount' => '800',
    'ReceiverParty' => '600211',
    'RecieverIdentifierType' => '11',
    'ResultURL' => 'http://7ee727a4.ngrok.io/reversal/response.php',
    'QueueTimeOutURL' => 'http://7ee727a4.ngrok.io/reversal/response.php',
    'Remarks' => 'ACT_001',
    'Occasion' => 'Reverse_Cash'
    """
    id = request.json["id"]
    data = get_transaction(id)
    transaction_id = data["receipt_number"]
    amount = data["amount"]
    receiver_party = data["phone_number"]
    return reverse(transaction_id, amount, receiver_party)


def get_transaction(id):
    lookup = Mpesa.query.get(id)
    return mpesa_schema.dump(lookup)


@app.route('/service/icon/upload', methods=['POST'])
def upload_file():
    # print(request.data)
    return upload()


@app.route('/service/icon', methods=['POST'])
def upload_file_():
    icon = request.json["icon"]
    name = request.json["name"]
    # branch_id = request.json["branch_id"]
    branch_id = Branch.query.first().id
    current = save_icon_to_service(icon, name, branch_id)
    return current


@app.route("/card")
@login_required
def payments_card():
    # get date from the database 
    lookup = Mpesa.query.all()
    data = mpesas_schema.dump(lookup)
    # work on the payments templates
    return render_template("payment_card.html", transactions=data)


@app.route("/wallpaper", methods=["GET", "POST"])
@login_required
def wallpaper__():
    form = WallpaperForm()
    if form.validate_on_submit():
        if form.picture.data:
            image = form.picture.data
            save_picture(image, "wallpaper")
    return render_template("wallpaper.html", form=form)


@app.route("/logo", methods=["GET", "POST"])
@login_required
def logo__():
    logo = LogoForm()
    try:
        if logo.validate_on_submit():
            logo_ = logo.logo.data
            save_picture(logo_, "company_logo")
    except Exception:
        pass
    return render_template("logo.html", logo=logo)


@app.route("/delete/wallpaper", methods=["POST"])
def delete_wallpaper():
    try:
        jpg = f"{image_path}wallpaper.png"
        png = f"{image_path}wallpaper.jpg"
        os.remove(jpg) if os.remove(png) else os.remove(jpg)
        db.session.execute("DELETE FROM wallpaper")
        flash("Wallpaper Successfully removed", "success")
        final = True
    except  FileNotFoundError:
        flash("Wallpaper does not exist.", "warning")
        final = False
    return jsonify({'msg': final})


@app.route("/reports")
@login_required
def payments_report():
    # work on the payments templates
    return render_template("payments_reports.html")


@app.route("/404")
def review_404():
    # work on the payments templates
    return render_template("payments_reports.html")


@app.errorhandler(500)
def interanal_error(e):
    return render_template('500.html'), 404


@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404


@app.route("/tellers", methods=["POST", "GET"])
@login_required
def tellers():
    # get data from the database
    tellers_ = Teller.query.all()
    teller_final = list()
    for teller in tellers_:
        t = teller_schema.dump(teller)
        # strftime(f"%d.%m.%y %H:%M")
        date = parse_date(t["date_added"])
        t["date_added"] = date.strftime(f"%d.%m.%y %H:%M")
        users = User.query.filter_by(teller=t["number"]).all()
        final = ""
        for index, user in enumerate(users):
            if len(users) > 1:
                final += f"{user.username}, "
            else:
                final += f"{user.username}"
        t["branch_unique_id"] = final if users else "-"
        teller_final.append(t)
    # init the form
    teller = TellerForm()
    services = ServiceOffered.query.all()
    users = User.query.all()
    if teller.validate_on_submit():
        # get specific company data
        if not teller_exists(teller.number.data):
            key_ = secrets.token_hex();
            teller_number = teller.number.data
            branch_id = Branch.query.first().id
            service_name = teller.service.data
            user = teller.users.data
            final_user = 0 if user == "None" else user
            try:
                branch = branch_exists_id(branch_id)
                final = add_teller(teller_number, branch_id, service_name, branch.unique_id, final_user)
                sio.emit("add_teller", {"teller_data": final})
                local.emit("update_services", final)
            except Exception:
                print("error! teller exists")
            return redirect(url_for("tellers"))
        else:
            flash("Teller Already exists.", "danger")
    return render_template("add_branch.html", form=teller, services=services, tellers=teller_final, users=users)


@app.route("/tellers/view", methods=["POST", "GET"])
@login_required
def tellers_view():
    # get data from the database
    tellers_ = Teller.query.all()
    teller_final = list()
    for teller in tellers_:
        t = teller_schema.dump(teller)
        # strftime(f"%d.%m.%y %H:%M")
        date = parse_date(t["date_added"])
        t["date_added"] = date.strftime(f"%d.%m.%y %H:%M")
        users = User.query.filter_by(teller=t["number"]).all()
        final = ""
        for index, user in enumerate(users):
            if len(users) > 1:
                final += f"{user.username}, "
            else:
                final += f"{user.username}"
        t["branch_unique_id"] = final if users else "-"
        teller_final.append(t)
    # init the form
    teller = TellerForm()
    services = ServiceOffered.query.all()
    users = User.query.all()
    return render_template("view_branch.html", form=teller, services=services, tellers=teller_final, users=users)



def branch_exists_id(id):
    return Branch.query.get(id)


def teller_exists(teller_number):
    lookup = Teller.query.filter_by(number=teller_number).first()
    teller_data = teller_schema.dump(lookup)
    return teller_data


""" not recommemded __check if current branch is in db"""


def log(msg):
    print(f"{datetime.now().strftime('%d:%m:%Y %H:%M:%S')} — {msg}")
    return True


def branch_exits(name):
    lookup = Branch.query.filter_by(name=name).first()
    branch_data = branch_schema.dump(lookup)
    return branch_data


# mpesa more info
@app.route("/info/<string:key>")
def more_info(key):
    print("key", key)
    lookup = Mpesa.query.get(key)
    data = mpesa_schema.dump(lookup)
    return render_template("info.html", data=data)


@app.route("/video/upload", methods=["POST"])
def upload_video_():
    data = upload_video()
    local.emit("update_vids", {})
    return data


# @app.route("/video/link", methods=["POST"])
# def upload_link_():
#     link_ = request.json["link"]
#     type_ = request.json["type"]
#     return upload_link(link_, type_)
#

# get single video
@app.route("/video/get/one", methods=["POST"])
def get_one_video_():
    id = request.json["id"]
    return get_single_video(id)


@app.route("/video/active", methods=["POST"])
def get_active():
    return get_active_videos()


@app.route("/video/get/all", methods=["POST"])
def get_all_videos_():
    return get_all_videos()


@app.route("/video/toggle", methods=["POST"])
def activate_video():
    id = request.json["id"]
    local.emit("update_vids", {})
    return toggle_status(id)


@app.route("/video/delete", methods=["POST"])
def video_delete():
    vid_id = request.json["id"]
    data = delete_video(vid_id)
    local.emit("update_vids", {})
    return jsonify(data)


@app.route("/upload", methods=["POST", "GET", "PUT"])
def upload_video__():
    return render_template("upload.html")


@app.route("/icons", methods=["POST", "GET", "PUT"])
def upload_icon():
    icons = Icon.query.all()
    return render_template("icon.html", icons=icons)


# view_branch
@app.route("/teller/view")
@login_required
def view_branch():
    # get data from the database
    branches_data = Branch.query.all()
    company = ServiceForm()
    return render_template("view_branch.html", form=company, data=branches_data)


@app.route("/branches/category")
@app.route("/branches/category/add", methods=["POST", "GET"])
@login_required
def add_category():
    company = ServiceForm()
    # checking the mentioned  comapany exists
    if company.validate_on_submit():
        final = bool()
        # medical
        if company.is_medical.data == "True":
            final = True
        else:
            final = False
        try:
            data = Service(company.name.data, company.service.data, final)
            db.session.add(data)
            db.session.commit()
        except sqlalchemy.exc.IntegrityError:
            flash(f"Category By That Name Exists", "warning")
        # adding a category
        sio.emit("category", service_schema.dump(data))
        company.name.data = ""
        company.service.data = ""
        db.session.close()
        flash(f"Service Successfully Added", "success")
    else:
        flash("Error! Make Sure all data is correct", "error")
    return render_template("add_category.html", form=company)


def move_to_api(filename):
    from pathlib import Path
    import shutil
    home = str(Path.home())
    from_ = os.path.join(app.root_path, "static/images/icons", filename)
    upload_path = os.path.join(home, "fuprox_api", "fuprox", "static/images/icons", filename)
    upload_pth = os.path.join(home, "fuprox_api", "fuprox", "static/images/icons")
    if not os.path.exists(f"{home}/fuprox_api/fuprox/icons"):
        try:
            new_dir = Path(upload_path)
            new_dir.mkdir(parents=True)
            shutil.move(from_, upload_pth)
            logging.info("Success! creating a directory.")
            return "Direcroty Created Successfully."
        except OSError:
            logging.info("Error! creating a directory.")
            return "Error! creating a directory."
    else:
        shutil.move(from_, upload_path)


def ticket_unique() -> int:
    return secrets.token_hex(16)


def save_picture(picture, filename):
    try:
        pic_name = filename
        # getting the name and the extension of the image
        _, ext = os.path.splitext(picture.filename)
        final_name = pic_name + ext

        picture_path = os.path.join(app.root_path, "static/images/", final_name)
        i = Image.open(picture)
        i.save(picture_path)
        blur_image(picture_path)
        wallie_to_db(picture_path)
    except Exception:
        final_name = "None"
    return final_name


def wallie_to_db(path):
    # final = bytes(path, encoding='utf8')
    lookup = Wallpaper(path)
    db.session.add(lookup)
    db.session.commit()
    return dict()


@app.route("/service", methods=["POST", "GET"])
@login_required
def add_company():
    service_data = Service.query.all()
    # init the form
    service = ServiceForm()
    tellers = Teller.query.all()
    icons = Icon.query.all()
    branch = Branch.query.first()
    if request.method == "POST":
        if service.validate_on_submit():
            code = service.code.data
            if len(code) == 1:
                name = service.name.data
                teller = service.teller.data
                branch_id = branch.id
                code = service.code.data
                icon = service.icon.data
                visible = True if service.visible.data == "True" else False
                active = True if service.active.data == "True" else False
                is_special = True if service.is_special.data == "True" else False
                # service emit service made
                final = create_service(name, teller, branch_id, code, icon, visible, active, is_special)
                if final:
                    try:
                        key = final["key"]
                        flash("Service Added Successfully", "success")
                        sio.emit("sync_service", final)
                        local.emit("update_services", final)
                        if final["is_special"]:
                            return redirect(url_for("add_schedule", unique_id=final["unique_id"]))
                        else:
                            return redirect(url_for("add_company"))
                    except KeyError:
                        flash(final['msg'], "danger")
            else:
                flash("Service code may not contain a single characters.", "warning")
        else:
            flash("Make sure all data is correct", "error")
    return render_template("add_company.html", form=service, companies=service_data, tellers=tellers, icons=icons)


@app.route("/service/view", methods=["POST", "GET"])
@login_required
def view_company_list():
    services_offered = ServiceOffered.query.all()
    return render_template("view_company.html", services_offered=services_offered)


@app.route("/service/schedule/<string:unique_id>", methods=["POST", "GET"])
@login_required
def add_schedule(unique_id):
    service = service_by_unique(unique_id)
    if service:
        schedule = service_schedule(unique_id)
        days_ = days()
        user_ = users()
        return render_template("add_schedule.html", service=service, schedules=schedule, days=days_, users=user_)
    else:
        return redirect(url_for("add_company"))



@app.route("/service/schedule/edit/<string:unique_id>", methods=["POST", "GET"])
@login_required
def edit_schedule(unique_id):
    locus = service_by_schedule(unique_id)
    schedule = get_schedule(unique_id)
    service = service_by_unique(locus["service"])
    days_ = days()
    user_ = users()
    return render_template("edit_schedule.html", service=service, schedule=schedule, days=days_, users=user_)


@app.route("/service/schedule/delete/<string:unique_id>", methods=["POST", "GET"])
@login_required
def delete_schedule_(unique_id):
    locus = service_by_schedule(unique_id)
    if locus:
        schedule = service_schedule(locus["service"])
        service = service_by_unique(locus["service"])
        days_ = days()
        user_ = users()
        schedule = delete_schedule(unique_id)
        if schedule:
            sio.emit("delete_schedule",schedule)
            flash("Schedule deleted successfully", "info")
        else:
            flash("Schedule cannot be deleted. It has bookings made.","warning")
        return redirect(url_for("add_schedule", unique_id=locus["service"]))
    else:
        return redirect(url_for("add_schedule",unique_id=locus["service"]))


@app.route("/add/service/schedule", methods=['POST'])
def add_service_schedule():
    start = request.json["start"]
    end = request.json["end"]
    specialist = request.json["specialist"]
    service = request.json["service"]
    limit = request.json["limit"]
    day = request.json["day"]
    latest_booking_time = request.json["latest_booking_time"]
    if start and end and specialist and day :
        checker = schedule_overlap(specialist,start, end, service, day)
        overlap = checker["status"] == 500
        if not overlap:
            final = add_schedule_db(start, end, specialist, day, service,limit,latest_booking_time)
            sio.emit("add_schedule",final["msg"])
        else:
            schedule_overlapped = checker["msg"]
            unique = schedule_overlapped.unique_id[-10:]
            start = schedule_overlapped.start
            end = schedule_overlapped.end
            final = {
                "msg": f"Schedule Overlap with {unique} which starts {start} and ends {end}",
                "status": 500
            }
    else:
        final = {
            "msg": "Requirements not met",
            "status": 500
        }
    return jsonify(final)


@app.route("/edit/service/schedule", methods=['POST'])
def edit_service_schedule():
    schedule = request.json["schedule"]
    start = request.json["start"]
    end = request.json["end"]
    specialist = request.json["specialist"]
    service = request.json["service"]
    day = request.json["day"]
    limit = request.json["limit"]
    lastest_booking_time = request.json["lastest_booking_time"]

    if start and end and specialist and day:
        checker = schedule_overlap(specialist,start, end, service, day)
        overlap = checker["status"] == 500
        if not overlap:
            final = edit_schedule_db(schedule,start, end, specialist, day, service,limit,lastest_booking_time)
            sio.emit("add_schedule",final["msg"])
        else:
            schedule_overlapped = checker["msg"]
            unique = schedule_overlapped.unique_id[-10:]
            start = schedule_overlapped.start
            end = schedule_overlapped.end
            final = {
                "msg": f"Schedule Overlap with {unique} which starts {start} and ends {end}",
                "status": 500
            }
    else:
        final = {
            "msg": "Requirements not met",
            "status": 500
        }
    return jsonify(final)

@app.route("/services/view")
@login_required
def view_company():
    # get the branch data
    company_data = Company.query.all()
    # init the form
    branch = TellerForm()
    return render_template("view_company.html", form=branch, data=company_data)


@app.route("/branches/category/view")
@login_required
def view_category():
    # category data
    service_data = Service.query.all()
    # init the form
    branch = TellerForm()
    return render_template("view_category.html", form=branch, data=service_data)


@app.route("/help", methods=["GET", "POST"])
def help():
    solution_data = Help.query.all()
    return render_template("help.html", data=solution_data)


@app.route("/get/wallpaper", methods=["POST"])
def get_wallpaper():
    wallie = Wallpaper.query.order_by(Wallpaper.date_added.desc()).first()
    return wallpaper_schema.dump(wallie)


@app.route("/get/logo", methods=["POST"])
def get_logo():
    logo = Logo.query.order_by(Logo.date_added.desc()).first()
    return logo_schema.dump(logo)


@app.route("/extras", methods=["GET", "POST"])
@login_required
def extras():
    current = Branch.query.first()
    form = ActivateForm()
    phrase = Phrase.query.first()
    default = "Proceed to room number"
    phrase = (phrase.phrase if phrase.phrase else default) if phrase else default
    current_phrase = Phrase.query.first()
    if request.method == "POST":
        if form.validate_on_submit() and form.submit.data:
            key = form.key.data
            if len(key) > 20:
                try:
                    # get key_segment from the other part from the identity module
                    data = requests.post(f"http://localhost:7676/activate", json={"key": key})
                    if (data.ok):
                        final_data = data.json()
                        if final_data:
                            if final_data["code"] == 200:
                                data_response = final_data["response"]
                                data = activate_branch(data_response)
                                user = User(username=register.username.data,
                                            email=data_response["branch"]["description"],
                                            password=hashed_password, branch_unique=branch_unique)
                                user.is_admin = True
                                user.teller = 1
                                db.session.add(user)
                                db.session.commit()
                                db.session.close()
                                if not data:
                                    flash("Success! Application Activated", "success")
                                    return redirect(url_for("home"))
                                else:
                                    flash(data["msg"], "warning")
                            else:
                                # error
                                print(final_data["code"])
                        else:
                            print("issues with the data, Empty response")

                    else:
                        flash("Error! Please confirm the key", "warning")
                        return redirect(url_for("extras"))
                except requests.exceptions.ConnectionError:
                    flash("Error! Activatation Server Not Reachable", "danger")
            else:
                flash("Error! Key too short", "danger")
    return render_template("extras.html", branch=current, form=form, current_phrase=current_phrase, phrase=phrase)


@app.route("/reset/tickets", methods=["POST"])
def reset_tickets():
    req = request.post("http://159.65.144.235:4000/ticket/reset")


@app.route("/phrase", methods=["POST"])
def phrase_():
    phrase = request.json["phrase"]
    option = request.json["options"]
    db.session.execute("DELETE FROM phrase")
    is_teller = True if int(option) == 1 else False
    lookup = Phrase(phrase, is_teller)
    db.session.add(lookup)
    db.session.commit()
    flash("Phrase Successfully Set", "success")
    return jsonify(phrase_schema.dump(lookup))


@app.route('/get/reset/details')
def reset_request():
    branch = Branch.query.first()
    if branch:
        lookup = ResetOption.query.first()
        final = reset_option_schema.dump(lookup)
        final["key_"] = branch.key_
    else:
        final = {}
    return jsonify(final)


@app.route("/reset/settings", methods=["POST"])
def reset_settings():
    option = request.json["option"]
    time = request.json["time"]

    db.session.execute("DELETE FROM reset_option")

    lookup = ResetOption(time, option)
    db.session.add(lookup)
    db.session.commit()

    flash("Success, Reset details Updated", "success")
    return jsonify(phrase_schema.dump(lookup))


@app.route("/this/branch", methods=["POST"])
def this_branch():
    return jsonify(branch_schema.dump(Branch.query.first()))


def activate_branch(data):
    if data:
        try:
            if data:
                if data["service"] and data["branch"] and data["company"]:
                    try:
                        branch = data["branch"]
                        service = data["service"]
                        company = data["company"]
                        days = data["days"]
                        clean_db()
                        prepare_db(branch["key_"])
                        add_service(service["name"], service["service"], service["is_medical"])
                        add_company(company["name"], company["service"])
                        add_branch(branch["name"], branch["company"], branch["longitude"], branch["latitude"],
                                   branch["opens"], branch["closes"], branch["service"], branch["description"],
                                   branch["key_"], branch["unique_id"])
                        add_days(days)
                        return False
                    except sqlalchemy.exc.InvalidRequestError as e:
                        log(f"Error! {e}")
                else:
                    return {'msg': "Data incomplete"}, 500
            else:
                return {"msg": "Error! Key not valid. Please confirm the key and retry."}
        except json.decoder.JSONDecodeError:
            return {"msg": "Error! Key not valid. Please confirm the key and retry."}
    else:
        return {"msg": "Error! Key not valid. Please confirm the key and retry."}


def there_are_bookings():
    bookings = Booking.query.all()
    return bookings


def prepare_db(key):
    bookings = there_are_bookings()
    if not bookings:
        try:
            branch = Branch.query.filter_by(key_=key).first()
            if branch:
                company = Company.query.filter_by(name=branch.company).first()
                if company:
                    service = Service.query.filter_by(name=branch.service).first()
                    db.session.delete(branch)
                    db.session.commit()
                    db.session.delete(company)
                    db.session.commit()
                    db.session.delete(service)
                else:
                    log("service issue")
            else:
                log("service issue")
        except sqlalchemy.exc.InvalidRequestError as e:
            log("your DB Need upkeep. it is not empty")
        finally:
            log("errors")
    else:
        log("Error, database is not empty still has some bookings")


def branch_exists(name):
    lookup = Branch.query.filter_by(name=name).first()
    return [1] if lookup else []


def add_branch(name, company, longitude, latitude, opens, closes, service, description, key_, unique_id):
    if branch_exists_():
        db.session.execute("DELETE FROM branch")

    if not branch_exists(name):
        lookup = Branch(name, company, longitude, latitude, opens, closes, service, description, key_, unique_id)
        try:
            db.session.add(lookup)
            db.session.commit()
            return dict()
        except sqlalchemy.exc.IntegrityError as e:
            print("Error! Could not create Branch.")
            return dict()
    else:
        return dict()


def add_company(name, service):
    if company_exists():
        db.session.execute("DELETE FROM company")

    lookup = Company(name, service)
    try:

        db.session.add(lookup)
        db.session.commit()
    except sqlalchemy.exc.IntegrityError:
        print("error! already copied")
    lookup_data = company_schema.dump(lookup)
    return lookup_data

def add_days(days):
    for day in days:
        d = Day(day["day"])
        d.unique_id = day["unique_id"]
        db.session.add(d)
        db.session.commit()
    return days


def service_exists():
    return Service.query.first()


def branch_exists_():
    return Branch.query.first()


def company_exists():
    return Company.query.first()


def clean_db():
    db.session.execute("DELETE FROM video;")
    db.session.execute("DELETE FROM schedule;")
    db.session.execute("DELETE FROM schedule;")
    db.session.execute("DELETE FROM user;")
    # db.session.execute("DELETE FROM department_service;")
    db.session.execute("DELETE FROM booking_held_comments;")
    db.session.execute("DELETE FROM teller_booking;")
    db.session.execute("DELETE FROM booking_times;")
    db.session.execute("DELETE FROM booking;")
    db.session.execute("DELETE FROM service_offered;")
    db.session.execute("DELETE FROM teller;")
    db.session.execute("DELETE FROM icon;")
    db.session.execute("DELETE FROM branch;")
    db.session.execute("DELETE FROM service;")
    db.session.execute("DELETE FROM image_company;")
    db.session.execute("DELETE FROM company;")
    db.session.execute("DELETE FROM company;")
    return True


def add_service(name, service, is_medical):
    lookup = Service(name, service, is_medical)
    try:
        db.session.add(lookup)
        db.session.commit()
    except sqlalchemy.exc.IntegrityError:
        print("error! record exists")
    return service_schema.dump(lookup)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/login", methods=["POST", "GET"])
def login():
    if not app_is_activated():
        return redirect(url_for("activate"))

    if current_user.is_authenticated:
        return redirect(url_for("home"))
    # loading the form
    login = LoginForm()
    # checking the form data status
    if login.validate_on_submit():
        user = User.query.filter_by(email=login.email.data).first()
        if user and bcrypt.check_password_hash(user.password, login.password.data):
            if user.is_admin or user.is_admin == None:
                next_page = request.args.get("next")
                login_user(user)
                return redirect(next_page) if next_page else redirect(url_for('home'))
            else:
                flash("User Not Authorised To Access System", "danger")
        else:
            flash("Login unsuccessful Please Check Email and Password", "danger")
    return render_template("login.html", form=login)


@app.route("/password/code", methods=["POST", "GET"])
def send_password_code():
    code = PasswordCode()
    # checking the form data status
    if code.validate_on_submit():
        email = code.email.data
        user = User.query.filter_by(email=code.email.data).first()
        if user:
            password_code_request(email, "Password Reset Request Code")
            flash("Code sent to email", "success")
            return redirect(url_for('enter_code', email=email))
        else:
            flash("Error! Please confirm data", "danger")
    return render_template("send_password_code.html", form=code)


@app.route("/password/code/<email>", methods=["POST", "GET"])
def enter_code(email):
    code = Code()
    if code.validate_on_submit():
        exists = code_exists(email, code.code.data)
        if exists:
            flash("Valid Code", "success")
            return redirect(url_for('verify_passwords', email=email))
        else:
            flash("Code not valid", "danger")
    return render_template("verify_code.html", form=code)


@app.route("/password/passwords/<email>", methods=["POST", "GET"])
def verify_passwords(email):
    passwords = Passwords()
    # checking the form data status
    if passwords.validate_on_submit():
        user = User.query.filter_by(email=email).first()
        hash = bcrypt.generate_password_hash(passwords.password.data).decode("utf-8")
        user.password = hash
        db.session.commit()
        if user:
            flash("Password changed successfully", "success")
            codes = Recovery.query.filter_by(user=user.id).all()
            for code in codes:
                db.session.delete(code)
                db.session.commit()
            return redirect(url_for('login'))
        else:
            flash("Passwords do not match", "danger")
    return render_template("new_passwords.html", form=passwords)


@app.route("/password/code/app/<email>", methods=["POST", "GET"])
def enter_code_app(email):
    code = Code()
    if code.validate_on_submit():
        exists = code_exists(email, code.code.data)
        if exists:
            flash("Valid Code", "success")
            return redirect(url_for('verify_passwords_app', email=email))
        else:
            flash("Code not valid", "danger")
    return render_template("verify_code.html", form=code)


@app.route("/password/passwords/app/<email>", methods=["POST", "GET"])
def verify_passwords_app(email):
    passwords = Passwords()
    # checking the form data status
    if passwords.validate_on_submit():
        user = User.query.filter_by(email=email).first()
        hash = bcrypt.generate_password_hash(passwords.password.data).decode("utf-8")
        user.password = hash
        db.session.commit()
        if user:
            flash("Password changed successfully", "success")
            codes = Recovery.query.filter_by(user=user.id).all()
            for code in codes:
                db.session.delete(code)
                db.session.commit()
        else:
            flash("Passwords do not match", "danger")
    return render_template("new_passwords.html", form=passwords)


@app.route("/password/passwords/confirm", methods=["POST", "GET"])
def verify_passwords_ap_confirm():
    flash("Password changed successfully", "success")
    return render_template("password_confirm.html", )


@app.route("/activate", methods=["GET", "POST"])
def activate():
    # checking if the current user is logged
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if app_is_activated():
        return redirect(url_for("login"))

    register = RegisterForm()
    if register.validate_on_submit():
        key = register.key.data
        if len(key) > 20:
            try:
                activate_data = requests.post(f"http://localhost:7676/activate", json={"key": key})
                if (activate_data.ok):
                    final_data = activate_data.json()
                    if final_data:
                        if final_data["code"] == 200:
                            data_response = final_data["response"]
                            data = activate_branch(data_response)
                            is_med = data_response["service"]["is_medical"]
                            keyword = "healthcare" if is_med else "banking"
                            requests.post("http://localhost:9000/seed/vids", json={"term": keyword})
                            try:
                                hashed_password = bcrypt.generate_password_hash(register.password.data).decode("utf-8")

                                branch_unique = Branch.query.first().unique_id

                                user = User(username=register.username.data,
                                            email=data_response["branch"]["description"],
                                            password=hashed_password,branch_unique=branch_unique)
                                user.is_admin = True
                                user.teller = 1
                                db.session.add(user)
                                db.session.commit()
                                db.session.close()
                                flash(f"Branch Activated successfully", "success")
                                return redirect(url_for("login"))
                            except sqlalchemy.exc.IntegrityError:
                                flash("User By That Username Exists", "warning")
                                return redirect(url_for("activate"))
                            if not data:
                                flash("Success! Application Activated", "success")
                                return redirect(url_for("home"))
                            else:
                                flash(data["msg"], "warning")
                                return redirect(url_for("login"))
                        else:
                            flash("Credential issue. Try again", "warning")
                            return redirect(url_for("login"))
                    else:
                        flash("Credential issue. Try again", "warning")
                        return redirect(url_for("activate"))
            except requests.exceptions.ConnectionError:
                flash("Error! Activatation Server Not Reachable", "danger")
                return redirect(url_for("activate"))

        else:
            flash("Error! Key too short", "danger")
            return redirect(url_for("activate"))
    return render_template("register.html", form=register)


# new ]
@app.route("/download/book/mac", methods=["GET"])
def book_mac():
    return send_from_directory("uploads/apps", "book_mac.zip", as_attachment=True)


@app.route("/download/book/windows", methods=["GET"])
def book_win():
    return send_from_directory("uploads/apps", "book_windows.zip",
                               as_attachment=True)


@app.route("/download/book/linux", methods=["GET"])
def book_lin():
    return send_from_directory("uploads/apps", "book_linux.zip", as_attachment=True)


@app.route("/download/teller/mac", methods=["GET"])
def teller_mac():
    return send_from_directory("uploads/apps", "teller_mac.zip", as_attachment=True)


@app.route("/download/teller/windows", methods=["GET"])
def teller_win():
    return send_from_directory("uploads/apps", "teller_windows.zip",
                               as_attachment=True)


@app.route("/download/teller/linux", methods=["GET"])
def teller_lin():
    return send_from_directory("uploads/apps", "teller_linux.zip",
                               as_attachment=True)


@app.route("/download/display/mac", methods=["GET"])
def display_mac():
    return send_from_directory("uploads/apps", "display_mac.zip", as_attachment=True)


@app.route("/download/display/windows", methods=["GET"])
def display_win():
    return send_from_directory("uploads/apps", "display_windows.zip", as_attachment=True)


@app.route("/download/display/linux", methods=["GET"])
def display_linux():
    return send_from_directory("uploads/apps", "display_linux.zip", as_attachment=True)


@app.route("/download/app", methods=["GET"])
def mobile_app():
    return send_from_directory("uploads/apps", "fuprox.apk", as_attachment=True)


''' working with users'''


@app.route("/extras/users/add", methods=["GET", "POST"])
@login_required
def add_users():
    # getting user data from the database
    users = User.query.all()
    # return form to add a user
    register = AddUser()
    tellers = Teller.query.all()
    if register.validate_on_submit():
        # hashing the password
        hashed_password = bcrypt.generate_password_hash(register.password.data).decode("utf-8")
        # adding the password to the database
        try:
            teller = register.teller.data
            is_teller = 0 if teller == "None" else teller

            user = User(username=register.username.data, email=register.email.data, password=hashed_password,branch_unique=ticket_unique())
            branch = Branch.query.first()

            user.teller = is_teller
            user.branch_unique = branch.unique_id

            is_specialist = True if register.specialist.data == "True" else False
            user.is_specialist = is_specialist
            db.session.add(user)
            db.session.commit()
            sio.emit("local_user",user_schema.dump(user))

            flash(f"Account Created successfully", "success")
            return redirect(url_for("add_users"))
        except sqlalchemy.exc.IntegrityError:
            flash("User By That Name Exists", "warning")
    return render_template("add_users.html", form=register, users=users, tellers=tellers)


@app.route("/extras/users/edit/promote/<int:id>", methods=["GET", "POST"])
def promote_user_account(id):
    user = User.query.get(id)
    if user:
        flash("User account has been PROMOTED successfully", "success")
        user.is_admin = True
        db.session.commit()
    else:
        flash("User account could not be promoted", "danger")
    return redirect(url_for("edit_user", id=id))


@app.route("/extras/users/edit/demote/<int:id>", methods=["GET", "POST"])
def demote_user_account(id):
    user = User.query.get(id)
    if user:
        flash("User account has been DEMOTED successfully", "success")
        user.is_admin = False
        db.session.commit()
    else:
        flash("User account could not be promoted", "danger")
    return redirect(url_for("edit_user", id=id))


@app.route("/teller/user/remove/<string:username>", methods=["GET", "POST"])
@login_required
def remove_user_from_teller(username):
    user = User.query.filter_by(username=username).first()
    teller = Teller.query.filter_by(number=user.teller).first()
    user.teller = 0
    db.session.commit()
    flash(f"{username} removed from teller", "warning")
    return redirect(url_for("edit_teller", id=teller.id))


@app.route("/extras/users/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_user(id):
    user = User.query.get(id)
    tellers = Teller.query.all()
    if user:
        register = EditUsers()
        if request.method == "POST":
            if register.validate_on_submit():
                hashed_password = bcrypt.generate_password_hash(register.password.data).decode("utf-8")
                # adding the password to the database
                try:
                    teller = register.teller.data
                    is_teller = 0 if teller == "None" else teller
                    is_specialist = True if register.specialist.data == "True" else False
                    user.teller = is_teller
                    user.password = hashed_password
                    user.is_specialist = is_specialist
                    user.email = register.email.data
                    user.username = register.username.data

                    db.session.commit()
                except sqlalchemy.exc.IntegrityError:
                    flash("User By That Name Exists", "warning")
                flash(f"Account Created successfully", "success")
        else:
            register.email.data = user.email
            register.username.data = user.username
    return render_template("edit_users.html", form=register, user=user, tellers=tellers)


@app.route("/extras/users/view")
@login_required
def view_users():
    pass


@app.route("/extras/users/manage")
@login_required
def manage_users():
    pass


# SEARCHING ROUTE
@app.route("/help/solution/<int:id>", methods=["GET", "POST"])
def search_(id):
    # get data from the database based on the data provided
    data = Help.query.get(id)
    # there should be a solution database || FAQ
    return render_template("search.html", data=data)


@app.route("/help/solution/add", methods=["GET", "POST"])
@login_required
def add_solution():
    solution_form = SolutionForm()
    if solution_form.validate_on_submit():
        topic = solution_form.topic.data
        title = solution_form.title.data
        sol = solution_form.solution.data

        solution_data = Help(topic, title, sol)
        db.session.add(solution_data)
        db.session.commit()
        db.session.close()
        flash("Solution Added Successfully", "success")
        # render a html && add the data to the page
    return render_template("add_solution.html", form=solution_form)


# the edit routes
@app.route("/service/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_branch(id):
    # init the form
    service = ServiceForm()
    tellers = Teller.query.all()
    services = ServiceOffered.query.all()
    icons = Icon.query.all()
    services_offered = ServiceOffered.query.all()

    # this teller
    this_service = ServiceOffered.query.get(id)
    # setting form inputs to the data in the database
    service_data = Service.query.all()
    if service.validate_on_submit():
        # update data in the database
        # this_service.name = service.name.data
        this_service.teller = service.teller.data
        this_service.code = service.code.data
        this_service.icon = service.icon.data
        this_service.name = service.name.data
        this_service.medical_active = True if service.visible.data == "True" else False
        this_service.active = True if service.active.data == "True" else False
        this_service.is_special = True if service.is_special.data == "True" else False
        db.session.commit()

        # prefilling the form with the empty fields
        service.name.data = ""
        service.teller.data = ""
        service.code.data = ""
        service.icon.data = ""
        final = service_offered_schema.dump(this_service)
        this_branch = Branch.query.first()
        sio.emit("sync_edit_service", final)
        local.emit("update_services", "")
        flash("Service Successfully Updated", "success")
        return redirect(url_for("add_company"))

    elif request.method == "GET":
        service.name.data = this_service.name
        service.teller.data = this_service.teller
        service.code.data = this_service.code
        service.icon.data = this_service.icon
    else:
        flash("Service Does Not exist. Add Service name first.", "danger")
    return render_template("edit_company.html", form=service, services=services, tellers=tellers, icons=icons,
                           services_offered=services_offered, this_service=this_service)


@app.route("/branch/delete/<int:id>", methods=["GET", "POST"])
@login_required
def delete_branch(id):
    branch_data = Branch.query.get(id)
    # get the branch data
    if request.method == "POST":
        db.session.delete(branch_data)
        db.session.commit()
        db.session.close()
        flash("Branch Deleted Sucessfully", "success")
    elif request.method == "GET":
        # init the form
        branch = TellerForm()
    db.session.delete(branch_data)
    db.session.commit()
    db.session.close()
    flash("Branch Deleted Sucessfully", "success")
    # init the form
    branch = TellerForm()
    return render_template("delete_branch.html", form=branch, data=branch_data)


@app.route("/teller/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_teller(id):
    teller = TellerForm()
    teller_data = Teller.query.get(id)
    services = ServiceOffered.query.all()
    users = User.query.all()
    assinged = list()
    not_assigned = list()
    for user in users:
        if user and teller_data:
            if user.teller == teller_data.number:
                assinged.append(user_schema.dump(user))
            else:
                not_assigned.append(user_schema.dump(user))

    if teller.validate_on_submit():
        try:
            teller_data.number = teller.number.data
            teller_data.service = teller.service.data
            db.session.commit()

            user = User.query.filter_by(username=teller.users.data).first()
            user.teller = teller.number.data
            db.session.commit()

            final = teller_schema.dump(teller_data)
            sio.emit("add_teller", {"teller_data": final})
            local.emit("update_services", final)
        except sqlalchemy.exc.IntegrityError:
            flash("Branch By That Name Exists", "warning")

        teller.number.data = ""
        teller.service.data = ""

        flash(f" {teller.users.data} added to the teller ", "success")
        return redirect(url_for("edit_teller", id=id))
    elif request.method == "GET":
        teller.number.data = teller_data.number if teller_data else ""
        teller.service.data = teller_data.service if teller_data else ""
    else:
        flash("Service Does Not exist. Add Service name first.", "danger")
    return render_template("edit_branch.html", form=teller, services_offered=teller_data, services=services,
                           users=not_assigned, assinged=assinged)


@app.route("/password/request/change", methods=["POST"])
def password_code_request_():
    to = request.json["email"]
    subject = request.json["subject"]
    return password_code_request(to, subject)


# @app.route("/seed/days", methods=["POST", 'GET'])
# def seed_days_():
#     return jsonify(seed_days())


# edit company
@app.route("/category/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_category(id):
    this_category = Service.query.get(id)
    # setting form inputs to the data in the database
    # # init the form
    service = ServiceForm()
    if service.validate_on_submit():
        # update data in the database 
        this_category.name = service.name.data
        this_category.service = service.service.data

        # update date to the database
        db.session.commit()
        db.session.close()
        # prefilling the form with the empty fields
        service.name.data = ""
        service.service.data = ""

        flash("Company Successfully Updated", "success")
        return redirect(url_for("view_category"))

    elif request.method == "GET":
        service.name.data = this_category.name
        service.service.data = this_category.service
    else:
        flash("Company Does Not exist. Add company name first.", "danger")
    return render_template("edit_category.html", form=service)


@sio.event
def connect():
    log('online connection established')


@sio.event
def disconnect():
    log('online disconnected from server')


@local.event
def connect():
    log('offline connection established')


@local.event
def disconnect():
    print('offline disconnected from server')


try:
    sio.connect(socket_link)
except socketio.exceptions.ConnectionError as a:
    log(f"[online] -> {a}")

try:
    local.connect(local_socket)
except socketio.exceptions.ConnectionError as a:
    log(f"[offline] -> {a}")
