from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)

#configuring sql settings
from sql_config import configure
configure(app)
mysql = MySQL(app)

#ROUTES
@app.route('/')
def index():
	return render_template('home.html')

@app.route('/about')
def about():
	return render_template('about.html')

@app.route('/articles')
def articles():
	# Displaying articles
	cur = mysql.connection.cursor()
	result = cur.execute('select * from articles')
	articles = cur.fetchall()

	if result > 0:
		return render_template('articles.html', articles = articles)
	else:
		msg = "No articles found!"
		return render_template('articles.html', msg = msg)

	cur.close()


@app.route('/article/<string:id>/')
def article(id):
	# Selecting specific article
	cur = mysql.connection.cursor()
	result = cur.execute('select * from articles where id = %s', [id])
	article = cur.fetchone()

	return render_template('article.html', article = article)



#REGISTRATION
class RegisterForm(Form):
	name = StringField('Name', [validators.Length(min=1, max=50)])
	username = StringField('Username', [validators.Length(min=4, max=25)])
	email = StringField('Email', [validators.Length(min=6, max=50)])
	password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
	confirm = PasswordField('Confirm Password')

@app.route('/register', methods = ['GET', 'POST'])
def register():
	form = RegisterForm(request.form)
	if request.method == 'POST' and form.validate():
		name = form.name.data
		email = form.email.data
		username = form.username.data
		password = sha256_crypt.encrypt(str(form.password.data)) #creating password hash

		cur = mysql.connection.cursor()
		cur.execute('insert into users(name, email, username, password) values(%s, %s, %s, %s)', (name, email, username, password))
		mysql.connection.commit()
		cur.close()

		flash('Successfully registered! Log in to continue.', 'success')
		return redirect(url_for('login'))


	return render_template('register.html', form = form)


#LOGIN
@app.route('/login', methods = ['GET' , 'POST'])
def login():
	if request.method == 'POST':
		#get form fields
		username = request.form['username']
		password_candidate = request.form['password']

		#creating a cursor
		cur = mysql.connection.cursor()
		result = cur.execute('select * from users where username = %s', [username])
		if result > 0:
			data = cur.fetchone()
			password = data['password']

			#comparing hashes
			if sha256_crypt.verify(password_candidate, password):
				#Passes
				session['logged_in'] = True
				session['username'] = username

				flash('Successfully logged in!', 'success')
				return redirect(url_for('dashboard'))


			else:
				error = "Invalid password"
				return render_template('login.html', error=error)

			cur.close()

		else:
			error = "Username not found"
			return render_template('login.html', error=error)

	return render_template('login.html')

#To avoid manual url changes to view unauthorized dashboard
def is_logged_in(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return f(*args, **kwargs)
		else:
			flash('Unauthorized, please log in first.', 'danger')
			return redirect(url_for('login'))
	return wrap

#DASHBOARD
@app.route('/dashboard')
@is_logged_in
def dashboard():
	# Displaying articles
	cur = mysql.connection.cursor()
	result = cur.execute('select * from articles')
	articles = cur.fetchall()

	if result > 0:
		return render_template('dashboard.html', articles = articles)
	else:
		msg = "No articles found!"
		return render_template('dashboard.html', msg = msg)

	cur.close()

@app.route('/logout')
@is_logged_in
def logout():
	session.clear()
	flash('Successfully logged out.','success')
	return redirect(url_for('login'))


#ARTICLES
class ArticleForm(Form):
	title = StringField('Title', [validators.Length(min=1, max=200)])
	body = TextAreaField('Content', [validators.Length(min=30)])

#Add article
@app.route('/add_article', methods = ['GET', 'POST'])
@is_logged_in
def add_article():
	form = ArticleForm(request.form)
	if request.method == 'POST' and form.validate():
		title = form.title.data
		body = form.body.data

		#create cursor
		cur = mysql.connection.cursor()
		result = cur.execute('insert into articles(title, body, author) values (%s, %s, %s)', (title, body, session['username']))
		mysql.connection.commit()
		cur.close()
		flash('Artcle successfully created', 'success')
		return redirect(url_for('dashboard'))

	return render_template('add_article.html', form=form)

#edit article
@app.route('/edit_article/<string:id>', methods = ['GET', 'POST'])
@is_logged_in
def edit_article(id):
	#getting article by id
	cur = mysql.connection.cursor()
	result = cur.execute('select * from articles where id = %s', [id])
	article = cur.fetchone()

	#getting the form
	form = ArticleForm(request.form)

	#populate fields
	form.title.data = article['title']
	form.body.data = article['body']


	if request.method == 'POST' and form.validate():
		title = request.form['title']
		body = request.form['body']

		#create cursor
		cur = mysql.connection.cursor()
		result = cur.execute('update articles set title = %s, body = %s where id = %s', (title, body, id))
		mysql.connection.commit()
		cur.close()
		
		flash('Artcle successfully updated', 'success')
		return redirect(url_for('dashboard'))

	return render_template('edit_article.html', form=form)


if __name__ == '__main__':
	app.secret_key = 'secretkey'
	app.run(debug=True)
