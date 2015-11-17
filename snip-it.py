import flask
import os
import pygments
import pygments.lexers
import pygments.formatters
import sys
import uuid

app = flask.Flask(__name__)

try:
    os.makedirs('data')
except:
    pass

@app.route('/')
def home():
    '''Show a form for the user to upload a snippet'''

    return flask.render_template(
        'home.html',
    )

@app.route('/save', methods = ['POST'])
def save():
    '''Save a new snippet'''

    content = flask.request.form['code']
    id = str(uuid.uuid4())

    with open(os.path.join('data', id), 'w') as fout:
        fout.write(content)

    return flask.redirect('/{}'.format(id))

@app.route('/<id>', methods = ['GET'])
def display(id):
    '''Show a saved snippet'''

    with open(os.path.join('data', id), 'r') as fin:
        content = fin.read()

    output = pygments.highlight(
        content,
        pygments.lexers.guess_lexer(content),
        pygments.formatters.HtmlFormatter(linenos = True)
    )

    return flask.render_template(
        'display.html',
        code = output,
    )

@app.route('/<id>', methods = ['DELETE'])
def delete(id):
    '''Delete a snippet'''

    os.remove(os.path.join('data', id))
    return flask.redirect('/')

if __name__ == '__main__':
    app.debug = '--debug' in sys.argv
    app.run(host = '0.0.0.0', port = 5000)
