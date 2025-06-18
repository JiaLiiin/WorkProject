from flask import Flask, render_template, request
from search import searchLetters

app = Flask(__name__)
@app.route('/')
def hello()->str:
    return 'Hello world from Flask'

@app.route('/entry')
def entry_page()->'html':
    return render_template('entry.html', the_title='Welcome to search letters on web')

@app.route('/another', methods=['POST'])
def search()->str:
    phrase=request.form['phrase']
    letters=request.form['letters']
    title='Here are the results: '
    results=str(searchLetters(phrase, letters))
    return render_template('result.html', the_title=title, the_phrase=phrase, the_letters=letters,the_result=results)   

app.run()
