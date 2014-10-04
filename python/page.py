#!/usr/bin/python

import config
import MySQLdb
import cgi
import re
import datetime 

#import examples

db=MySQLdb.connect(host=config.MySQLConnection.hostname,user=config.MySQLConnection.username, passwd=config.MySQLConnection.password, db=config.MySQLConnection.dbname)

class Line(object):
	def __init__(self, lineNumber, whoSaidIt, whatWasSaid, timeItWasSaid, timeSinceLastStatement):
		self.lineNumber=lineNumber
		self.whoSaidIt=whoSaidIt
		self.whatWasSaid=whatWasSaid
		self.timeItWasSaid=timeItWasSaid
		self.timeSinceLastStatement=timeSinceLastStatement
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
		self.lines=[]



def textParser(txt, db="A"):
	firstparse = txt.find('[')
	secondparse = txt.find('[',firstparse)
	thirdparse = txt.find('[',secondparse)
	firstq=txt.find('?',firstparse)
	header = txt[:firstparse]
	results = re.match( r'.*([0-9][0-9])/([0-9][0-9])/([0-9][0-9][0-9][0-9]) ([0-9][0-9]):([0-9][0-9]) [AP]M(.*) (.*),.*', header, re.M|re.I)
	#I have no idea how RE works, in case you cannot tell
	thisdate={}
	thisdate["month"] = int(results.group(1))
	thisdate["day"] = int(results.group(2))
	thisdate["year"] = int(results.group(3))
	thisdate["hour"] = int(results.group(4))
	thisdate["minute"] = int(results.group(5))
	agentsName = results.group(6) + " " +results.group(7)[0]
	zeroline=txt[firstparse:firstq]
	starttime = datetime.datetime(thisdate["year"],thisdate["month"],thisdate["day"],thisdate["hour"],thisdate["minute"])
	firstLine=Line(0,agentsName,zeroline,starttime,0)
	listOfLines=[firstLine,]


	allLines=textsplitter(txt[firstq+1:], 1,listOfLines)
	return allLines

def textsplitter(restOfText, lineNumber, listOfLines):
	potentialStartOfNextLine = restOfText.find('[',1)
	print restOfText
	if not (potentialStartOfNextLine==-1):
		probableLine=restOfText[:potentialStartOfNextLine]
		restOfRestOfText=restOfText[potentialStartOfNextLine:]
		##print "if Not __--__--\n\n"+ probableLine + "\n\n --__--\n\n" + restOfRestOfText
	else:
		probableLine=restOfText
		restOfText=""
	closingBracket = restOfRestOfText.find("]")
	stringToTest=restOfRestOfText[:closingBracket]
	timeRegEx=re.compile("""([0-9][0-9]):([0-9][0-9]):([0-9][0-9]).([AP]M)*""")
	timeOfNextLine = timeRegEx.findall(stringToTest)
	print timeOfNextLine
	print probableLine
	if not (len(timeOfNextLine[0]) == 4):
		print "timeOfNextLine"
		print timeOfNextLine
		return -1
	else:

		timeStampEnd = probableLine.find(']')
		print "\nTimeStampEnd \n" + probableLine[:timeStampEnd+1]
		nameEnd = probableLine.find(":",timeStampEnd)
		print "\nNameEnd \n" + probableLine[:nameEnd]
		timeStamp = probableLine[:timeStampEnd+1]
		print "\ntimeStamp \n" + timeStamp
		name = probableLine[timeStampEnd+1:nameEnd]
		print "\n name \n" + name
		whatWasSaid = probableLine[nameEnd:]
		print "\n whatWasSaid \n" + whatWasSaid
		timePartsOfThisLine = timeRegEx.findall(timeStamp)
		print "timeParts"
		print len(timePartsOfThisLine)
		hours = int(timePartsOfThisLine[0][0])
		minutes = int(timePartsOfThisLine[0][1])
		seconds = int(timePartsOfThisLine[0][2])
		if (timePartsOfThisLine[0][3] == "PM"):
			hours = hours+12
		timeThisWasSaid = datetime.datetime(year=2000, month = 1, day = 1, hour = hours, minute =minutes, second = seconds)
		timeOfLastLine = listOfLines[-1].timeItWasSaid
		timeSinceLastStatement = timeThisWasSaid - timeOfLastLine
		toadd = Line(lineNumber, name, whatWasSaid,timeThisWasSaid, timeSinceLastStatement)
		listOfLines.append(toadd)
		print toadd
		raw_input("I just added a line.")
		#newRestOfText = restOfRestOfText[potentialStartOfNextLine-1:]

		#print newRestOfText
		#raw_input("waiting")
		lineNumber +=1
		potentialStartOfNextLine = restOfRestOfText.find("[",1)
		if (potentialStartOfNextLine == -1):
			print "potentialStartOfNextLine == 1"
			return listOfLines
		newList = textsplitter(restOfRestOfText, lineNumber,listOfLines)
		while (newList == -1):
			print "newlist == -1"
			potentialStartOfNextLine = restOfRestOfText.find("[",potentialStartOfNextLine)
			newList = textsplitter(restOfRestOfText, lineNumber,listOfLines)
			if (potentialStartOfNextLine == -1):
				newList=textsplitter(restOfRestOfText, lineNumber,listOfLines)
		return newList
 
		
def mainSequence(db, txt, chatid):
	thischat = parseBlobIntoLines(txt)
	thischat.chatID=chatid

	cursor = db.cursor()

	cmd = "INSERT INTO maintable (chatid) VALUES (%s)" %( chatid )
	cursor.execute(cmd)
	for each in thischat.lines:
		if ((each.whoSaidIt==thischat.Agent) or (each.whoSaidIt==thischat.Agentfname + " " + thischat.Agentlinitial)):
			whosaid="agent"
		else:
			whosaid="customer"

		cmd = """INSERT INTO interactions (chatid, line, whois, linetext, timefromlastline) VALUES ("%s", "%s", "%s", "%s", "%s")""" %(chatid, str(each.lineNumber), whosaid, each.whatWasSaid, each.timeSinceLastStatement)
		print cmd
		cursor.execute(cmd)







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



