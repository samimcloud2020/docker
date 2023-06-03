from flask import Flask,render_template, request
from flask_mysqldb import MySQL
 
app = Flask(__name__)
 
app.config['MYSQL_HOST'] = 'mydb'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_PORT'] = '3306'
#app.config['MYSQL_DB'] = 'flask'
 
mysql = MySQL(app)
@app.route("/")
def home():
    return "Hello, World!"
    
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port='5000')

#import mysql.connector
#db = mysql.connector.connect(host = 'mydb', user = 'root', password = 'root', port = 3306)
