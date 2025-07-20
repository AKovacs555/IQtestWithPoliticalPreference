from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
    session,
    flash,
    g,
)
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import RadioField, SubmitField, StringField, PasswordField
from wtforms.validators import InputRequired, Length
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os
import urllib.parse
import json
import uuid
import stripe
from flask_compress import Compress

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "devkey")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///responses.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["ENABLE_ANALYTICS"] = os.environ.get("ENABLE_ANALYTICS", "0") == "1"
app.config["ENABLE_ADS"] = os.environ.get("ENABLE_ADS", "0") == "1"
app.config["STRIPE_PUBLISHABLE_KEY"] = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
app.config["STRIPE_SECRET_KEY"] = os.environ.get("STRIPE_SECRET_KEY", "")
app.config["GOOGLE_ADSENSE_CLIENT_ID"] = os.environ.get("GOOGLE_ADSENSE_CLIENT_ID", "")
app.config["GA_MEASUREMENT_ID"] = os.environ.get("GA_MEASUREMENT_ID", "")
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 604800  # cache static files for a week

Compress(app)

with open(os.path.join(os.path.dirname(__file__), "translations", "en.json")) as f:
    TRANSLATIONS = {"en": json.load(f)}

stripe.api_key = app.config["STRIPE_SECRET_KEY"]

csrf = CSRFProtect(app)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])


def send_verification_email(user):
    token = serializer.dumps(user.id)
    verify_url = url_for("verify_email", token=token, _external=True)
    app.logger.info("Verification link for %s: %s", user.email, verify_url)


@app.context_processor
def inject_config():
    def _(key):
        return TRANSLATIONS.get("en", {}).get(key, key)

    return dict(config=app.config, datetime=datetime, _=_)


class Response(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    iq_score = db.Column(db.Integer, nullable=False)
    party = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True)
    password_hash = db.Column(db.String(128), nullable=False)
    is_premium = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)
    referral_code = db.Column(db.String(32), unique=True)
    referred_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    responses = db.relationship("Response", backref="user", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String, nullable=False)
    option1 = db.Column(db.String, nullable=False)
    option2 = db.Column(db.String, nullable=False)
    option3 = db.Column(db.String, nullable=False)
    option4 = db.Column(db.String, nullable=False)
    answer_index = db.Column(db.Integer, nullable=False)


DEFAULT_QUESTIONS = [
    {
        "question": "What comes next in the sequence: 2, 4, 8, 16, ...?",
        "options": ["18", "24", "32", "34"],
        "answer": 2,
    },
    {
        "question": "If all Bloops are Razzies and all Razzies are Lazzies, are all Bloops definitely Lazzies?",
        "options": ["Yes", "No", "Maybe", "Not sure"],
        "answer": 0,
    },
    {
        "question": "Which shape has four equal sides and four right angles?",
        "options": ["Triangle", "Square", "Circle", "Pentagon"],
        "answer": 1,
    },
    {
        "question": "Find the missing letter in the series: A, C, E, G, ?",
        "options": ["H", "I", "J", "K"],
        "answer": 1,
    },
    {
        "question": "Which number is the smallest?",
        "options": ["-2", "0", "1", "3"],
        "answer": 0,
    },
    {
        "question": "Which word is the odd one out?",
        "options": ["Dog", "Cat", "Car", "Mouse"],
        "answer": 2,
    },
    {
        "question": "What is 15 divided by 3?",
        "options": ["3", "5", "7", "9"],
        "answer": 1,
    },
    {
        "question": 'If you rearrange the letters "CIFAIPC" you get the name of a(n)?',
        "options": ["Ocean", "Country", "City", "Animal"],
        "answer": 2,
    },
    {
        "question": "Which number best completes the analogy: 8 : 4 as 10 : ?",
        "options": ["3", "5", "7", "9"],
        "answer": 1,
    },
    {
        "question": "Which of these is a mammal?",
        "options": ["Shark", "Dolphin", "Octopus", "Trout"],
        "answer": 1,
    },
    {
        "question": "How many sides does a hexagon have?",
        "options": ["5", "6", "7", "8"],
        "answer": 1,
    },
    {
        "question": "Which month of the year has 28 days?",
        "options": ["February", "April", "September", "All of them"],
        "answer": 3,
    },
    {
        "question": "What is the next number in the series: 3, 6, 9, 12, ...?",
        "options": ["14", "15", "16", "18"],
        "answer": 3,
    },
    {
        "question": "Which planet is known as the Red Planet?",
        "options": ["Earth", "Mars", "Jupiter", "Venus"],
        "answer": 1,
    },
    {
        "question": "Which is heavier: a pound of feathers or a pound of bricks?",
        "options": ["Feathers", "Bricks", "They weigh the same", "Cannot tell"],
        "answer": 2,
    },
    {
        "question": "If 5x = 20, what is x?",
        "options": ["2", "3", "4", "5"],
        "answer": 2,
    },
    {
        "question": "Which of these is a prime number?",
        "options": ["9", "15", "17", "21"],
        "answer": 2,
    },
    {
        "question": "What color do you get when you mix blue and yellow?",
        "options": ["Green", "Purple", "Orange", "Brown"],
        "answer": 0,
    },
    {
        "question": "Which animal is known for its trunk?",
        "options": ["Lion", "Elephant", "Giraffe", "Horse"],
        "answer": 1,
    },
    {
        "question": "Which gas do plants absorb from the atmosphere?",
        "options": ["Oxygen", "Hydrogen", "Carbon Dioxide", "Nitrogen"],
        "answer": 2,
    },
]


PARTIES = ["Party A", "Party B", "Party C", "None/No preference"]


class PartyForm(FlaskForm):
    party = RadioField(
        "Which party do you support?",
        choices=[(p, p) for p in PARTIES],
        validators=[InputRequired()],
    )
    submit = SubmitField("Submit")


class RegistrationForm(FlaskForm):
    username = StringField(
        "Username", validators=[InputRequired(), Length(min=3, max=80)]
    )
    email = StringField("Email", validators=[InputRequired(), Length(max=120)])
    password = PasswordField("Password", validators=[InputRequired(), Length(min=6)])
    submit = SubmitField("Register")


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[InputRequired()])
    password = PasswordField("Password", validators=[InputRequired()])
    submit = SubmitField("Login")


class ForgotPasswordForm(FlaskForm):
    email = StringField("Email", validators=[InputRequired(), Length(max=120)])
    submit = SubmitField("Reset Password")


class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        "New Password", validators=[InputRequired(), Length(min=6)]
    )
    submit = SubmitField("Set Password")


class ChangePasswordForm(FlaskForm):
    password = PasswordField(
        "New Password", validators=[InputRequired(), Length(min=6)]
    )
    submit = SubmitField("Change Password")


def create_tables():
    with app.app_context():
        db.create_all()
        if Question.query.count() == 0:
            for q in DEFAULT_QUESTIONS:
                question = Question(
                    question=q["question"],
                    option1=q["options"][0],
                    option2=q["options"][1],
                    option3=q["options"][2],
                    option4=q["options"][3],
                    answer_index=q["answer"],
                )
                db.session.add(question)
            db.session.commit()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


create_tables()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash("Username already exists.")
        elif User.query.filter_by(email=form.email.data).first():
            flash("Email already registered.")
        else:
            user = User(
                username=form.username.data,
                email=form.email.data,
                referral_code=uuid.uuid4().hex[:8],
            )
            ref = request.args.get("ref")
            if ref:
                ref_user = User.query.filter_by(referral_code=ref).first()
                if ref_user:
                    user.referred_by = ref_user.id
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            send_verification_email(user)
            flash("Please verify your email before logging in.")
            return redirect(url_for("login"))
    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            if not user.is_verified:
                flash("Please verify your email first.")
            else:
                login_user(user)
                return redirect(url_for("index"))
        flash("Invalid credentials")
    return render_template("login.html", form=form)


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = serializer.dumps(user.id)
            reset_url = url_for("reset_password", token=token, _external=True)
            app.logger.info("Password reset link for %s: %s", user.email, reset_url)
            flash("Password reset link sent to your email (simulated).")
        else:
            flash("Email not found.")
    return render_template("forgot_password.html", form=form)


@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    try:
        user_id = serializer.loads(token, max_age=3600)
    except (BadSignature, SignatureExpired):
        flash("Invalid or expired token.")
        return redirect(url_for("login"))
    user = User.query.get(user_id)
    if not user:
        flash("Invalid user.")
        return redirect(url_for("login"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash("Password updated.")
        return redirect(url_for("login"))
    return render_template("reset_password.html", form=form)


@app.route("/verify/<token>")
def verify_email(token):
    try:
        user_id = serializer.loads(token, max_age=3600 * 24)
    except (BadSignature, SignatureExpired):
        flash("Invalid or expired verification link.")
        return redirect(url_for("login"))
    user = User.query.get(user_id)
    if not user:
        flash("Invalid user.")
        return redirect(url_for("login"))
    user.is_verified = True
    db.session.commit()
    flash("Email verified. You can now log in.")
    return redirect(url_for("login"))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/subscribe", methods=["POST"])
@login_required
def subscribe():
    plan = request.form.get("plan", "one_time")
    if plan == "monthly":
        price_data = {
            "currency": "usd",
            "product_data": {"name": "Premium Monthly"},
            "unit_amount": 500,
            "recurring": {"interval": "month"},
        }
        mode = "subscription"
    elif plan == "annual":
        price_data = {
            "currency": "usd",
            "product_data": {"name": "Premium Annual"},
            "unit_amount": 5000,
            "recurring": {"interval": "year"},
        }
        mode = "subscription"
    else:
        price_data = {
            "currency": "usd",
            "product_data": {"name": "Premium Access"},
            "unit_amount": 500,
        }
        mode = "payment"

    session_data = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode=mode,
        line_items=[
            {
                "price_data": price_data,
                "quantity": 1,
            }
        ],
        success_url=url_for("subscription_success", _external=True),
        cancel_url=url_for("premium", _external=True),
    )
    return redirect(session_data.url)


@app.route("/subscribe/success")
@login_required
def subscription_success():
    current_user.is_premium = True
    db.session.commit()
    flash("Subscription successful!")
    return redirect(url_for("premium_success"))


@app.route("/premium/success")
@login_required
def premium_success():
    return render_template("premium_success.html")


@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    questions = Question.query.all()
    if "quiz_index" not in session:
        session["quiz_index"] = 0
        session["answers"] = {}

    index = session["quiz_index"]

    if request.method == "POST":
        choice = request.form.get("choice")
        if choice is not None:
            session["answers"][str(index)] = int(choice)
        index += 1
        session["quiz_index"] = index

    if not current_user.is_authenticated and index >= 5:
        flash("Create an account to unlock more questions.")
        return redirect(url_for("register"))
    if current_user.is_authenticated and not current_user.is_premium and index >= 10:
        flash("Upgrade to premium to access the rest of the quiz.")
        return redirect(url_for("premium"))
    if index >= len(questions):
        score = 0
        for i, q in enumerate(questions):
            if (
                str(i) in session["answers"]
                and session["answers"][str(i)] == q.answer_index
            ):
                score += 1
        score = round((score / len(questions)) * 100)
        session.pop("quiz_index", None)
        session.pop("answers", None)
        session["score"] = score
        return redirect(url_for("survey"))

    question = questions[index]
    progress = f"{index + 1} / {len(questions)}"
    progress_percent = int((index + 1) / len(questions) * 100)
    return render_template(
        "quiz.html",
        question=question,
        progress=progress,
        progress_percent=progress_percent,
    )


@app.route("/survey", methods=["GET", "POST"])
def survey():
    form = PartyForm()
    if form.validate_on_submit():
        score = session.get("score")
        if score is None:
            return redirect(url_for("quiz"))
        response = Response(
            iq_score=score,
            party=form.party.data,
            user_id=current_user.id if current_user.is_authenticated else None,
        )
        db.session.add(response)
        db.session.commit()
        session.pop("score", None)
        session["last_result"] = {"score": score, "party": form.party.data}
        return redirect(url_for("result"))
    return render_template("survey.html", form=form)


@app.route("/result")
def result():
    result = session.get("last_result")
    if not result:
        return redirect(url_for("index"))
    text = f"I scored {result['score']} on this IQ & politics quiz! Can you beat me?"
    url = url_for("index", _external=True)
    params = urllib.parse.urlencode({"text": text, "url": url})
    tweet_url = f"https://twitter.com/intent/tweet?{params}"
    fb_url = f"https://www.facebook.com/sharer/sharer.php?u={urllib.parse.quote(url)}"
    line_url = (
        f"https://social-plugins.line.me/lineit/share?url={urllib.parse.quote(url)}"
    )
    return render_template(
        "result.html",
        result=result,
        tweet_url=tweet_url,
        fb_url=fb_url,
        line_url=line_url,
    )


@app.route("/summary")
def summary():
    return render_template("summary.html")


@app.route("/premium")
@login_required
def premium():
    return render_template("premium.html")


@app.route("/profile")
@login_required
def profile():
    responses = (
        Response.query.filter_by(user_id=current_user.id)
        .order_by(Response.timestamp.desc())
        .all()
    )
    return render_template("profile.html", responses=responses)


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        current_user.set_password(form.password.data)
        db.session.commit()
        flash("Password updated.")
        return redirect(url_for("settings"))
    return render_template("settings.html", form=form)


@app.route("/download-data")
@login_required
def download_data():
    data = {
        "user": {
            "username": current_user.username,
            "email": current_user.email,
            "is_premium": current_user.is_premium,
        },
        "responses": [
            {
                "score": r.iq_score,
                "party": r.party,
                "timestamp": r.timestamp.isoformat(),
            }
            for r in current_user.responses
        ],
    }
    return jsonify(data)


@app.route("/delete-account", methods=["POST"])
@login_required
def delete_account():
    Response.query.filter_by(user_id=current_user.id).delete()
    uid = current_user.id
    logout_user()
    User.query.filter_by(id=uid).delete()
    db.session.commit()
    flash("Account deleted.")
    return redirect(url_for("index"))


@app.route("/delete-history", methods=["POST"])
@login_required
def delete_history():
    Response.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash("History deleted.")
    return redirect(url_for("profile"))


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/api/summary")
def api_summary():
    data = (
        db.session.query(
            Response.party, db.func.count(Response.id), db.func.avg(Response.iq_score)
        )
        .group_by(Response.party)
        .all()
    )
    summary_data = {"parties": [], "counts": [], "averages": []}
    for party, count, avg in data:
        summary_data["parties"].append(party)
        summary_data["counts"].append(count)
        summary_data["averages"].append(round(avg, 2))
    return jsonify(summary_data)


@app.route("/analytics", methods=["POST"])
def analytics():
    event = request.json or {}
    app.logger.info("Event: %s", event)
    return "", 204


if __name__ == "__main__":
    app.run(debug=True)
