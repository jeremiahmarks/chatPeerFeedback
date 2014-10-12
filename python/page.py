#!/usr/bin/python




import MySQLdb
import cgi
import re
import datetime
import xmlrpclib
#import random
import cgitb
#import config



################################################################################
##
## Important stuff that should be easy to change
##
################################################################################
	############################################################################
	## Database Settings
	############################################################################
mysqlhostname=""
mysqlusername=""
mysqlpassword=""
mysqldbname=""
	############################################################################
	## Path to this file for email
	############################################################################
urltothisfile=""
	############################################################################
	## Infusiont particular Settings
	############################################################################
infusionsoftapp=""
infusionsoftAPIKey=""
tagID=395   #This is the tag that is associated with people who should recieve the emails for peer feedback
fromAddress = ""
	############################################################################
	##  Time Thresholds
	############################################################################
timeGreen = 90
timeYellow=240

print "Content-type: text/html\n\n"
cgitb.enable()


################################################################################
##
## Classes
##
################################################################################


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

class ISServer:
	global infusionsoftapp
	global infusionsoftAPIKey
	global tagID
	global fromAddress

	def __init__(self):
		self.appurl = "https://" + infusionsoftapp+".infusionsoft.com:443/api/xmlrpc"
		self.connection = xmlrpclib.ServerProxy(self.appurl)

	def sendEmail(self, emailBody):
		"""
		This method will take the body of an email and mail it to all contacts
		who have the tag "ChatSupport" and email addresses that end in @infusionsoft.com
		"""
		contactList = self.getContacts()
		toAddress='~Contact.Email~'
		ccAddress=''
		bccAddress=''
		contentType="HTML"
		subject="Please Provide Feedback"
		htmlBody=emailBody
		textBody=''
		self.connection.APIEmailService.sendEmail(infusionsoftAPIKey, contactList, fromAddress, toAddress, ccAddress, bccAddress, contentType, subject, htmlBody, textBody)


	def getContacts(self):
		desiredResults=[]
		listOfDicts = self.connection.DataService.query(infusionsoftAPIKey, "ContactGroupAssign", 1000,0,{'GroupId':395},['ContactId'],"ContactId", True )
		for eachEntry in listOfDicts:
			desiredResults.append(eachEntry['ContactId'])
		return desiredResults

	def addContact(self, fname, email):
		newContact={}
		newContact["FirstName"]=fname
		#newContact["LastName"]=lname
		newContact["Email"]=email

		thiscontact = self.connection.ContactService.add(infusionsoftAPIKey, newContact)
		self.connection.ContactService.addToGroup(infusionsoftAPIKey, thiscontact, tagID)
		self.connection.APIEmailService.optIn(infusionsoftAPIKey, email, "This email was opted in to recieve notifications regarding peer feedback")






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
	elif (arguments.has_key("emailRecent")):
		emailUpdates()
	elif (arguments.has_key("signup")):
		server=ISServer()
		server.addContact(arguments['Name'].value, arguments['Email'].value)
		generateIndexPage()
	elif (arguments.has_key("deleteData")):
		dropall()
	else:
		generateIndexPage()

################################################################################
##
## MySQLdb connection Generator
##
################################################################################

def databaseConnection():
	global mysqlhostname
	global mysqlusername
	global mysqlpassword
	global mysqldbname
	return MySQLdb.connect(host=mysqlhostname, user=mysqlusername, passwd=mysqlpassword, db=mysqldbname )

################################################################################
##  _____                    _____                           _   _
## |  __ \                  / ____|                         | | (_)
## | |__) |_ _  __ _  ___  | |  __  ___ _ __   ___ _ __ __ _| |_ _  ___  _ __
## |  ___/ _` |/ _` |/ _ \ | | |_ |/ _ \ '_ \ / _ \ '__/ _` | __| |/ _ \| '_ \
## | |  | (_| | (_| |  __/ | |__| |  __/ | | |  __/ | | (_| | |_| | (_) | | | |
## |_|   \__,_|\__, |\___|  \_____|\___|_| |_|\___|_|  \__,_|\__|_|\___/|_| |_|
##              __/ |
##             |___/
################################################################################

	############################################################################
	##
	## Elements that will be used throughout the site
	##
	############################################################################
def mainnav():
	navstr="""	<div class="nav">
					<form class="addchats" name="addchats" method="post" action="./page">
						<input type="submit" name="singlesubmit" value="Submit a single chat">
						<!-- <input type="submit" name="multisubmit" value="Submit multiple chats"> -->
						<input type="submit" name="goindex" value="Return to the Index Page">
						<input type="submit" name="emailRecent" value="Email Recent Updates">
						<input type="submit" name="deleteData" value="delete">
						<div class="signupForNotifications">
							<label for="Name">Name:</label>
							<input type="text" id="Name" name="Name" />
							<label for="Email">Email: </label>
							<input type="text" id="Email" name="Email">
							<input type="submit" name="signup" value="Signup" />
						</div>

					</form>
				</div>
	"""
	return navstr

def pagestart(pagetitle="InfusionSoft Chat PeerFeedback"):
	startstr="""
		<html>
			<head>
				<title>%s</title>
                                <script type='text/javascript' src='http://code.jquery.com/jquery-git2.js'></script>

				<style>
					body, button, input, select, textarea {
    					background-color: #333;
    					color: #fff;
    					font-family: Arial,Helvetica,sans-serif;
					    font-size: 1.3rem;
					    line-height: 1.5;
					}
					input[type="checkbox"]{
						display:none;

					}
					input[type="checkbox"].positive + label {
						display:inline-block;
						cursor:pointer;
						background-image: url("../images/gray_arrow_up.png");
						background-repeat: no repeat;
						background-size: 20px 20px;
						height: 20px;
						width: 20px;
					}
					input[type="checkbox"].positive:checked + label {
						background-image: url("../images/green_arrow_up.png");


					}
					input[type="checkbox"].negative + label {
						display:inline-block;
						cursor:pointer;
						background-image: url("../images/gray_arrow_down.png");
						background-repeat: no repeat;
						background-size: 20px 20px;
						height: 20px;
						width: 20px;
					}
					input[type="checkbox"].negative:checked + label {
						background-image: url("../images/red_arrow_down.png");


					}
					input[type="checkbox"].important + label {
						display:inline-block;
						cursor:pointer;
						background-image: url("../images/gray_important_icon.png");
						background-repeat: no repeat;
						background-size: 20px 20px;
						height: 20px;
						width: 20px;
					}
					input[type="checkbox"].important:checked + label {
						background-image: url("../images/important_icon.png");


					}

					.Green{
						background-color: Green;
					}
					.Yellow{
						background-color: Yellow;
					}
					.Red{
						background-color: Red;
					}
					.timebeteenchats{
						color: #000;
						text-align: center;
					}

				</style>
                                <script language="javascript" type="text/javascript">
                                $(window).load(function(){
                                    $("input:checkbox").click(function() {
                                        if ($(this).is(":checked")) {
                                            var group = "input:checkbox[name='" + $(this).attr("name") + "']";
                                            $(group).prop("checked", false);
                                            $(this).prop("checked", true);
                                        } else {
                                            $(this).prop("checked", false);
                                        }
                                    });
                                });


                                </script>
			</head>
			<body>""" %(pagetitle)
	return startstr

	############################################################################
	##
	##	These are the actual pages that are used in the site
	##
	############################################################################
		##  _____               _                   _____
		## |_   _|             | |                 |  __ \      /\
		##   | |    _ __     __| |   ___  __  __   | |__) |    /  \      __ _    ___
		##   | |   | '_ \   / _` |  / _ \ \ \/ /   |  ___/    / /\ \    / _` |  / _ \
		##  _| |_  | | | | | (_| | |  __/  >  <    | |       / ____ \  | (_| | |  __/
		## |_____| |_| |_|  \__,_|  \___| /_/\_\   |_|      /_/    \_\  \__, |  \___|
		##                                                               __/ |
		##                                                              |___/
def generateIndexPage():
	"""
	This method is used for generally building and displaying a simple index page
	of all of the chats that have been submitted previously.
	"""
	db=databaseConnection()
	cur = db.cursor()

	myquery = "SELECT * FROM maintable"
	cur.execute(myquery)

	rows = cur.fetchall()

	pagehtml = pagestart() + mainnav()


	pagehtml = pagehtml + """<table>
								<tr>
									<td width="200">ChatID</td>
									<!-- <td>Agent</td> -->
									<td width="200">Date Uploaded</td>
									<td width="200">Provide Feedback</td>
									<td width="200">View feedback</td>
								</tr>"""

	for row in rows:
		pagehtml = pagehtml + """	<tr>
								<td class="chatid">%s</td>
								<td class="dateUploaded">%s</td>
								<td class="providefeedback"><a href="%s">Provide Feedback</td>
								<td class="viewfeedback"><a href="%s">View Feedback</td>
							</tr> """ %(row[0], row[1], urltothisfile + "?chat=" + row[0], urltothisfile + "?chat=" + row[0] + "&mode=view")

	pagehtml = pagehtml + """</table></body>"""

	print pagehtml
		########################################################################
		##	This page collects feedback on chats
		########################################################################
def votingPage(chatid):
	"""
	This page is used to collect feedback on a chat record.
	"""
	global timeGreen
	global timeYellow

	db=databaseConnection()
	cur=db.cursor()
	agentQuery = "SELECT agent FROM maintable WHERE chatid ='%s'" %(chatid)
	cur.execute(agentQuery)
	name=cur.fetchall()
	fullname=name[0][0]
	fname=fullname.split()[0]



	myquery = "SELECT * FROM interactions WHERE chatid ='%s' ORDER BY line" %(chatid)
	cur.execute(myquery)

	rows = cur.fetchall()
	totalLines=len(rows)

	htmlString= pagestart() + mainnav()
	htmlString = htmlString + 	"""<form class="feedback" name="%s" method="post" action="./page">
										<table class="chatRecord" border="1">
											<tr class="heading">
												<td>Who</td>
												<td>What Was Said</td>
												<td>Simple Feedback</td>
												<td>Complex Feedback</td>
											</tr>""" %(chatid)
	htmlString = htmlString + """ 	<input type="hidden" name="thischatid" value="%s">
									<input type="hidden" name="linesOfChat" value="%s">""" %(chatid, totalLines)
	for row in rows:
		thistext = row[3].replace(fullname, "Agent")
		thistext = thistext.replace(fname, "Agent")
		if (row[4]=="0"):
			totalSeconds=0
		else:
			hoursString, minutesString, secondsString = row[4][2:].split(':')
			hours=int(hoursString)
			minutes=int(minutesString)
			seconds=int(secondsString)
			totalSeconds = seconds+minutes*60+hours*3600

		if (totalSeconds<timeGreen):
			timeClass="Green"
		elif (totalSeconds<timeYellow):
			timeClass="Yellow"
		else:
			timeClass="Red"


		if (row[1] == "%05d" %(1) or row[1]=="%05d" %(0)):
			htmlString=htmlString + """

			<tr class="agent" >
				<td class="WhoIsTalking">%s</td>
				<td class="WhatWasSaid">%s</td>
				<td>
					<table class="agentButtons">
						<tr>
							<td class="posButton">
								<input class="positive" type="checkbox" name="%s" value="pos" id="%s" />
								<label for="%s"><!-- <img src="../images/gray_arrow_up.png" height="20px" width="20px" /> --></label>
							</td>
						</tr>
						<tr>
							<td class="negButton">
								<input class="negative" type="checkbox" name="%s" value="neg" id="%s" />
								<label for="%s"></label>
							</td>
						</tr>
					</table>
				</td>
				<td>
					<input type="textarea" name="%s" cols="40" rows="5"></textarea>
				</td>
			</tr>""" %(row[2], thistext, "simple"+row[1],"pos"+row[1], "pos"+row[1], "simple"+row[1],"neg"+row[1],"neg"+row[1], "text"+row[1])

		elif (row[2] == "agent"):
			htmlString=htmlString + """
			<tr class="timebeteenchats"><td colspan="4" class="%s">%s</td></tr>
			<tr class="agent" >
				<td class="WhoIsTalking">%s</td>
				<td class="WhatWasSaid">%s</td>
				<td>
					<table class="agentButtons">
						<tr>
							<td class="posButton">
								<input class="positive" type="checkbox" name="%s" value="pos" id="%s" />
								<label for="%s"><!-- <img src="../images/gray_arrow_up.png" height="20px" width="20px" /> --></label>
							</td>
						</tr>
						<tr>
							<td class="negButton">
								<input class="negative" type="checkbox" name="%s" value="neg" id="%s" />
								<label for="%s"></label>
							</td>
						</tr>
					</table>
				</td>
				<td>
					<input type="textarea" name="%s" cols="40" rows="5"></textarea>
				</td>
			</tr>
			   """ %(timeClass, row[4], row[2], thistext, "simple"+row[1],"pos"+row[1], "pos"+row[1], "simple"+row[1],"neg"+row[1],"neg"+row[1], "text"+row[1])
		else:
			htmlString = htmlString+"""
			<tr class="timebeteenchats"><td class="%s" colspan="4">%s</td></tr>
			<tr class="user" >
				<td class="WhoIsTalking">%s</td>
				<td class="WhatWasSaid">%s</td>
				<td class="userButton">
					<input class="important" type="checkbox" name="%s" value="important" id="%s">
					<label for="%s"></label>
				</td>
				<td>
					<input type="textarea" name="%s"ols="40" rows="5"></textarea>
				</td>
			</tr>
			""" %(timeClass, row[4], row[2], thistext , "simple"+row[1], "important"+row[1], "important"+row[1], "text"+row[1])
	htmlString=htmlString + """
		</table>
		<input type="submit" name="feedbacksubmit" value="submit">
	</form>
</body>
</html>"""
	print htmlString
		########################################################################
		##	This page displays a chats cumulative feedback
		########################################################################
def cumulativePage(chatid):
	"""
	This page is used to display the cumulative results of one particular chat
	record
	"""
	thischat = Chat()


	tables = ["complexfeedback", 'interactions', 'maintable', 'simplefeedback']

	pageinformation={}

	for eachtable in tables:
		db=databaseConnection()
		cur=db.cursor()
		if (eachtable=="maintable"):
			thisquery = """SELECT * FROM %s WHERE chatid="%s" """ %(eachtable, chatid)
		else:
			thisquery = """SELECT * FROM %s WHERE chatid = "%s" ORDER BY line""" %(eachtable, chatid)
		cur.execute(thisquery)
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
		########################################################################
		##	This page will eventually all a user to enter more than one chat at
		##	a time
		########################################################################
def multiAdd():
	generateIndexPage()
		########################################################################
		##	This page allows a user to enter a chat for feedback
		########################################################################
def individualAdd():
	htmlString=pagestart() + mainnav()
	htmlString=htmlString + """
	<form name="singlesubmit" class="chatsubmission" method="post" action="./page">
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
	############################################################################
	##The main logic behind the process
	############################################################################
def mainSequence(txt, chatid):
	thischat = parseBlobIntoLines(txt)
	thischat.chatID=chatid
	db=databaseConnection()

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
		########################################################################
		##	Takes an entire chat interaction and returns a series of Lines
		########################################################################
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
	## What may happen is that the attachment may bugger things up, so this should deal with that
	if not (re.match(r'^\[',txt,re.M|re.I)):
		nextbracket = txt.find('[')
		txt=txt[nextbracket:]

	firstlineTimestamp = re.match(r'.*(\[[0-9][0-9]:[0-9][0-9]:[0-9][0-9] [AP]M\]).*',txt,re.M|re.I).group(1)
	## I am keeping these re expressions because I don't understand RE and they
	##	may be helpful to figure another solution
	##  a=re.match(r'.*([0-9][0-9]):([0-9][0-9]):([0-9][0-9]) ([AP]M\]).*',t1,re.M|re.I)  ##
	##  a=re.match(r'.*(\[[0-9][0-9]:[0-9][0-9]:[0-9][0-9] [AP]M\]).*',t1,re.M|re.I).group(1)
	txt=txt.replace(firstlineTimestamp,'',1)
	nextTimeStamp=txt.find('\n[')
	firstline = txt[:nextTimeStamp]
	txt=txt.replace(firstline, '', 1)

	thischat.lines.append(convertZerothLine(zerothLine,thischat))
	thischat.Agent=thischat.lines[0].whoSaidIt
	thischat.lines.append(convertFirstLine(thischat, txt[:14],firstline))



	while(len(txt)>0):
		(messageTimeStamp, thisMessage, txt) = getNextLine(txt)
		convertNormalLine(messageTimeStamp, thisMessage, thischat)

	return thischat
		########################################################################
		##	This method breaks off the next interaction and returns two peices
		########################################################################
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

	nextBracket = txt.find('[')
	if (nextBracket==-1):
		return (nextLinesTimeStamp, txt,'')
	if (re.match(r'(\[[0-9][0-9]:[0-9][0-9]:[0-9][0-9] [AP]M\])',txt[nextBracket:nextBracket+13],re.M|re.I)):
		return (nextLinesTimeStamp, txt[:nextBracket], txt[nextBracket:])
	while True:
		nextBracket = txt.find('[',nextBracket)
		if (re.match(r'(\[[0-9][0-9]:[0-9][0-9]:[0-9][0-9] [AP]M\])',txt[nextBracket:nextBracket+13],re.M|re.I)):
			return (nextLinesTimeStamp, txt[:nextBracket], txt[nextBracket:])
		########################################################################
		##	This converts the very first line of text into the table
		########################################################################
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

	#zline = zline.replace(agentsName, "Agent")

	startTimeAsObject = datetime.datetime(startTime["year"],startTime["month"],startTime["day"],startTime["hour"],startTime["minute"])
	zerothAsLine=Line(0,agentsName,zline,startTimeAsObject,0)

	return zerothAsLine
		########################################################################
		##	Since the second line that is recorded is also different from the
		##	rest of the chat, this method deals with that line
		########################################################################
def convertFirstLine(thischat, firstlineTimestamp,firstline):
	firstlineTimestamp=firstlineTimestamp.replace('\n','')
	messageSentTime=re.match(r'.*([0-9][0-9]):([0-9][0-9]):([0-9][0-9]) ([AP]M)', firstlineTimestamp, re.M|re.I)
	messageTime={}
	messageTime["hour"] = int(messageSentTime.group(1))
	messageTime["minute"] = int(messageSentTime.group(2))
	messageTime["second"] = int(messageSentTime.group(3))
	if (messageSentTime.group(4)=="PM"):
		messageTime["hour"] = messageTime["hour"] + 12
	stime = thischat.lines[0].timeItWasSaid
	messageTimeAsObject = datetime.datetime(stime.year, stime.month, stime.day, messageTime["hour"], messageTime["minute"], messageTime["second"])
	timeDifference = messageTimeAsObject - stime
	return Line(1,thischat.Agent,firstline,messageTimeAsObject,timeDifference)
	#thischat.lines.append(Line(1,thischat.Agent,firstline,messageTimeAsObject,timeDifference))
		########################################################################
		##	Most of the rest of the lines are about the same, this method deals
		##	with them
		########################################################################
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
		########################################################################
		##  This method parses feedback and sends each feedback to the
		## 	appropriate place for it to get updated
		########################################################################
def updateDatabase(arguments):
	chatid = arguments["thischatid"].value
	totalLines = arguments["linesOfChat"].value
	for x in range(int(totalLines)):

		if arguments.has_key("simple"+str("%05d" %x)):
			print "Updating simple"
			incrementSimple(chatid, str("%05d" %x), arguments["simple"+str("%05d" %x)].value)
		if arguments.has_key("text"+str("%05d" %x)):
			updateComplex(chatid, str("%05d" %x),arguments["text"+str("%05d" %x)].value)
	cumulativePage(chatid)
		########################################################################
		##	This method increments the simple feedback mechanism
		########################################################################
def incrementSimple(chatid, linesOfChat, value):
	db=databaseConnection()
	cur = db.cursor()
	if (value=="pos" or value=="important"):
		stmt="""UPDATE simplefeedback SET counta = counta + 1 WHERE chatid="%s" AND line = "%s" """ %(chatid, linesOfChat)

	else:
		stmt = """UPDATE simplefeedback SET countb = countb + 1 WHERE chatid ="%s" AND line = "%s" """ %(chatid, linesOfChat)

	cur.execute(stmt)
		########################################################################
		##	This method updates the written feedback section
		########################################################################
def updateComplex(chatid, linesOfChat, feedback):
	db=databaseConnection()
	cur = db.cursor()
	stmt="""INSERT INTO complexfeedback (chatid, line, complexfeedback) VALUES (%s, %s, %s)"""
	cur.execute(stmt, (chatid, linesOfChat, feedback))

	############################################################################
	##
	##  This function clears the tables data
	##
	############################################################################
def dropall():
	tables = ["complexfeedback", 'interactions', 'maintable', 'simplefeedback']
	db = databaseConnection()
	cur = db.cursor()

	for eachtable in tables:
		stmt="""TRUNCATE TABLE %s;""" %(eachtable)
		cur.execute(stmt)
	print "all dropped"
	generateIndexPage()
################################################################################
##
## The email script
##
################################################################################
def emailUpdates():
	global urltothisfile
	db=databaseConnection()
	firstQuery = """SELECT COUNT(*) FROM emailed WHERE DATE_SUB(NOW(), INTERVAL 23 HOUR) <= sent"""
	thiscur=db.cursor()
	thiscur.execute(firstQuery)
	if (thiscur.fetchall()[0][0]>0):
		print pagestart()+mainnav()+"""<h1>I am sorry, an email as been sent in the last 23 hours and you cannot send one now.</h1></body></html>"""
	else:
		iserver=ISServer()
		secondQuery = """SELECT * FROM maintable WHERE DATE_SUB(NOW(), INTERVAL 24 HOUR) <= uploaded"""
		thiscur.execute(secondQuery)
		allRows = thiscur.fetchall()
		htmlList="""
		<table>
		"""
		for each in allRows:
			htmlList=htmlList+"""<tr>
									<td>%s</td>
									<td>%s</td>
									<td>
										<a href="%spage?chat=%s">Provide Feedback</a>
									</td>
									<td>
										<a href="%spage?chat=%s&mode=view">View Feedback</a>
									</td>
								</tr>""" %(each[0], each[2], urltothisfile, each[0], urltothisfile, each[0])
		htmlList=htmlList+"""</table>"""

		emailbody = emailTop() + htmlList + emailbottom()
		iserver.sendEmail(emailbody)
		generateIndexPage()
def emailTop():
	htmlString="""
	<html>
		<head>
		</head>
		<body style="background-color: #333; color: #fff; font-family: Arial,Helvetica,sans-serif;">
			<h1>Hello ~Contact.FirstName~!</h1>
			<p>If you get a chance please help your peers by providing them feedback on some of these chats?</p>


	"""
	return htmlString
def emailbottom():
	htmlString="<p<Thank you for taking a look and helping us deliver amazing customer delight!</p></body></html>"
	return htmlString

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

