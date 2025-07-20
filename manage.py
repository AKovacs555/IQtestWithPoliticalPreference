from app import app, db, Question, DEFAULT_QUESTIONS

with app.app_context():
    for q in DEFAULT_QUESTIONS:
        if not Question.query.filter_by(question=q['question']).first():
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
    print('Questions seeded')
