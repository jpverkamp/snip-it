import flask
import os
import pygments
import pygments.lexers
import pygments.formatters
import signal
import sys
import uuid
import redis as redislib

from flask.ext.api import status

app = flask.Flask(__name__)
app.secret_key = os.urandom(24)

redis = redislib.StrictRedis(host = 'redis', decode_responses = True)

def sigterm_handler(signo, frame):
    print('Exiting, force Redis SAVE')
    redis.save()

signal.signal(signal.SIGTERM, sigterm_handler)

@app.route('/', methods = ['GET'])
@app.route('/<post_id>', methods = ['GET'])
def home(post_id = None):
    '''Show a form for the user to upload a snippet'''

    # Render a post in view/edit mode
    if post_id:
        content = redis.hget(post_id, 'content')
        edit_mode = flask.request.args.get('edit', False)

        if edit_mode:
            return flask.render_template('home.html', code = content, edit_mode = True)

        else:
            content = pygments.highlight(content, pygments.lexers.guess_lexer(content), pygments.formatters.HtmlFormatter())
            return flask.render_template('display.html', code = content)

    # Render the home page
    else:
        return flask.render_template('home.html', edit_mode = False)

@app.route('/', methods = ['POST'], defaults = {'post_id': None})
@app.route('/<post_id>', methods = ['POST'])
def save(post_id):
    '''Create a new snippet or edit a previously existing one'''

    content = flask.request.form['code']

    # Edit/delete a previously existing post
    if post_id:
        if not redis.exists(post_id):
            return 'ID not found', status.HTTP_404_NOT_FOUND

        edit_key = flask.request.form['edit_key']
        if redis.hget(post_id, 'edit_key') != edit_key:
            flask.flash('Edit key invalid', status.HTTP_403_FORBIDDEN)
            return flask.redirect('/{}?edit=true'.format(post_id))

        if flask.request.form['action'] == 'Delete':
            redis.delete(post_id)
            flask.flash('Post deleted')
            return flask.redirect('/')

    # Create a new post
    else:
        post_id = str(uuid.uuid4())
        edit_key = str(uuid.uuid4())

    redis.hset(post_id, 'content', content)
    redis.hset(post_id, 'edit_key', edit_key)

    flask.flash('Edit key: {}'.format(edit_key))
    return flask.redirect('/{}'.format(post_id))

@app.route('/<post_id>', methods = ['DELETE'])
def delete(post_id):
    '''Delete a snippet'''

    if not redis.exists(post_id):
        return 'ID not found', status.HTTP_404_NOT_FOUND

    edit_key = flask.request.form['edit_key']
    if redis.hget(post_id, 'edit_key') != edit_key:
        return 'Edit key invalid', status.HTTP_403_FORBIDDEN

    redis.delete(post_id)

    flask.flash('Post deleted')
    return flask.redirect('/')

if __name__ == '__main__':
    app.debug = '--debug' in sys.argv
    app.run(host = '0.0.0.0', port = 5000)
