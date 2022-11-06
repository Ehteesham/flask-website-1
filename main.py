import mail as mail
from flask import Flask, render_template, session, request, redirect
from datetime import datetime
import json
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
import os
import math
from werkzeug.utils import secure_filename

with open('config.json', 'r') as c:
    para = json.load(c)['parameter']

local_server = True
app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = para['uploader_file']
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=para['gmail-user'],
    MAIL_PASSWORD=para['gmail-password']
)
mail = Mail(app)

if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = para['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = para['prod_uri']

db = SQLAlchemy(app)


class Contact(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(300), nullable=False)
    phone = db.Column(db.String(12), nullable=False)
    message = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)


class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    tagline = db.Column(db.String(40), nullable=False)
    slug = db.Column(db.String(12), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    img_file = db.Column(db.String(20), nullable=False)
    date = db.Column(db.String(12), nullable=True)


@app.route("/")
def home():
    posts = Posts.query.filter_by().all()  # [0:para['no_posts']]
    last = math.ceil(len(posts)/int(para['no_posts']))

    page = request.args.get('page')
    if not str(page).isnumeric():
        page = 1
    page = int(page)
    posts = posts[(page-1)*int(para['no_posts']): (page-1)*int(para['no_posts'])+int(para['no_posts'])]
    if page == 1:
        prev = "#"
        nex = "/?page=" + str(page + 1)
    elif page == last:
        nex = "#"
        prev = "/?page=" + str(page - 1)
    else:
        prev = "/?page=" + str(page - 1)
        nex = "/?page=" + str(page + 1)

    return render_template("index.html", params=para, posts=posts, prev=prev, nex=nex)


@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone_number')
        message = request.form.get('message')
        entry = Contact(name=name, email=email, phone=phone, message=message, date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New message from ' + name,
                          sender=email,
                          recipients=[para['gmail-user']],
                          body=message + "\n" + phone
                          )

    return render_template("contact.html", params=para)


@app.route("/post/<string:post_slug>", methods=['GET'])
def post_render(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template("post.html", params=para, post=post)


@app.route("/about")
def about():
    return render_template("about.html", params=para)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if 'user' in session and session['user'] == para['user_name']:
        posts = Posts.query.all()
        return render_template("dashboard.html", params=para, posts=posts)

    if request.method == 'POST':
        username = request.form.get('uname')
        userpassword = request.form.get('upass')

        if username == para['user_name'] and userpassword == para['user_password']:
            session['user'] = username
            posts = Posts.query.all()
            return render_template("dashboard.html", params=para, posts=posts)
        else:
            return render_template("login.html", params=para)

    else:
        return render_template("login.html", params=para)


@app.route("/edit/<string:sno>", methods=['GET', 'POST'])
def edit(sno):
    if 'user' in session and session['user'] == para['user_name']:
        if request.method == 'POST':
            title = request.form.get('title')
            tline = request.form.get('tagline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()
            if sno == '0':
                entry = Posts(title=title, tagline=tline, slug=slug, content=content,
                              img_file=img_file, date=date)
                db.session.add(entry)
                db.session.commit()
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = title
                post.tagline = tline
                post.slug = slug
                post.img_file = img_file
                post.content = content
                post.date = datetime.now()
                db.session.commit()
                return redirect('/edit/' + sno)

    post = Posts.query.filter_by(sno=sno).first()
    return render_template("edit.html", params=para, post=post, sno=sno)


@app.route("/uploader", methods=['GET', 'POST'])
def uploader():
    if 'user' in session and session['user'] == para['user_name']:
        if request.method == 'POST':
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "Uploaded successfully!"


@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/login')


@app.route("/delete/<string:sno>", methods=['GET', 'POST'])
def delete(sno):
    if 'user' in session and session['user'] == para['user_name']:
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
        return redirect("/login")


app.run(debug=True)
