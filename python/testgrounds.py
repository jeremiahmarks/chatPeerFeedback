import config
import MySQLdb


def red():
	db=MySQLdb.connect(host=config.MySQLConnection.hostname,user=config.MySQLConnection.username, passwd=config.MySQLConnection.password, db=config.MySQLConnection.dbname)
	cursor=db.cursor()

	cursor.execute("SELECT * FROM maintable")
	numrows = int(cursor.rowcount)

	for x in range(0,numrows):
	    row = cursor.fetchone()
	    print row[0], "-->", row[1] , " " , row[2], " - ", row[3]

if __name__ == '__main__':
	red()
