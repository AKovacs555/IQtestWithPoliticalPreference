from flask import (
    Flask, render_template, request, redirect, url_for,
    jsonify, session, flash
)
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import RadioField, SubmitField, StringField, PasswordField
from wtforms.validators import InputRequired, Length
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os
import urllib.parse
import stripe

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'devkey')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///responses.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = bool(os.environ.get('FLASK_DEBUG'))
app.config['ENABLE_ANALYTICS'] = os.environ.get('ENABLE_ANALYTICS', '0') == '1'
app.config['ENABLE_ADS'] = os.environ.get('ENABLE_ADS', '0') == '1'
app.config['STRIPE_PUBLISHABLE_KEY'] = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
app.config['STRIPE_SECRET_KEY'] = os.environ.get('STRIPE_SECRET_KEY', '')

stripe.api_key = app.config['STRIPE_SECRET_KEY']

csrf = CSRFProtect(app)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@app.context_processor
def inject_config():
    return dict(config=app.config, datetime=datetime)

class Response(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    iq_score = db.Column(db.Integer, nullable=False)
    party = db.Column(db.String(50), nullable=False)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_premium = db.Column(db.Boolean, default=False)

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
        'question': 'What comes next in the sequence: 2, 4, 8, 16, ...?',
        'options': ['18', '24', '32', '34'],
        'answer': 2
    },
    {
        'question': 'If all Bloops are Razzies and all Razzies are Lazzies, are all Bloops definitely Lazzies?',
        'options': ['Yes', 'No', 'Maybe', 'Not sure'],
        'answer': 0
    },
    {
        'question': 'Which shape has four equal sides and four right angles?',
        'options': ['Triangle', 'Square', 'Circle', 'Pentagon'],
        'answer': 1
    },
    {
        'question': 'Find the missing letter in the series: A, C, E, G, ?',
        'options': ['H', 'I', 'J', 'K'],
        'answer': 1
    },
    {
        'question': 'Which number is the smallest?',
        'options': ['-2', '0', '1', '3'],
        'answer': 0
    }
]


PARTIES = ['Party A', 'Party B', 'Party C', 'None/No preference']

class PartyForm(FlaskForm):
    party = RadioField('Which party do you support?', choices=[(p, p) for p in PARTIES],
                       validators=[InputRequired()])
    submit = SubmitField('Submit')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6)])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Login')


def create_tables():
    with app.app_context():
        db.create_all()
        if Question.query.count() == 0:
            for q in DEFAULT_QUESTIONS:
                question = Question(
                    question=q['question'],
                    option1=q['options'][0],
                    option2=q['options'][1],
                    option3=q['options'][2],
                    option4=q['options'][3],
                    answer_index=q['answer']
                )
                db.session.add(question)
            db.session.commit()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

create_tables()

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists.')
        else:
            user = User(username=form.username.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('index'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid credentials')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/subscribe', methods=['POST'])
@login_required
def subscribe():
    session_data = stripe.checkout.Session.create(
        payment_method_types=['card'],
        mode='payment',
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {'name': 'Premium Access'},
                'unit_amount': 500,
            },
            'quantity': 1,
        }],
        success_url=url_for('subscription_success', _external=True),
        cancel_url=url_for('index', _external=True)
    )
    return redirect(session_data.url)


@app.route('/subscribe/success')
@login_required
def subscription_success():
    current_user.is_premium = True
    db.session.commit()
    flash('Subscription successful!')
    return redirect(url_for('index'))

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    questions = Question.query.all()
    if 'quiz_index' not in session:
        session['quiz_index'] = 0
        session['answers'] = {}

    index = session['quiz_index']

    if request.method == 'POST':
        choice = request.form.get('choice')
        if choice is not None:
            session['answers'][str(index)] = int(choice)
        index += 1
        session['quiz_index'] = index

    if index >= len(questions) or (not current_user.is_authenticated and index >= 5):
        score = 0
        for i, q in enumerate(questions):
            if str(i) in session['answers'] and session['answers'][str(i)] == q.answer_index:
                score += 20
        session.pop('quiz_index', None)
        session.pop('answers', None)
        session['score'] = score
        return redirect(url_for('survey'))

    question = questions[index]
    progress = f"{index + 1} / {len(questions)}"
    return render_template('quiz.html', question=question, progress=progress)

@app.route('/survey', methods=['GET', 'POST'])
def survey():
    form = PartyForm()
    if form.validate_on_submit():
        score = session.get('score')
        if score is None:
            return redirect(url_for('quiz'))
        response = Response(iq_score=score, party=form.party.data)
        db.session.add(response)
        db.session.commit()
        session.pop('score', None)
        session['last_result'] = {'score': score, 'party': form.party.data}
        return redirect(url_for('result'))
    return render_template('survey.html', form=form)

@app.route('/result')
def result():
    result = session.get('last_result')
    if not result:
        return redirect(url_for('index'))
    text = (
        f"I scored {result['score']} on this quick IQ quiz and support {result['party']}! Try it yourself:"
    )
    url = url_for('index', _external=True)
    params = urllib.parse.urlencode({"text": text, "url": url})
    tweet_url = f"https://twitter.com/intent/tweet?{params}"
    fb_url = f"https://www.facebook.com/sharer/sharer.php?u={urllib.parse.quote(url)}"
    line_url = f"https://social-plugins.line.me/lineit/share?url={urllib.parse.quote(url)}"
    return render_template('result.html', result=result, tweet_url=tweet_url,
                           fb_url=fb_url, line_url=line_url)

@app.route('/summary')
def summary():
    return render_template('summary.html')


@app.route('/premium')
@login_required
def premium():
    if not current_user.is_premium:
        flash('Premium membership required')
        return redirect(url_for('index'))
    return render_template('premium.html')


@app.route('/terms')
def terms():
    return render_template('terms.html')


@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/api/summary')
def api_summary():
    data = db.session.query(Response.party,
                            db.func.count(Response.id),
                            db.func.avg(Response.iq_score)).group_by(Response.party).all()
    summary_data = {
        'parties': [],
        'counts': [],
        'averages': []
    }
    for party, count, avg in data:
        summary_data['parties'].append(party)
        summary_data['counts'].append(count)
        summary_data['averages'].append(round(avg, 2))
    return jsonify(summary_data)

if __name__ == '__main__':
    app.run(debug=True)
