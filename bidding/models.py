from datetime import datetime
from flask_login import UserMixin
import secrets
from fuprox import db, ma, login_manager
from dateutil import parser
import random
from flask import request,redirect,url_for

def ticket_unique() -> int:
    return secrets.token_hex(16)


def week_number():
    return datetime.now().strftime("%V")


def final_schedule_number():
    return f"{ticket_unique()}.{week_number()}"


def default_preq_date():
    return parser.parse("01/01/1970")


@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception:
        return redirect(url_for(request.url_rule.endpoint))


def verify_token():
    return int(str(random.getrandbits(32))[:6])


def midnight():
    return parser.parse("00:00")


# we are going to create the model from a user class
# the user mixen adds certain fields that are required matain the use session
# it will add certain fileds to the user class tha are essential to the user login


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(12), unique=True, nullable=False)
    email = db.Column(db.String(48), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default="default.jpg")
    password = db.Column(db.String(60), nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.now)
    is_admin = db.Column(db.Boolean, default=False)
    teller = db.Column(db.Integer, default=0)
    is_specialist = db.Column(db.Boolean, default=False)
    unique_id = db.Column(db.String(250), default=ticket_unique, unique=True)
    branch_unique = db.Column(db.ForeignKey("branch.unique_id"), nullable=False)

    def __repr__(self):
        return f"(' {self.id} ',' {self.username} ', '{self.email}', '{self.image_file}',{self.date_added} )"

    def __init__(self, username, email, password, branch_unique):
        self.username = username
        self.email = email
        self.password = password
        self.branch_unique = branch_unique


class UserSchema(ma.Schema):
    class Meta:
        fields = ("id", "username", "email", "image_file", "is_admin", "teller", "password", "unique_id",
                  "is_specialist", "date_added", "branch_unique")


# creating a company class


class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(length=50), unique=True)
    service = db.Column(db.String(length=250))

    def __init__(self, name, service):
        self.name = name
        self.service = service

    def __repr__(self):
        return f"Company {self.name} -> {self.service}"


class CompanySchema(ma.Schema):
    class Meta:
        fields = ("id", "name", "service")


# creating a branch class

# creating a branch class
class Branch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(length=250), unique=True)
    company = db.Column(db.String(length=100), db.ForeignKey("company.name"), nullable=False)
    longitude = db.Column(db.String(length=50))
    latitude = db.Column(db.String(length=50))
    opens = db.Column(db.String(length=50))
    closes = db.Column(db.String(length=50))
    service = db.Column(db.String(length=100), db.ForeignKey("service.name"))
    description = db.Column(db.String(length=50))
    key_ = db.Column(db.Text)
    valid_till = db.Column(db.DateTime)
    is_synced = db.Column(db.Boolean, default=False)
    unique_id = db.Column(db.String(255), nullable=False, unique=True)

    def __init__(self, name, company, longitude, latitude, opens, closes, service, description, key_, unique_id):
        self.name = name
        self.company = company
        self.longitude = longitude
        self.latitude = latitude
        self.opens = opens
        self.closes = closes
        self.service = service
        self.description = description
        self.key_ = key_
        self.unique_id = unique_id


# creating branch Schema
class BranchSchema(ma.Schema):
    class Meta:
        fields = (
            'id', 'name', 'company', 'address', 'longitude', 'latitude', 'opens', 'closes', 'service', 'description',
            "key_", "valid_till", "is_synced", "unique_id")


# creating a user class
# creating a company class
class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(length=50), unique=True)
    service = db.Column(db.String(length=250))
    is_medical = db.Column(db.Boolean, default=False)

    def __init__(self, name, service, is_medical):
        self.name = name
        self.service = service
        self.is_medical = is_medical


class ServiceSchema(ma.Schema):
    class Meta:
        fields = ("id", "name", "service", "is_medical")


class Help(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(length=100), nullable=False, unique=True)
    title = db.Column(db.String(length=250), nullable=False)
    solution = db.Column(db.Text, nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.now, nullable=False)

    def __init__(self, topic, title, solution):
        self.topic = topic
        self.title = title
        self.solution = solution


class Mpesa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=True)
    receipt_number = db.Column(db.String(255), nullable=True)
    transaction_date = db.Column(db.String(255), nullable=True)
    phone_number = db.Column(db.String(255), nullable=True)
    checkout_request_id = db.Column(db.String(255), nullable=True)
    merchant_request_id = db.Column(db.String(255), nullable=True)
    result_code = db.Column(db.Integer, nullable=False)
    result_desc = db.Column(db.Text, nullable=True)
    date_added = db.Column(db.DateTime(), default=datetime.now)
    local_transactional_key = db.Column(db.String(255), nullable=False)
    booking_id = db.Column(db.Integer, nullable=True, default=0)
    token = db.Column(db.String(length=255))

    def __init__(self, MerchantRequestID, CheckoutRequestID, ResultCode, ResultDesc):
        self.merchant_request_id = MerchantRequestID
        self.checkout_request_id = CheckoutRequestID
        self.result_code = ResultCode
        self.result_desc = ResultDesc


class MpesaSchema(ma.Schema):
    class Meta:
        fields = ("id", "amount", "receipt_number", "transaction_data", "phone_number", "checkout_request_id",
                  "merchant_request_id", "result_code", "result_desc", "date_added", "local_transactional_key",
                  "booking_id", "token")


# creating a booking ID
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_name = db.Column(db.ForeignKey("service_offered.unique_id"), nullable=True)
    start = db.Column(db.String(length=200))
    branch_id = db.Column(db.ForeignKey("branch.id"), nullable=False)
    ticket = db.Column(db.String(length=6), nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.now, unique=False)
    active = db.Column(db.Boolean, default=False, nullable=False)
    nxt = db.Column(db.Integer, nullable=False, default=1001)
    serviced = db.Column(db.Boolean, nullable=False, default=False)
    teller = db.Column(db.String(250), default=0, nullable=False)
    kind = db.Column(db.Integer, nullable=False)
    user = db.Column(db.Integer, default=0, nullable=False)
    is_instant = db.Column(db.Boolean, default=False)
    forwarded = db.Column(db.Boolean, default=False)
    is_synced = db.Column(db.Boolean, default=False)
    unique_id = db.Column(db.String(250), default=ticket_unique, unique=True)
    unique_teller = db.Column(db.String(250), default=000)
    verify = db.Column(db.Integer, default=verify_token)
    is_emergency = db.Column(db.Boolean, default=False)
    is_skipped = db.Column(db.Boolean, default=False)
    is_held = db.Column(db.Boolean, default=False)
    slot = db.Column(db.ForeignKey("schedule.unique_id"), nullable=True, default=None)

    def __init__(self, service_name, start, branch_id, ticket, active, nxt, serviced, teller, kind, user, instant,
                 forwarded):
        self.service_name = service_name
        self.start = start
        self.branch_id = branch_id
        self.ticket = ticket
        self.active = active
        self.nxt = nxt
        self.serviced = serviced
        self.teller = teller
        self.kind = kind
        self.user = user
        self.is_instant = instant
        self.forwarded = forwarded
        self.nxt = 1001


class BookingSchema(ma.Schema):
    class Meta:
        fields = ("id", "service_name", "start", "branch_id", "ticket", "active", "nxt", "serviced", "teller",
                  "kind", "user", "is_instant", "forwarded", "is_synced", "unique_id", "unique_teller", "date_added",
                  "verify", "is_emergency", "is_skipped", "is_held", "slot")


class ImageCompany(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.ForeignKey("company.id"), nullable=False)
    image = db.Column(db.String(length=250), nullable=False)

    def __init__(self, company, image):
        self.company = company
        self.image = image


class ImageCompanySchema(ma.Schema):
    class Meta:
        fields = ("id", "company", "image")


#  new models
class Teller(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.now)
    branch = db.Column(db.Integer)
    service = db.Column(db.String(200))
    unique_id = db.Column(db.String(255), default=ticket_unique, unique=True)
    is_synced = db.Column(db.Boolean, default=False)
    branch_unique_id = db.Column(db.String(length=250), nullable=False, default=1234)
    active = db.Column(db.Boolean, default=True)

    def __init__(self, number, branch, service, branch_unique_id):
        self.number = number
        self.branch = branch
        self.service = service
        self.branch_unique_id = branch_unique_id


class TellerSchema(ma.Schema):
    class Meta:
        fields = (
            "id", "number", "date_added", "branch", "service", "is_synced", "unique_id", "branch_unique_id", "active")


def ticket_unique() -> int:
    return secrets.token_hex(16)


# working with flask migrate
class ServiceOffered(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    branch_id = db.Column(db.ForeignKey("branch.id"), nullable=False)
    name = db.Column(db.String(length=250), unique=True)
    teller = db.Column(db.String(100), nullable=True)
    date_added = db.Column(db.DateTime, default=datetime.now)
    code = db.Column(db.String(length=10), nullable=False)
    icon = db.Column(db.String(length=20))
    is_synced = db.Column(db.Boolean, default=False)
    unique_id = db.Column(db.String(255), default=ticket_unique, unique=True)
    medical_active = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=True)
    is_special = db.Column(db.Boolean, default=False)

    def __init__(self, name, branch_id, teller, code, icon):
        self.name = name
        self.branch_id = branch_id
        self.teller = teller
        self.code = code
        self.icon = icon
        self.is_synced = False


class ServiceOfferedSchema(ma.Schema):
    class Meta:
        fields = ("id", "branch_id", "name", "teller", "date_added", "code", "icon", "unique_id", "medical_active",
                  "active", "is_special")


class Icon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(length=50), nullable=False, unique=True)
    date_added = db.Column(db.DateTime, default=datetime.now)
    branch = db.Column(db.Integer, nullable=False)
    icon = db.Column(db.Text)

    def __init__(self, name, branch, icon):
        self.name = name
        self.branch = branch
        self.icon = icon


class IconSchema(ma.Schema):
    class Meta:
        fields = ("id", "name", "date_added", "branch", "icon")


class Wallpaper(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(length=50), nullable=False, default="wallpaper")
    date_added = db.Column(db.DateTime, default=datetime.now)
    wallpaper = db.Column(db.Text)

    def __init__(self, wallpaper):
        self.wallpaper = wallpaper


class WallpaperSchema(ma.Schema):
    class Meta:
        fields = ("id", "name", "date_added", "wallpaper")


class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(length=250), unique=True)
    active = db.Column(db.Integer, default=0)
    type = db.Column(db.Integer, default=0)

    def __init__(self, name, type):
        self.name = name
        self.type = type


class VideoSchema(ma.Schema):
    class Meta:
        fields = ("id", "name", "active", "type")


class Phrase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phrase = db.Column(db.String(length=250), unique=True)
    use_teller = db.Column(db.Boolean, default=True)
    date_added = db.Column(db.DateTime, default=datetime.now)
    active = db.Column(db.Boolean, default=True)

    def __init__(self, phrase, use_teller):
        self.phrase = phrase
        self.use_teller = use_teller


class PhraseSchema(ma.Schema):
    class Meta:
        fields = ("id", "name", "phrase", "date_added", "active", "use_teller")


class ResetOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.String(length=250), unique=midnight)
    date_added = db.Column(db.DateTime, default=datetime.now)
    active = db.Column(db.Boolean, default=True)

    def __init__(self, time, option):
        self.time = time
        self.active = option


class Logo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.Text)
    date_added = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, path):
        self.path = path


class LogoSchema(ma.Schema):
    class Meta:
        fields = ("id", "path", "date_added")


class ResetOptionSchema(ma.Schema):
    class Meta:
        fields = ("id", "time", "date_added", "active")


class TellerBooking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teller_to = db.Column(db.Integer, nullable=False)
    booking_id = db.Column(db.Integer, nullable=False)
    teller_from = db.Column(db.Integer)
    remarks = db.Column(db.Text, nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)
    date_added = db.Column(db.DateTime, default=datetime.now)
    is_synced = db.Column(db.Boolean, default=False)
    pre_req = db.Column(db.Integer, default=0)
    preq_date_serviced = db.Column(db.DateTime, default=default_preq_date)

    def __init__(self, teller_to, booking_id, teller_from, remarks, active):
        self.teller_to = teller_to
        self.teller_from = teller_from
        self.booking_id = booking_id
        self.remarks = remarks
        self.active = active


class TellerBookingSchema(ma.Schema):
    class Meta:
        fields = (
            "id", "teller_to", "booking_id", "teller_from", "remarks", "active", "date_added", "pre_req", "is_synced",
            "preq_date_serviced")


class Recovery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.ForeignKey("user.id"), nullable=False)
    code = db.Column(db.String(length=50), nullable=False)
    used = db.Column(db.Boolean, nullable=False, default=False)

    def __init__(self, user, code):
        self.user = user
        self.code = code


class RecoverySchema(ma.Schema):
    class Meta:
        fields = ("id", "user", "code", "used")


class BookingTimes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, nullable=False, unique=True)
    date_added = db.Column(db.DateTime, default=datetime.now())
    service = db.Column(db.ForeignKey("service_offered.unique_id"), nullable=False)
    start = db.Column(db.DateTime, default=datetime.now)
    end = db.Column(db.DateTime, default=None)
    is_synced = db.Column(db.Boolean, default=False)

    def __init__(self, booking_id, service):
        self.booking_id = booking_id
        self.service = service


class BookingTimesSchema(ma.Schema):
    class Meta:
        fields = ("id", "booking_id", "start", "end", "service", "date_added", "is_synced")

class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.ForeignKey("user.unique_id"), nullable=False)
    day = db.Column(db.ForeignKey("day.unique_id"), nullable=False)
    service = db.Column(db.ForeignKey("service_offered.unique_id"), nullable=False)
    start = db.Column(db.Time, nullable=False)
    end = db.Column(db.Time, nullable=False)
    last_allowed_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.Boolean, default=False)
    date_added = db.Column(db.DateTime, default=datetime.now)
    unique_id = db.Column(db.String(255), default=ticket_unique, unique=True)
    limit = db.Column(db.Integer, default=0, nullable=False)

    def __init__(self, user, start, end, status):
        self.user = user
        self.start = start
        self.end = end
        self.status = status


class ScheduleSchema(ma.Schema):
    class Meta:
        fields = ("id", "day", "user", "start", "end", "status", "last_allowed_time","service", "date_added", "unique_id", "limit")


class Day(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.String(255), unique=True)
    unique_id = db.Column(db.String(255), default=ticket_unique, unique=True)
    date_added = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, day):
        self.day = day


class DaySchema(ma.Schema):
    class Meta:
        fields = ("id", "day", "unique_id", "date_added")
