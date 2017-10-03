def configure(app):
	app.config['MYSQL_HOST'] = 'localhost' #139.59.29.3
	app.config['MYSQL_USER'] = 'root'
	app.config['MYSQL_PASSWORD'] = 'ayushman.dey97'
	app.config['MYSQL_DB'] = 'myflaskapp'
	app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
