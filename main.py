from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask import Flask, render_template, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import StringField
from newsapi import NewsApiClient
from wtforms.validators import InputRequired, Length
from flask_sqlalchemy import SQLAlchemy
import bcrypt
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finalproject.db'
app.config['SECRET_KEY'] = 'HelloWorld!'

app.app_context().push()
db = SQLAlchemy(app)
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'username'
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=True)
    password_hash = db.Column(db.String(80))
class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = StringField('password', validators=[InputRequired(), Length(min=8, max=80)])
class RegisterForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    email = StringField('email', validators=[InputRequired(), Length(max=50)])
    password = StringField('password', validators=[InputRequired(), Length(min=8, max=80)])
class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(40), unique=True)
    content = db.Column(db.String(1000))
    category = db.Column(db.String(24))
    imageURL = db.Column(db.String(40))
    author = db.Column(db.String(15))
    source = db.Column(db.String(40))
class NewsForm(FlaskForm):
    title = StringField('title', validators=[InputRequired(),  Length(min=4, max=40)])
    content = StringField('content', validators=[InputRequired(), Length(min=1, max=1000)])
    category = StringField('category', validators=[InputRequired(), Length(min=1, max=24)])
    imageURL = StringField('imgURL', validators=[InputRequired(), Length(min=12, max=40)])
    author = StringField('author', validators=[InputRequired(), Length(min=4, max=15)])
    source = StringField('source', validators=[InputRequired(), Length(min=1, max=40)])
with app.app_context():
    db.create_all()
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/signup', methods=['POST', 'GET'])
def signup():
    try:
        form = RegisterForm()
        password = form.password.data
        print(form.password.data)
        if form.validate_on_submit():
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            new_user = User(username=form.username.data, email=form.email.data, password_hash=hashed)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
    except IntegrityError:
        return '<h1>User with that email or username is already registered</h1>', 400
    return render_template('signup.html', title='Sign up', form=form)
@app.route('/bbc',methods=['GET', 'POST'])
def bbc():
    newsapi = NewsApiClient(api_key="71363a23a1444cbdb0470d77b19daac2")
    topheadlines = newsapi.get_top_headlines(sources="bbc-news")
    articles = topheadlines['articles']
    desc = []
    news = []
    img = []
    for i in range(len(articles)):
        myarticles = articles[i]
        news.append(myarticles['title'])
        desc.append(myarticles['description'])
        img.append(myarticles['urlToImage'])
    mylist = zip(news, desc, img)
    return render_template('bbc.html', context=mylist)
@app.route('/login', methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('news'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        password = form.password.data
        if not user:
            return '<h1>Invalid username or password</h1>'
        if bcrypt.checkpw(password.encode('utf-8'), user.password_hash):
            login_user(user)
            return redirect(url_for('news'))
    return render_template('login.html', title='Login', form=form)
@app.route('/products', methods=['POST', 'GET'])
def news():
    news = News.query.all()
    return render_template('tovars.html', news=news)
@app.route('/addnews', methods=['GET', 'POST'])
def addnews():
    form = NewsForm()
    if form.validate_on_submit():
        new_news = News(title=form.title.data, content=form.content.data, category=form.category.data, imageURL=form.imageURL.data, author=form.author.data, source=form.source.data)
        db.session.add(new_news)
        db.session.commit()
        return redirect(url_for('news'))
    return render_template('add.html', form=form)
@app.route('/myads', methods=['GET', 'POST'])
def myads():
    posts = News.query.filter(News.author == current_user.username).all()
    return render_template('myads.html',news=posts)
@app.route('/filter_by/<category>')
def sort_categories(category):
    news = News.query.filter_by(category=category).all()
    return render_template('tovars.html', news=news)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
@login_required
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('index'))
@app.route('/delete-post/<id>')
def delete_post(id):
    post = News.query.filter_by(id=id).first()
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted', category='succes')
    return redirect(url_for('myads'))
@app.route('/edit-post/<id>', methods=['POST', 'GET'])
def edit_post(id):
    form = NewsForm()
    if form.validate_on_submit():
        news = News.query.filter(News.id == id).first()
        news.title = form.title.data
        news.content = form.content.data
        news.category = form.category.data
        news.imageURL = form.imageURL.data
        news.author = form.author.data
        news.source = form.source.data
        db.session.commit()
        return redirect(url_for("myads"))
    return render_template("edit.html", form=form)
if __name__ == '__main__':
    app.run(debug=True)
