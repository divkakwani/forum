"""
@author: Divyanshu Kakwani
@license: GPL
"""

from flask import Flask, request, make_response, redirect
from flask import render_template
from db import boardDB
from flask.ext.cache import Cache

app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})


@app.before_request
def before_request():
    boardDB.setup()


@app.teardown_request
def teardown_request(exception):
    boardDB.teardown()


@app.route('/ask', methods=['GET', 'POST'])
def ask():
    if request.method == 'GET':
        return render_template('ask.html')
    elif request.method == 'POST':
        # Get all the values from the form
        name = request.form.get('name')
        title = request.form.get('title')
        desc = request.form.get('desc')

        # Check if any of the above is null. If yes, throw error
        error = not all(len(s) for s in [name, title, desc])
        error_message = 'You missed one or more fields'
        if error:
            return render_template('ask.html', error=error_message)

        boardDB.add_question(title=title, desc=desc, asker=name)
        cache.delete('questions')
        return make_response(redirect('/'))


@app.route('/board')
def alt_board():
    return make_response(redirect('/'))


@cache.cached(timeout=100)
@app.route('/', methods=['GET'])
def board():
    questions = cache.get('questions')
    answers_cnts = cache.get('answers_cnts')
    # Check if each of `questions` and `answers_cnts` exist in the cache
    if not questions:
        questions = boardDB.getall_qs()
        cache.set('questions', questions)
    if not answers_cnts:
        answers_cnts = {q[0]: boardDB.get_num_ans(q[0]) for q in questions}
        cache.set('answers_cnts', answers_cnts)

    return render_template('board.html',
                           questions=questions, answers_cnts=answers_cnts)


@app.route('/question/<qid>', methods=['GET', 'POST'])
def question(qid):
    error_message = None
    if request.method == 'POST':
        name = request.form.get('name')
        answer = request.form.get('answer')
        # Input validation
        if name == '' or answer == '':
            error_message = 'You missed one or more fields'
        else:
            boardDB.add_answer(qid, answer, name)
            cache.delete('answers_cnts')
            return make_response(redirect('/question/' + qid))

    question = boardDB.get_question(qid)
    answers = boardDB.get_answers(qid)
    return render_template('question.html',
                           question=question, answers=answers,
                           error=error_message)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, threaded=True)
