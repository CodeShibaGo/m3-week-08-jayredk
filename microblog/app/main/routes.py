from flask import render_template, flash, redirect, url_for, request, g
from flask_login import current_user, login_required
from flask_babel import _, get_locale
import sqlalchemy as sa
from langdetect import detect, LangDetectException
from datetime import datetime, timezone
from app import app, db
from app.models import User, Post
from app.translate import translate

from sqlalchemy import text
from flask_wtf.csrf import generate_csrf

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()
    g.locale = str(get_locale())

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        try:
            language = detect(request.form['post'])
        except LangDetectException:
            language = ''
        post = Post(body=request.form['post'], author=current_user, language=language)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('index'))
    page = request.args.get('page', 1, type=int)
    posts = db.paginate(current_user.following_posts(), page=page, per_page=app.config['POSTS_PER_PAGE'], error_out=False)
    
    next_url = url_for('index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) \
        if posts.has_prev else None

    return render_template('index.html', title='Home page', csrf_token=generate_csrf, posts=posts.items, next_url=next_url, prev_url=prev_url)

@app.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    query = sa.select(Post).order_by(Post.timestamp.desc())
    posts = db.paginate(query, page=page, per_page=app.config['POSTS_PER_PAGE'], error_out=False)

    next_url = url_for('explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('explore', page=posts.prev_num) \
        if posts.has_prev else None

    return render_template('index.html', title='Explore', posts=posts.items, next_url=next_url, prev_url=prev_url)

@app.route('/user/<username>')
@login_required
def user(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))
    page = request.args.get('page', 1, type=int)
    query = user.posts.select().order_by(Post.timestamp.desc())
    posts = db.paginate(query, page=page, per_page=app.config['POSTS_PER_PAGE'], error_out=False)

    next_url = url_for('user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    
    return render_template('user.html', user=user, posts=posts, next_url=next_url, prev_url=prev_url, csrf_token=generate_csrf)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.username = request.form['username']
        current_user.about_me = request.form['about_me']
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        user_info = {
            'username': current_user.username,
            'about_me': current_user.about_me
        }
        
    return render_template('edit_profile.html', title='Edit profile', user=user_info, csrf_token=generate_csrf)

@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    if request.method == 'POST':
        sql_query = text(f"SELECT * FROM user WHERE username ='{username}'")
        user = db.session.query(User).from_statement(sql_query).first()
        if user is None:
            flash(f'User {username} not found.')
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash(f'You are following {username}!')
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))
    
@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    if request.method == 'POST':
        sql_query = text(f"SELECT * FROM user WHERE username ='{username}'")
        user = db.session.query(User).from_statement(sql_query).first()
        if user is None:
            flash(f'User {username} not found.')
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash(f'You are not following {username}.')
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))

@app.route('/translate', methods=['POST'])
@login_required
def translate_text():
    data = request.get_json()
    return { 'text': translate(data['text'], data['source_language'], data['dest_language'])}
