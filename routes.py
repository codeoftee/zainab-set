import os
from datetime import timedelta

from flask import render_template, request, flash, session, redirect, url_for
import hashlib

from werkzeug.utils import secure_filename

from config import Config
from index import db, app
from models import User, Products
from user_functions import check_user


@app.route('/admin')
def admin_page():
    user_profile = check_user()
    if user_profile is None:
        return redirect(url_for('login'))
    products = Products.query.all()
    return render_template('admin.html', user_profile=user_profile,
                           products=products)


@app.route('/add-product', methods=['POST', 'GET'])
def add_product():
    user_profile = check_user()
    if user_profile is None:
        return redirect(url_for('login'))

    if request.method == 'GET':
        return render_template('add-product.html')

    title = request.form.get('title')
    price = request.form.get('price')
    description = request.form.get('description')
    category = request.form.get('category')
    # upload image
    image = request.files['image']
    if image is None or image.filename is None:
        flash('Please select product image!')
        return render_template('add-product.html')

    filename = secure_filename(image.filename)
    image.save(os.path.join(Config.UPLOADS_FOLDER, filename))
    picture = filename
    product = Products(title=title, price=price, description=description,
                       category=category, picture=picture)
    db.session.add(product)
    db.session.commit()
    flash('Product added successfully!')
    return redirect(url_for('admin_page'))


@app.route('/edit/<pid>', methods=['POST', 'GET'])
def edit_product(pid):
    user_profile = check_user()
    if user_profile is None:
        return redirect(url_for('login'))
    product = Products.query.filter_by(id=pid).first()
    if product is None:
        # the product with that id cannot be found
        flash("Product not found")
        return redirect(url_for('admin_page'))

    if request.method == 'GET':
        return render_template('edit.html', product=product)
    else:
        # update the product
        product.title = request.form.get('title')
        product.price = request.form.get('price')
        product.description = request.form.get('description')
        product.category = request.form.get('category')

        image = request.files['image']
        if image is not None and image.filename is not None:
            filename = secure_filename(image.filename)
            image.save(os.path.join(Config.UPLOADS_FOLDER, filename))
            product.picture = filename
        db.session.commit()
        flash('Product updated successfully')
        return redirect(url_for('admin_page'))


@app.route('/delete/<pid>')
def delete_product(pid):
    user = check_user()
    if user is None:
        return redirect(url_for('login'))

    # check database for the product with that id.
    product = Products.query.filter(Products.id == pid).one()
    if product is None:
        # if the product was not found send msg and redirect
        flash('Product not found')
        return redirect(url_for('admin_page'))
    else:
        db.session.delete(product)
        db.session.commit()
        flash('{} deleted successfully'.format(product.title))
        return redirect(url_for('admin_page'))


@app.route('/')
def homepage():
    user_profile = check_user()
    return render_template('home.html', user_profile=user_profile)


@app.route('/login')
def login_page():
    return render_template('login.html')


@app.route('/logout')
def logout():
    # remove sessions
    session.pop('email')
    session.pop('password')
    session.pop('id')
    # remove cookies
    resp = redirect(url_for('homepage'))
    resp.set_cookie('user_id', max_age=0)
    resp.set_cookie('pw', max_age=0)
    return resp


@app.route('/do-login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    correct_user = User.query.filter_by(email=email).first()
    if correct_user is not None:
        if correct_user.password_hash == password_hash:
            flash("Welcome " + correct_user.firstname)
            # save session pythonbasics.org/flask-sessions/
            session['email'] = email
            session['password'] = password
            session['id'] = correct_user.id

            response = redirect(url_for('admin_page'))
            response.set_cookie('user_id', str(correct_user.id),
                                max_age=timedelta(hours=24))
            response.set_cookie('pw', password_hash,
                                max_age=timedelta(hours=24))
            return response

    flash("Invalid email or password")
    return redirect(url_for('login_page'))



@app.route('/product/<pid>')
def view_product(pid):
    pid = int(pid)
    ans = pid * 4
    return "U are looking for product {}".format(ans)


@app.route('/register')
def register_page():
    return render_template('register.html')


@app.route('/do-sign-up', methods=['POST'])
def do_signup():
    firstname = request.form['firstname']
    lastname = request.form['lastname']
    email = request.form['email']
    phone = request.form['phone']
    password = request.form['password']
    password2 = request.form['password2']
    if firstname == '' or lastname == '' or email == '' or password == '':
        flash('All fields are required!')
        return redirect(url_for('register_page'))
    if password != password2:
        flash('Passwords does not match')
        return redirect(url_for('register_page'))
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    user_exist = User.query.filter_by(email=email).first()
    if user_exist is not None:
        flash('Email already exist')
        return redirect(url_for('register_page'))

    new_user = User(firstname=firstname, lastname=lastname, email=email,
                    password_hash=password_hash, phone=phone)
    db.session.add(new_user)
    db.session.commit()
    # save session pythonbasics.org/flask-sessions/
    session['email'] = email
    session['password'] = password
    session['id'] = new_user.id

    response = redirect(url_for('homepage'))
    response.set_cookie('user_id', str(new_user.id),
                        max_age=timedelta(hours=24))
    response.set_cookie('pw', password_hash,
                        max_age=timedelta(hours=24))
    return response
