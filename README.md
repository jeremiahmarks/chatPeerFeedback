chatPeerFeedback
================

This application will server as a way to get anonymous peer feedback on support chats

This application will be written in Python, PHP, and potentially Java/Tomcat.

The application will have four main pages/views:

1. The page where a daily input can be made.
  * Page will provide two large text areas for two chats. Each chat will have an associated id number that is in the format of 
      YYMMDD - 0000###
  * Page will be used by lead/other to add chat logs to the general queue. 
2. The one-off input page
  * Page will be used by individual chat agents to submit their own chat logs for peer feedback
3. The chat feedback page
  * page will display the an individual chat log and allow the viewer to provide feedback
  * example can be seen at : http://jlmarks.org/is2/chatrev.html
4. The chat results page
  * page will display the chat log with a cumulative total of good/bad and all associated comments. 
  
Additional pages:

1. All chat logs submitted page
  * page to see list of all chat logs submitted with links to each the feedback and results page. 

TODO

1. Determine database design
2. Scripts to write:
  * parse strings into component parts
  * upload component parts to server
  * when feedback is submitted save feedback for each line of the chat in a way that it does not overwrite other feedback and allows things to be tallied
  * access and server information based on pages outlined
  * script that emails all chats submitted for review

Database design:

1. main table
  * chatdate - the date portion of the chat id
  * chatnumber - the number portion of the chat id
  * chatID - the combined portions of the chatdate - chatnumber
  * dat/time uploaded - the date time that the chat was uploaded. 
2. Interactions table
  * chatid - the combined portions of the chatdate - chatnumber
  * line # - which line of the chat we are recording (starts with 0 which is the record of when chat started and who chat is with)
  * Agent/Customer - Who submitted the line, the agent or the customer?
  * Line Text - What was submitted for that line
  * Time from last line - the time difference from the last line that was submitted to this line
3. Simple feedback table
  * Chatid - the combined portions of the chatdate - chatnumber
  * line # - which line of the chat we are recording (starts with 0 which is the record of when chat started and who chat is with)
  * countA - the number of votes for simple feedback option A (Either good for the agent or important for the customer)
  * countB - the number of votes for simple feedback option B (Either bad for the agent or something else for the customer)
4. Complex feedback table
  * Chatid - the combined portions of the chatdate - chatnumber
  * line # - which line of the chat we are recording (starts with 0 which is the record of when chat started and who chat is with)
  * complexfeedback - the text feedback that was submitted for this line.
