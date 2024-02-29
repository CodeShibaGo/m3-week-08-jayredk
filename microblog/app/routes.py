from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
import sqlalchemy as sa
from urllib.parse import urlsplit
from datetime import datetime, timezone
from app import app, db
from app.models import User, Post
from app.email import send_password_reset_email

from sqlalchemy import text
from werkzeug.security import generate_password_hash
from flask_wtf.csrf import generate_csrf

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        post = Post(body=request.form['post'], author=current_user)
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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        sql_query = text(f"SELECT * FROM user where username='{username}'")
        user = db.session.query(User).from_statement(sql_query).first()

        if user is None or not user.check_password(request.form['password']):
            flash('Invalid username or password')
            return redirect(url_for('login'))

        login_user(user, remember=request.form.get('remember', False))
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page):
            next_page = url_for('index')
        return redirect(next_page)

    return render_template('login.html', title='Sign In', csrf_token=generate_csrf)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    csrf_token = generate_csrf

    if request.method == 'POST':
        password = request.form['password']
        password2 = request.form['password2']

        if (password != password2): 
            flash('password do not match')
            return redirect(url_for('register'))
        
        user_info = {
            'username': request.form['username'],
            'email': request.form['email'],
            'password_hash': generate_password_hash(password)
        }

        sql_query = text("""
            INSERT INTO user (username, email, password_hash)
            VALUES (:username, :email, :password_hash)
        """)
        db.session.execute(sql_query, user_info)
        db.session.commit()
        
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))

    return render_template('register.html', title='Register', csrf_token=csrf_token)

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

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form['email']
        sql_query = text(f"SELECT * FROM user WHERE email ='{email}'")
        user = db.session.query(User).from_statement(sql_query).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html', title='Reset Password', csrf_token=generate_csrf)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))

    if request.method == 'POST':
        password = request.form['password']
        user.set_password(password)
        db.session.commit()
        flash('Your password has been reset')
        return redirect(url_for('login'))
    return render_template('reset_password.html', csrf_token=generate_csrf)
