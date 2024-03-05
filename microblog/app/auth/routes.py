from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user
from urllib.parse import urlsplit
from app import app, db
from app.models import User
from app.auth.email import send_password_reset_email

from sqlalchemy import text
from werkzeug.security import generate_password_hash
from flask_wtf.csrf import generate_csrf

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

    return render_template('auth/login.html', title='Sign In', csrf_token=generate_csrf)

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

    return render_template('auth/register.html', title='Register', csrf_token=csrf_token)

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
    return render_template('auth/reset_password_request.html', title='Reset Password', csrf_token=generate_csrf)

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
    return render_template('auth/reset_password.html', csrf_token=generate_csrf)
