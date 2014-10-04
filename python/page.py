#!/usr/bin/python

import config
import MySQLdb
import cgi
import re
import datetime 

import examples

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
 
		








