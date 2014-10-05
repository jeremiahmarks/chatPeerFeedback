#!/usr/bin/python

import config
import MySQLdb
import cgi
import re
import datetime 
import random
import cgitb

#import examples

print "Content-type: text/html\n\n"
cgitb.enable()


###############
##
## Classes
##
###############


class Line(object):
	def __init__(self, lineNumber, whoSaidIt, whatWasSaid, timeItWasSaid="", timeSinceLastStatement=""):
		self.lineNumber=lineNumber
		self.whoSaidIt=whoSaidIt
		self.whatWasSaid=whatWasSaid
		self.timeItWasSaid=timeItWasSaid
		self.timeSinceLastStatement=timeSinceLastStatement
		self.allComplexFeedback=[]

	def setSimpleFeedBack(self, simpleA, simpleB):
		self.simpleA=simpleA
		self.simpleB=simpleB

	def addComplexFeedback(self, feedback):
		self.allComplexFeedback.append(feedback)

	def __str__(self):
		thisLine= "     Line number: " + str(self.lineNumber) + "\n" +  "             Who: " + self.whoSaidIt + "\n" + "   What was said: " + self.whatWasSaid + '\n' + "When it was said: " + str(self.timeItWasSaid) + '\n'
		return thisLine

class Chat(object):
	def __init__(self):
		self.Agent=""
		self.Agentfname=""
		self.Agentlinitial=""
		self.Customer=""
		self.chatID=""
		self.fullLog=""
		self.orderedLines={}
		self.lines=[]


################################################################################
##
##  General "What to do now" logic
##`~
################################################################################


def guidingWhereToGo(arguments):

	if (arguments.has_key("chat")):
		if (arguments.has_key("mode")):
			cumulativePage(arguments["chat"].value)
		else:
			votingPage(arguments["chat"].value)
	elif (arguments.has_key("feedbacksubmit")):
		updateDatabase(arguments)
	elif (arguments.has_key("singlesubmit")):
		individualAdd()
	elif (arguments.has_key("multisubmit")):
		multiAdd()
	elif (arguments.has_key("singleChatSubmitted")):
		mainSequence(arguments["chatlog"].value, arguments["chatid"].value)
	else:
		generateIndexPage()



################################################################################
##
##  Displaying that data
##
################################################################################
 
	############################################################################
	##
	## Elements that will be used throughout the site
	##
	############################################################################
def mainnav():
	navstr="""	<div class="nav">
					<form class="addchats" name="addchats" method="post" action="./page.py">
						<input type="submit" name="singlesubmit" value="Submit a single chat">
						<input type="submit" name="multisubmit" value="Submit multiple chats">
						<input type="submit" name="goindex" value="Return to the Index Page">
					</form>
				</div>
	"""
	return navstr

def pagestart(pagetitle="InfusionSoft Chat PeerFeedback"):
	startstr="""
		<html>
			<head>
				<title>%s</title>
				<style>
					body, button, input, select, textarea {
    					background-color: #333;
    					color: #fff;
    					font-family: Arial,Helvetica,sans-serif;
					    font-size: 1.3rem;
					    line-height: 1.5;
					}
				</style>
			</head>
			<body>""" %(pagetitle)
	return startstr



def generateIndexPage():
	"""
	This method is used for generally building and displaying a simple index page
	of all of the chats that have been submitted previously.
	"""
	db=MySQLdb.connect(host=config.MySQLConnection.hostname,user=config.MySQLConnection.username, passwd=config.MySQLConnection.password, db=config.MySQLConnection.dbname)
	cur = db.cursor()

	myquery = "SELECT * FROM maintable"
	cur.execute(myquery)

	rows = cur.fetchall()

	pagehtml = pagestart()

	pagehtml = pagehtml + mainnav()

	addtable = "<table>"
	closetable = "</table>"
	tableRow="<tr>"
	closeTableRow="</tr>"
	closeBody="</body></html>"

	pagehtml = pagehtml + addtable
	pagehtml = pagehtml + tableRow
	pagehtml = pagehtml + "<td>ChatID</td><td>Agent</td><td>Provide Feedback</td><td>View feedback</td>" + closeTableRow 



	for row in rows:
		pagehtml = pagehtml + tableRow + """<td><a href="./page.py?chat=%s">""" %(row[0]) + row[0] + """</a></td><td>""" + row[2] + """</td><td><a href="./page.py?chat=%s">Provide Feedback</a></td><td><a href="./page.py?chat=%s&mode=view">View Feedback</a></td>""" %(row[0], row[0]) + closeTableRow
	pagehtml = pagehtml + closetable + closeBody

	print pagehtml

def votingPage(chatid):
	"""
	This page is used to collect feedback on a chat record.
	"""
	db=MySQLdb.connect(host=config.MySQLConnection.hostname,user=config.MySQLConnection.username, passwd=config.MySQLConnection.password, db=config.MySQLConnection.dbname)
	cur=db.cursor()

	myquery = "SELECT * FROM interactions WHERE chatid ='%s' ORDER BY line" %(chatid)
	cur.execute(myquery)

	rows = cur.fetchall()
	totalLines=len(rows)

	htmlString= pagestart() + mainnav()
	htmlString = htmlString + 	"""<form class="feedback" name="%s" method="post" action="./page.py"><table class="chatRecord" border="1"><tr class="heading"><td>Who</td><td>What Was Said</td><td>Simple Feedback</td><td>Complex Feedback</td></tr>""" %(chatid)
	htmlString = htmlString + """ <input type="hidden" name="thischatid" value="%s"> <input type="hidden" name="linesOfChat" value="%s">""" %(chatid, totalLines)
	for row in rows:
		if (row[2] == "agent"):
			htmlString=htmlString + """
			<tr class="agent" >
				<td class="WhoIsTalking">%s</td>
				<td class="WhatWasSaid">%s</td>
				<td>
					<table class="agentButtons">
						<tr>
							<td class="posButton">
								<input type="radio" name="%s" value="pos">
							</td>
						</tr>
						<tr>
							<td class="negButton">
								<input type="radio" name="%s" value="neg">
							</td>
						</tr>
					</table>
				</td>
				<td>
					<input type="textarea" name="%s" cols="40" rows="5"></textarea>
				</td>
			</tr>""" %(row[2], row[3], "simple"+row[1], "simple"+row[1], "text"+row[1])
		else:
			htmlString = htmlString+"""
			<tr class="user" >
				<td class="WhoIsTalking">%s</td>
				<td class="WhatWasSaid">%s</td>
				<td class="userButton">
					<input type="radio" name="%s" value="important">
				</td>
				<td>
					<input type="textarea" name="%s"ols="40" rows="5"></textarea>
				</td>
			</tr>""" %(row[2], row[3], "simple"+row[1],"text"+row[1])
	htmlString=htmlString + """
		</table> <input type="submit" name="feedbacksubmit" value="submit"></form></body></html>"""
	print htmlString

def cumulativePage(chatid):
	"""
	This page is used to display the cumulative results of one particular chat 
	record
	"""
	thischat = Chat()


	tables = ["complexfeedback", 'interactions', 'maintable', 'simplefeedback']

	pageinformation={}

	for eachtable in tables:
		db=MySQLdb.connect(host=config.MySQLConnection.hostname,user=config.MySQLConnection.username, passwd=config.MySQLConnection.password, db=config.MySQLConnection.dbname)
		cur=db.cursor()
		if (eachtable=="maintable"):
			thisquery = """SELECT * FROM %s WHERE chatid=%s """ %(eachtable, chatid)
		else:
			thisquery = "SELECT * FROM %s WHERE chatid = %s ORDER BY line" %(eachtable, chatid)
		cur.execute(thisquery)
#		pageinformation[eachtable] = cur.execute(thisquery, (eachtable, chatid)).fetchall()
		pageinformation[eachtable] = cur.fetchall()

	htmlString = pagestart() + mainnav()

	#######
	## setting up the top of the page
	#######
	headString = "<div><span>Agent: %s</span><span>ChatID: %s</span></div>" %(pageinformation['maintable'][0][2] , chatid)

	##########
	## Setting Up The Data  (it is capitalized because it is important (>.<)  )
	##########

	for eachline in pageinformation['interactions']:
		thischat.orderedLines[eachline[1]] = Line(eachline[1], eachline[2], eachline[3])
	for eachline in pageinformation['simplefeedback']:
		thischat.orderedLines[eachline[1]].setSimpleFeedBack(eachline[2], eachline[3])
	for eachline in pageinformation['complexfeedback']:
		thischat.orderedLines[eachline[1]].addComplexFeedback(eachline[2])

	##########
	## Creating the table
	##########

	tablestring="""<table class="chatfeedback" border="1">
					<tr class="feedbackHeader">
						<td>Who</td>
						<td>What</td>
						<td>Simple</td>
						<td>In-Depth</td>
					</tr>
					"""
	for eachline in range(len(thischat.orderedLines.keys())):
		el='%05d' %int(eachline)
		if (thischat.orderedLines[el].whoSaidIt == "agent"):
			thisrow="""
			<tr class="agent" >
				<td class="WhoIsTalking">%s</td>
				<td class="WhatWasSaid">%s</td>
				<td>
					<table class="agentFeedback">
						<tr>
							<td class="posFeedback">
								%s
							</td>
						</tr>
						<tr>
							<td class="negFeedback">
								%s
							</td>
						</tr>
					</table>
				</td>
				<td>
					<table class="writtenFeedback">""" %(thischat.orderedLines[el].whoSaidIt, thischat.orderedLines[el].whatWasSaid, str(thischat.orderedLines[el].simpleA), str(thischat.orderedLines[el].simpleB))
			for eachFeedback in thischat.orderedLines[el].allComplexFeedback:
				thisrow = thisrow + """<tr class="writtenFeedback"><td class="writtenFeedback">%s</td></tr>""" %(eachFeedback, )
			thisrow=thisrow + """
					</table>
				</td>
			</tr>"""
		else:
			thisrow="""
			<tr class="user" >
				<td class="WhoIsTalking">%s</td>
				<td class="WhatWasSaid">%s</td>
				<td class="userFeedback">
					%s
				</td>
				<td>
					<table class="writtenFeedback">""" %(thischat.orderedLines[el].whoSaidIt, thischat.orderedLines[el].whatWasSaid, str(thischat.orderedLines[el].simpleA))
			for eachFeedback in thischat.orderedLines[el].allComplexFeedback:
				thisrow = thisrow + """<tr class="writtenFeedback"><td class="writtenFeedback">%s</td></tr>""" %(eachFeedback, )
			thisrow=thisrow + """
					</table>
				</td>
			</tr>"""
		tablestring = tablestring + thisrow
	tablestring = tablestring + "</table>"

	htmlString = htmlString + headString + tablestring + "</body></html>"
	print htmlString

			




def multiAdd():
	generateIndexPage()



def individualAdd():
	htmlString=pagestart() + mainnav()
	htmlString=htmlString + """
	<form name="singlesubmit" class="chatsubmission" method="post" action="./page.py">
		<table>
			<tr>
				<td>
					<textarea name="chatlog" cols="90" rows="50"></textarea>
				</td>
				<td>
					<label for="chatid">Chat ID</label>
					<input type="text" id="chatid" name="chatid"><br />
					<input type="submit" name="singleChatSubmitted" value="Submit Chat">
				</td>
			</tr>
		</table>
	</form></body></html>

	"""
	print htmlString

################################################################################
##
##  Submission Processing
##
################################################################################

		
def mainSequence(txt, chatid):
	thischat = parseBlobIntoLines(txt)
	thischat.chatID=chatid
	db=MySQLdb.connect(host=config.MySQLConnection.hostname,user=config.MySQLConnection.username, passwd=config.MySQLConnection.password, db=config.MySQLConnection.dbname)

	cursor = db.cursor()

	cmd = "INSERT INTO maintable (chatid, agent) VALUES (%s, %s)" 
	cursor.execute(cmd, (chatid,thischat.Agent ))
	for each in thischat.lines:
		if ((each.whoSaidIt==thischat.Agent) or (each.whoSaidIt==thischat.Agentfname + " " + thischat.Agentlinitial)):
			whosaid="agent"
		else:
			whosaid="customer"

		cmd = """INSERT INTO interactions (chatid, line, whois, linetext, timefromlastline) VALUES (%s, %s, %s, %s, %s)""" 
		vals = (chatid, '%05d' %int(each.lineNumber), whosaid, each.whatWasSaid, each.timeSinceLastStatement)

		cursor.execute(cmd, (chatid, '%05d' %int(each.lineNumber), whosaid, each.whatWasSaid, each.timeSinceLastStatement))

		cmd2 = """INSERT INTO simplefeedback (chatid, line) VALUES (%s, %s)"""
		cursor.execute(cmd2, (chatid, '%05d' %int(each.lineNumber)))
	generateIndexPage()


def parseBlobIntoLines(txt):
	"""
	This method is intended to take a full text blob and parse it into individual lines
	That said, there are three lines that need special treatment and two additional line
	types that will need consideration

	The lines that need special treatment are the zeroth, the first, and the last line. 
	The line types that will need special treatment are file upload lines, agent transfer lines,
	and "Absent" lines. 
	"""
	#the zeroth line is the line that starts the blob and ends immediatly before the 
	#first instance of [HH:MM:SS [AP]M]
	thischat=Chat()
	zerothLine=re.match(r'(.*)(?=\[[0-9])*',txt,re.M|re.I).group(1)
	txt=txt.replace(zerothLine,"")
	while True:
		if (txt[0]=='\n'):
			txt=txt.replace('\n','',1)
		else:
			break
	##
	## What may happen is that if the attachment may bugger things up, so this should deal with that

	if not (re.match(r'^\[',txt,re.M|re.I)):
		nextbracket = txt.find('[')
		txt=txt[nextbracket:]


	firstlineTimestamp = re.match(r'.*(\[[0-9][0-9]:[0-9][0-9]:[0-9][0-9] [AP]M\]).*',txt,re.M|re.I).group(1)
	##  a=re.match(r'.*([0-9][0-9]):([0-9][0-9]):([0-9][0-9]) ([AP]M\]).*',t1,re.M|re.I)  ##  
	##  a=re.match(r'.*(\[[0-9][0-9]:[0-9][0-9]:[0-9][0-9] [AP]M\]).*',t1,re.M|re.I).group(1)
	txt=txt.replace(firstlineTimestamp,'',1)
	nextTimeStamp=txt.find('\n[')
	firstline = txt[:nextTimeStamp]
	txt=txt.replace(firstline, '', 1)

	thischat.lines.append(convertZerothLine(zerothLine,thischat))
	thischat.Agent=thischat.lines[0].whoSaidIt

	while(len(txt)>0):
		(messageTimeStamp, thisMessage, txt) = getNextLine(txt)
		convertNormalLine(messageTimeStamp, thisMessage, thischat)

	return thischat



def getNextLine(txt):
	"""
	This method will take a large block of text figure out where the next
	full submission ends, and return the next submission and the block of text
	without the next submission
	"""
	if (txt[0]=='\n'):
		txt=txt.replace('\n','',1)
	nextLinesTimeStamp=re.match(r'.*(\[[0-9][0-9]:[0-9][0-9]:[0-9][0-9] [AP]M\])',txt,re.M|re.I).group(1)
	txt=txt.replace(nextLinesTimeStamp,'',1)

	##Find the next "[", make sure that it is part of an actual time stamp. 
	##If it is not, check the next one. etc.  
	##If there are no more '[' assume that this is the end of the interaction. 
	
	nextBracket = txt.find('[')
	if (nextBracket==-1):
		return (nextLinesTimeStamp, txt,'')
	if (re.match(r'(\[[0-9][0-9]:[0-9][0-9]:[0-9][0-9] [AP]M\])',txt[nextBracket:nextBracket+13],re.M|re.I)):
		return (nextLinesTimeStamp, txt[:nextBracket], txt[nextBracket:])
	while True:
		nextBracket = txt.find('[',nextBracket)
		if (re.match(r'(\[[0-9][0-9]:[0-9][0-9]:[0-9][0-9] [AP]M\])',txt[nextBracket:nextBracket+13],re.M|re.I)):
			return (nextLinesTimeStamp, txt[:nextBracket], txt[nextBracket:])

def convertZerothLine(zline, thischat):
	chatStartTime=re.match( r'.*([0-9][0-9])/([0-9][0-9])/([0-9][0-9][0-9][0-9]) ([0-9][0-9]):([0-9][0-9]) ([AP]M)(.*) (.*),.*', zline, re.M|re.I)
	startTime={}
	startTime["month"] = int(chatStartTime.group(1))
	startTime["day"] = int(chatStartTime.group(2))
	startTime["year"] = int(chatStartTime.group(3))
	startTime["hour"] = int(chatStartTime.group(4))
	startTime["minute"] = int(chatStartTime.group(5))
	if (chatStartTime.group(6)=="PM"):
		startTime["hour"] = startTime["hour"] + 12
	agentsName=chatStartTime.group(7) + " " + chatStartTime.group(8)
	thischat.Agentfname = chatStartTime.group(7)
	thischat.Agentlinitial = chatStartTime.group(8)[0]
	startTimeAsObject = datetime.datetime(startTime["year"],startTime["month"],startTime["day"],startTime["hour"],startTime["minute"])
	zerothAsLine=Line(0,agentsName,zline,startTimeAsObject,0)
	return zerothAsLine

def convertFirstLine(thischat, firstlineTimestamp,firstline):
	messageSentTime=re.match(r'.*([0-9][0-9]):([0-9][0-9]):([0-9][0-9]) ([AP]M))', firstlineTimestamp, re.M|re.I)
	messageTime={}
	messageTime["hour"] = int(messageSentTime.group(1))
	messageTime["minute"] = int(messageSentTime.group(2))
	messageTime["second"] = int(messageSentTime.group(3))
	if (messageSentTime.group(4)=="PM"):
		messageTime["hour"] = messageTime["hour"] + 12
	stime = thischat.lines[0].timeItWasSaid
	messageTimeAsObject = datetime.datetime(stime.year, stime.month, stime.day, messageTime["hour"], messageTime["minute"], messageTime["second"])
	timeDifference = messageTimeAsObject - stime
	thischat.lines.append(Line(1,thischat.Agent,firstline,messageTimeAsObject,timeDifference))


def convertNormalLine(chattimeStamp, txt, thischat):
	lineNumber = len(thischat.lines)
	messageSentTime=re.match(r'.*([0-9][0-9]):([0-9][0-9]):([0-9][0-9]) ([AP]M)', chattimeStamp, re.M|re.I)
	messageTime={}
	messageTime["hour"] = int(messageSentTime.group(1))
	messageTime["minute"] = int(messageSentTime.group(2))
	messageTime["second"] = int(messageSentTime.group(3))
	if (messageSentTime.group(4)=="PM"):
		messageTime["hour"] = messageTime["hour"] + 12
	prevTime=thischat.lines[lineNumber-1].timeItWasSaid
	messageTimeAsObject = datetime.datetime(prevTime.year, prevTime.month, prevTime.day, messageTime["hour"], messageTime["minute"], messageTime["second"])
	timeDifference = messageTimeAsObject - prevTime
	txt=txt.strip()
	if(txt.startswith(thischat.Agentfname + " " + thischat.Agentlinitial)):
		whoSaidIt = thischat.Agent
	else:
		whoSaidIt = txt[:txt.find(':')]
	thischat.lines.append(Line(lineNumber,whoSaidIt,txt[txt.find(':'):],messageTimeAsObject,timeDifference))






def updateDatabase(arguments):
	chatid = arguments["thischatid"].value
	totalLines = arguments["linesOfChat"].value
	for x in range(int(totalLines)):
		if arguments.has_key("simple"+str(x)):
			print "Updating simple"
			incrementSimple(chatid, str(x), arguments["simple"+str(x)].value)
		if arguments.has_key("text"+str(x)):
			updateComplex(chatid,str(x),arguments["text"+str(x)].value)
	cumulativePage(chatid)




def incrementSimple(chatid, linesOfChat, value):
	db=MySQLdb.connect(host=config.MySQLConnection.hostname,user=config.MySQLConnection.username, passwd=config.MySQLConnection.password, db=config.MySQLConnection.dbname)
	cur = db.cursor()
	if (value=="pos" or value=="important"):
		stmt="""UPDATE simplefeedback SET counta = counta + 1 WHERE chatid=%s AND line = %s """
	else:
		stmt = """UPDATE simplefeedback SET countb = countb + 1 WHERE chatid =%s AND line = %s """

	cur.execute(stmt, (chatid, linesOfChat))

def updateComplex(chatid, linesOfChat, feedback):
	db=MySQLdb.connect(host=config.MySQLConnection.hostname,user=config.MySQLConnection.username, passwd=config.MySQLConnection.password, db=config.MySQLConnection.dbname)
	cur = db.cursor()
	stmt="""INSERT INTO complexfeedback (chatid, line, complexfeedback) VALUES (%s, %s, %s)"""
	cur.execute(stmt, (chatid, linesOfChat, feedback))


################################################################################
##
##  Various if name is main processes
##
################################################################################


#if __name__ == '__main__':
#	start=random.randint(0,5000)
#	for chat in examples.examples:
#		db=MySQLdb.connect(host=config.MySQLConnection.hostname,user=config.MySQLConnection.username, passwd=config.MySQLConnection.password, db=config.MySQLConnection.dbname)
#		mainSequence(db,chat,start)
#		start+=1


if __name__ == '__main__':
	arguments = cgi.FieldStorage()
	guidingWhereToGo(arguments)

################################################################################
################################################################################
##  Somehow the file was duplicated at the end of itself.  I just noticed this 
## 	and am not sure if I made any changes down here.  I am commenting this out
## 	in case I did work down here and want those changes to be kept.
##
################################################################################
# #!/usr/bin/python

# import config
# import MySQLdb
# import cgi
# import re
# import datetime 
# import random
# import cgitb

# #import examples

# print "Content-type: text/html\n\n"
# cgitb.enable()


# ###############
# ##
# ## Classes
# ##
# ###############


# class Line(object):
# 	def __init__(self, lineNumber, whoSaidIt, whatWasSaid, timeItWasSaid, timeSinceLastStatement):
# 		self.lineNumber=lineNumber
# 		self.whoSaidIt=whoSaidIt
# 		self.whatWasSaid=whatWasSaid
# 		self.timeItWasSaid=timeItWasSaid
# 		self.timeSinceLastStatement=timeSinceLastStatement
# 	def __str__(self):
# 		thisLine= "     Line number: " + str(self.lineNumber) + "\n" +  "             Who: " + self.whoSaidIt + "\n" + "   What was said: " + self.whatWasSaid + '\n' + "When it was said: " + str(self.timeItWasSaid) + '\n'
# 		return thisLine

# class Chat(object):
# 	def __init__(self):
# 		self.Agent=""
# 		self.Agentfname=""
# 		self.Agentlinitial=""
# 		self.Customer=""
# 		self.chatID=""
# 		self.fullLog=""
# 		self.lines=[]


# ################################################################################
# ##
# ##  General "What to do now" logic
# ##
# ################################################################################


# def guidingWhereToGo(arguments):

# 	if (arguments.has_key("chat")):
# 		votingPage(arguments["chat"].value)
# 	elif (arguments.has_key("feedbacksubmit")):
# 		updateDatabase(arguments)
# 	elif (arguments.has_key("singlesubmit")):
# 		individualAdd()
# 	elif (arguments.has_key("multisubmit")):
# 		multiAdd()
# 	elif (arguments.has_key("singleChatSubmitted")):
# 		mainSequence(arguments["chatlog"].value, arguments["chatid"].value)
# 	else:
# 		generateIndexPage()



# ################################################################################
# ##
# ##  Displaying that data
# ##
# ################################################################################
 




# def generateIndexPage():
# 	db=MySQLdb.connect(host=config.MySQLConnection.hostname,user=config.MySQLConnection.username, passwd=config.MySQLConnection.password, db=config.MySQLConnection.dbname)
# 	cur = db.cursor()

# 	myquery = "SELECT * FROM maintable"
# 	cur.execute(myquery)

# 	rows = cur.fetchall()

# 	pagehtml = "<html><head></head><body>"

# 	pagehtml = pagehtml + """
# 	<div class="buttons">
# 		<form class="addchats" name="addchats" method="post" action="./page.py">
# 			<input type="submit" name="singlesubmit" value="Submit a single chat">
# 			<input type="submit" name="multisubmit" value="Submit multiple chats">
# 		</form>
# 	</div>

# 	"""

# 	addtable = "<table>"
# 	closetable = "</table>"
# 	tableRow="<tr>"
# 	closeTableRow="</tr>"
# 	closeBody="</body></html>"

# 	pagehtml = pagehtml + addtable
# 	pagehtml = pagehtml + tableRow
# 	pagehtml = pagehtml + "<td>ChatID</td><td>Agent</td>" + closeTableRow 



# 	for row in rows:
# 		pagehtml = pagehtml + tableRow + """<td><a href="./page.py?chat=%s">""" %(row[0]) + row[0] + """</a></td><td>""" + row[2] + "</td>" + closeTableRow
# 	pagehtml = pagehtml + closetable + closeBody

# 	print pagehtml

# def votingPage(chatid):
# 	db=MySQLdb.connect(host=config.MySQLConnection.hostname,user=config.MySQLConnection.username, passwd=config.MySQLConnection.password, db=config.MySQLConnection.dbname)
# 	cur=db.cursor()

# 	myquery = "SELECT * FROM interactions WHERE chatid ='%s' ORDER BY line" %(chatid)
# 	cur.execute(myquery)

# 	rows = cur.fetchall()
# 	totalLines=len(rows)

# 	htmlString="""<html><head></head><body><form class="feedback" name="%s" method="post" c><table class="chatRecord" border="1"><tr class="heading"><td>Who</td><td>What Was Said</td><td>Simple Feedback</td><td>Complex Feedback</td></tr>""" %(chatid)
# 	htmlString = htmlString + """ <input type="hidden" name="thischatid" value="%s"> <input type="hidden" name="linesOfChat" value="%s">""" %(chatid, totalLines)
# 	for row in rows:
# 		if (row[2] == "'agent'"):
# 			htmlString=htmlString + """
# 			<tr class="agent" >
# 				<td class="WhoIsTalking">%s</td>
# 				<td class="WhatWasSaid">%s</td>
# 				<td>
# 					<table class="agentButtons">
# 						<tr>
# 							<td class="posButton">
# 								<input type="radio" name="%s" value="pos">
# 							</td>
# 						</tr>
# 						<tr>
# 							<td class="negButton">
# 								<input type="radio" name="%s" value="neg">
# 							</td>
# 						</tr>
# 					</table>
# 				</td>
# 				<td>
# 					<input type="textarea" name="%s" cols="40" rows="5"></textarea>
# 				</td>
# 			</tr>""" %(row[2], row[3], "simple"+row[1], "simple"+row[1], "text"+row[1])
# 		else:
# 			htmlString = htmlString+"""
# 			<tr class="user" >
# 				<td class="WhoIsTalking">%s</td>
# 				<td class="WhatWasSaid">%s</td>
# 				<td class="userButton">
# 					<input type="radio" name="%s" value="important">
# 				</td>
# 				<td>
# 					<input type="textarea" name="%s"ols="40" rows="5"></textarea>
# 				</td>
# 			</tr>""" %(row[2], row[3], "simple"+row[1],"text"+row[1])
# 	htmlString=htmlString + """
# 		</table> <input type="submit" name="feedbacksubmit" value="submit"></form></body></html>"""
# 	print htmlString

# def cumulativePage(chatid):
# 	print"comingsoon!"
# def individualAdd():
# 	htmlString="<html><head></head><body>"
# 	htmlString="""
# 	<form name="singlesubmit" class="chatsubmission" method="post" action="./page.py">
# 		<table>
# 			<tr>
# 				<td>
# 					<textarea name="chatlog" cols="90" rows="50"></textarea>
# 				</td>
# 				<td>
# 					<label for="chatid">Chat ID</label>
# 					<input type="text" id="chatid" name="chatid"><br />
# 					<input type="submit" name="singleChatSubmitted" value="Submit Chat">
# 				</td>
# 			</tr>
# 		</table>
# 	</form></body></html>

# 	"""
# 	print htmlString

# ################################################################################
# ##
# ##  Submission Processing
# ##
# ################################################################################

		
# def mainSequence(txt, chatid):
# 	thischat = parseBlobIntoLines(txt)
# 	thischat.chatID=chatid
# 	db=MySQLdb.connect(host=config.MySQLConnection.hostname,user=config.MySQLConnection.username, passwd=config.MySQLConnection.password, db=config.MySQLConnection.dbname)

# 	cursor = db.cursor()
# 	print txt

# 	cmd = "INSERT INTO maintable (chatid, agent) VALUES (%s, %s)" 
# 	cursor.execute(cmd, (chatid,thischat.Agent ))
# 	for each in thischat.lines:
# 		if ((each.whoSaidIt==thischat.Agent) or (each.whoSaidIt==thischat.Agentfname + " " + thischat.Agentlinitial)):
# 			whosaid="agent"
# 		else:
# 			whosaid="customer"

# 		cmd = """INSERT INTO interactions (chatid, line, whois, linetext, timefromlastline) VALUES (%s, %s, %s, %s, %s)""" 
# 		vals = (chatid, str(each.lineNumber), whosaid, each.whatWasSaid, each.timeSinceLastStatement)

# 		cursor.execute(cmd, (chatid, each.lineNumber, whosaid, each.whatWasSaid, each.timeSinceLastStatement))

# 		cmd2 = """INSERT INTO simplefeedback (chatid, line) VALUES (%s, %s)"""
# 		cursor.execute(cmd2, (chatid, str(each.lineNumber)))


# def parseBlobIntoLines(txt):
# 	"""
# 	This method is intended to take a full text blob and parse it into individual lines
# 	That said, there are three lines that need special treatment and two additional line
# 	types that will need consideration

# 	The lines that need special treatment are the zeroth, the first, and the last line. 
# 	The line types that will need special treatment are file upload lines, agent transfer lines,
# 	and "Absent" lines. 
# 	"""
# 	#the zeroth line is the line that starts the blob and ends immediatly before the 
# 	#first instance of [HH:MM:SS [AP]M]
# 	thischat=Chat()
# 	zerothLine=re.match(r'(.*)(?=\[[0-9])*',txt,re.M|re.I).group(1)
# 	txt=txt.replace(zerothLine,"")
# 	while True:
# 		if (txt[0]=='\n'):
# 			txt=txt.replace('\n','',1)
# 		else:
# 			break
# 	##
# 	## What may happen is that if the attachment may bugger things up, so this should deal with that

# 	if not (re.match(r'^\[',txt,re.M|re.I)):
# 		nextbracket = txt.find('[')
# 		txt=txt[nextbracket:]


# 	firstlineTimestamp = re.match(r'.*(\[[0-9][0-9]:[0-9][0-9]:[0-9][0-9] [AP]M\]).*',txt,re.M|re.I).group(1)
# 	##  a=re.match(r'.*([0-9][0-9]):([0-9][0-9]):([0-9][0-9]) ([AP]M\]).*',t1,re.M|re.I)  ##  
# 	##  a=re.match(r'.*(\[[0-9][0-9]:[0-9][0-9]:[0-9][0-9] [AP]M\]).*',t1,re.M|re.I).group(1)
# 	txt=txt.replace(firstlineTimestamp,'',1)
# 	nextTimeStamp=txt.find('\n[')
# 	firstline = txt[:nextTimeStamp]
# 	txt=txt.replace(firstline, '', 1)

# 	thischat.lines.append(convertZerothLine(zerothLine,thischat))
# 	thischat.Agent=thischat.lines[0].whoSaidIt

# 	while(len(txt)>0):
# 		(messageTimeStamp, thisMessage, txt) = getNextLine(txt)
# 		convertNormalLine(messageTimeStamp, thisMessage, thischat)

# 	return thischat



# def getNextLine(txt):
# 	"""
# 	This method will take a large block of text figure out where the next
# 	full submission ends, and return the next submission and the block of text
# 	without the next submission
# 	"""
# 	if (txt[0]=='\n'):
# 		txt=txt.replace('\n','',1)
# 	nextLinesTimeStamp=re.match(r'.*(\[[0-9][0-9]:[0-9][0-9]:[0-9][0-9] [AP]M\])',txt,re.M|re.I).group(1)
# 	txt=txt.replace(nextLinesTimeStamp,'',1)

# 	##Find the next "[", make sure that it is part of an actual time stamp. 
# 	##If it is not, check the next one. etc.  
# 	##If there are no more '[' assume that this is the end of the interaction. 
	
# 	nextBracket = txt.find('[')
# 	if (nextBracket==-1):
# 		return (nextLinesTimeStamp, txt,'')
# 	if (re.match(r'(\[[0-9][0-9]:[0-9][0-9]:[0-9][0-9] [AP]M\])',txt[nextBracket:nextBracket+13],re.M|re.I)):
# 		return (nextLinesTimeStamp, txt[:nextBracket], txt[nextBracket:])
# 	while True:
# 		nextBracket = txt.find('[',nextBracket)
# 		if (re.match(r'(\[[0-9][0-9]:[0-9][0-9]:[0-9][0-9] [AP]M\])',txt[nextBracket:nextBracket+13],re.M|re.I)):
# 			return (nextLinesTimeStamp, txt[:nextBracket], txt[nextBracket:])

# def convertZerothLine(zline, thischat):
# 	chatStartTime=re.match( r'.*([0-9][0-9])/([0-9][0-9])/([0-9][0-9][0-9][0-9]) ([0-9][0-9]):([0-9][0-9]) ([AP]M)(.*) (.*),.*', zline, re.M|re.I)
# 	startTime={}
# 	startTime["month"] = int(chatStartTime.group(1))
# 	startTime["day"] = int(chatStartTime.group(2))
# 	startTime["year"] = int(chatStartTime.group(3))
# 	startTime["hour"] = int(chatStartTime.group(4))
# 	startTime["minute"] = int(chatStartTime.group(5))
# 	if (chatStartTime.group(6)=="PM"):
# 		startTime["hour"] = startTime["hour"] + 12
# 	agentsName=chatStartTime.group(7) + " " + chatStartTime.group(8)
# 	thischat.Agentfname = chatStartTime.group(7)
# 	thischat.Agentlinitial = chatStartTime.group(8)[0]
# 	startTimeAsObject = datetime.datetime(startTime["year"],startTime["month"],startTime["day"],startTime["hour"],startTime["minute"])
# 	zerothAsLine=Line(0,agentsName,zline,startTimeAsObject,0)
# 	return zerothAsLine

# def convertFirstLine(thischat, firstlineTimestamp,firstline):
# 	messageSentTime=re.match(r'.*([0-9][0-9]):([0-9][0-9]):([0-9][0-9]) ([AP]M))', firstlineTimestamp, re.M|re.I)
# 	messageTime={}
# 	messageTime["hour"] = int(messageSentTime.group(1))
# 	messageTime["minute"] = int(messageSentTime.group(2))
# 	messageTime["second"] = int(messageSentTime.group(3))
# 	if (messageSentTime.group(4)=="PM"):
# 		messageTime["hour"] = messageTime["hour"] + 12
# 	stime = thischat.lines[0].timeItWasSaid
# 	messageTimeAsObject = datetime.datetime(stime.year, stime.month, stime.day, messageTime["hour"], messageTime["minute"], messageTime["second"])
# 	timeDifference = messageTimeAsObject - stime
# 	thischat.lines.append(Line(1,thischat.Agent,firstline,messageTimeAsObject,timeDifference))


# def convertNormalLine(chattimeStamp, txt, thischat):
# 	lineNumber = len(thischat.lines)
# 	messageSentTime=re.match(r'.*([0-9][0-9]):([0-9][0-9]):([0-9][0-9]) ([AP]M)', chattimeStamp, re.M|re.I)
# 	messageTime={}
# 	messageTime["hour"] = int(messageSentTime.group(1))
# 	messageTime["minute"] = int(messageSentTime.group(2))
# 	messageTime["second"] = int(messageSentTime.group(3))
# 	if (messageSentTime.group(4)=="PM"):
# 		messageTime["hour"] = messageTime["hour"] + 12
# 	prevTime=thischat.lines[lineNumber-1].timeItWasSaid
# 	messageTimeAsObject = datetime.datetime(prevTime.year, prevTime.month, prevTime.day, messageTime["hour"], messageTime["minute"], messageTime["second"])
# 	timeDifference = messageTimeAsObject - prevTime
# 	txt=txt.strip()
# 	if(txt.startswith(thischat.Agentfname + " " + thischat.Agentlinitial)):
# 		whoSaidIt = thischat.Agent
# 	else:
# 		whoSaidIt = txt[:txt.find(':')]
# 	thischat.lines.append(Line(lineNumber,whoSaidIt,txt[txt.find(':'):],messageTimeAsObject,timeDifference))






# def updateDatabase(arguments):
# 	chatid = arguments["thischatid"].value
# 	totalLines = arguments["linesOfChat"].value

# 	for x in range(int(totalLines)):
# 		if arguments.has_key("simple"+str(x)):
# 			incrementSimple(chatid, str(x), arguments["simple"+str(x)].value)
# 		if arguments.has_key("text"+str(x)):
# 			updateComplex(chatid,str(x),arguments["text"+str(x)].value)




# def incrementSimple(chatid, linesOfChat, value):
# 	db=MySQLdb.connect(host=config.MySQLConnection.hostname,user=config.MySQLConnection.username, passwd=config.MySQLConnection.password, db=config.MySQLConnection.dbname)
# 	cur = db.cursor()
# 	if (value=="pos" or value=="important"):
# 		stmt="""UPDATE simplefeedback SET counta = counta + 1 WHERE chatid="%s" AND line = "%s" """
# 	else:
# 		stmt = """UPDATE simplefeedback SET countb = countb + 1 WHERE chatid ="%s" AND line = "%s" """

# 	cur.execute(stmt, (chatid, linesOfChat))

# def updateComplex(chatid, linesOfChat, feedback):
# 	db=MySQLdb.connect(host=config.MySQLConnection.hostname,user=config.MySQLConnection.username, passwd=config.MySQLConnection.password, db=config.MySQLConnection.dbname)
# 	cur = db.cursor()
# 	stmt="""INSERT INTO complexfeedback (chatid, line, complexfeedback) VALUES (%s, %s, %s)"""
# 	cur.execute(stmt, (chatid, linesOfChat, feedback))


# ################################################################################
# ##
# ##  Various if name is main processes
# ##
# ################################################################################


# #if __name__ == '__main__':
# #	start=random.randint(0,5000)
# #	for chat in examples.examples:
# #		db=MySQLdb.connect(host=config.MySQLConnection.hostname,user=config.MySQLConnection.username, passwd=config.MySQLConnection.password, db=config.MySQLConnection.dbname)
# #		mainSequence(db,chat,start)
# #		start+=1


# if __name__ == '__main__':
# 	arguments = cgi.FieldStorage()
# 	guidingWhereToGo(arguments)


