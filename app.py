import psycopg2
from flask import Flask, render_template, request, url_for, flash, redirect
from werkzeug.exceptions import abort
from datetime import datetime
from init_db import do_init


def get_db_connection():
    conn = psycopg2.connect(
    host="localhost",
    database="blogdb",
    user="postgres")
    return conn

def get_post(post_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM posts WHERE id = %s',
                        (post_id,))
    columns = list(cur.description)
    post = cur.fetchall()
    conn.close()
    if post is None:
        abort(404)
    return (post, columns)

app = Flask(__name__)
do_init()
app.config['SECRET_KEY'] = 'do_not_touch_or_you_will_be_fired'


# this function is used to format date to a finnish time format from database format
# e.g. 2021-07-20 10:36:36 is formateed to 20.07.2021 klo 10:36
def format_date(post_date):
    isodate = post_date.replace(' ', 'T')
    newdate = datetime.fromisoformat(isodate)
    return newdate.strftime('%d.%m.%Y') + ' klo ' + newdate.strftime('%H:%M')


# this index() gets executed on the front page where all the posts are
@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM posts')
    columns = list(cur.description)
    result = cur.fetchall()
    conn.close()
    # we need to iterate over all posts and format their date accordingly.
    posts = []
    for row in result:
        row_dict = {}
        for i, col in enumerate(columns):
            row_dict[col.name] = row[i]
        posts.append(row_dict)
    return render_template('index.html', posts=posts)


# here we get a single post and return it to the browser
@app.route('/<int:post_id>')
def post(post_id):
    result, columns = get_post(post_id)
    post = []
    for row in result:
        row_dict = {}
        for i, col in enumerate(columns):
            row_dict[col.name] = row[i]
        post.append(row_dict)
    return render_template('post.html', post=post[0])

# here we create a new post
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('INSERT INTO posts (title, content) VALUES (%s, %s)',
                         (title, content))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))

    return render_template('create.html')


@app.route('/<int:id>/edit', methods=('GET', 'POST'))
def edit(id):
    result, columns = get_post(id)
    post = []
    for row in result:
        row_dict = {}
        for i, col in enumerate(columns):
            row_dict[col.name] = row[i]
        post.append(row_dict)

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('UPDATE posts SET title = %s, content = %s'
                         ' WHERE id = %s',
                         (title, content, id))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))

    return render_template('edit.html', post=post[0])


# Here we delete a SINGLE post.
@app.route('/<int:id>/delete', methods=('POST',))
def delete(id):
    result, columns = get_post(id)
    post = []
    for row in result:
        row_dict = {}
        for i, col in enumerate(columns):
            row_dict[col.name] = row[i]
        post.append(row_dict)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM posts WHERE id = %s', (id,))
    conn.commit()
    conn.close()
    flash('"{}" was successfully deleted!'.format(post[0]['title']))
    return redirect(url_for('index'))
