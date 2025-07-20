from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import RadioField, SubmitField
from wtforms.validators import InputRequired
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import urllib.parse

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'devkey')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///responses.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = bool(os.environ.get('FLASK_DEBUG'))
app.config['ENABLE_ANALYTICS'] = os.environ.get('ENABLE_ANALYTICS', '0') == '1'

csrf = CSRFProtect(app)
db = SQLAlchemy(app)

@app.context_processor
def inject_config():
    return dict(config=app.config, datetime=datetime)

class Response(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    iq_score = db.Column(db.Integer, nullable=False)
    party = db.Column(db.String(50), nullable=False)

# Simple quiz data
QUIZ_QUESTIONS = [
    {
        'question': 'What comes next in the sequence: 2, 4, 8, 16, ...?',
        'options': ['18', '24', '32', '34'],
        'answer': 2  # index of correct option
    },
    {
        'question': 'If all Bloops are Razzies and all Razzies are Lazzies, are all Bloops definitely Lazzies?',
        'options': ['Yes', 'No'],
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


def create_tables():
    with app.app_context():
        db.create_all()

create_tables()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if request.method == 'POST':
        score = 0
        for i, q in enumerate(QUIZ_QUESTIONS):
            user_answer = request.form.get(f'q{i}')
            if user_answer is not None and int(user_answer) == q['answer']:
                score += 20
        session['score'] = score
        return redirect(url_for('survey'))
    return render_template('quiz.html', questions=QUIZ_QUESTIONS)

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
    return render_template('result.html', result=result, tweet_url=tweet_url)

@app.route('/summary')
def summary():
    return render_template('summary.html')

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
