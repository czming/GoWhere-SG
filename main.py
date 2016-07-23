#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import os
import jinja2
from google.appengine.api import users
from google.appengine.api import images
from google.appengine.ext import ndb
import cgi
import urllib
from datetime import datetime

def event_key():
	return ndb.Key('needed','strings')
#a class to create Comment objects with the author, content and datetime properties
class Event(ndb.Model):
	author = ndb.StringProperty(indexed=False)
	name = ndb.StringProperty(indexed=False) #need to find out what the indexed = False means
	details = ndb.StringProperty(indexed=False)
	location = ndb.StringProperty(indexed=False)
	eventdate = ndb.StringProperty()
	curr_datetime = ndb.DateTimeProperty(auto_now_add=True) #gets the current date and time
	image = ndb.BlobProperty()
	haveimage = ndb.StringProperty()

JINJA_ENVIRONMENT = jinja2.Environment(
	loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class MainHandler(webapp2.RequestHandler):
    def get(self):
		template = JINJA_ENVIRONMENT.get_template('index.html')
		template_values = {}
		self.response.write(template.render(template_values))

class Parks(webapp2.RequestHandler):
    def get(self):
		template = JINJA_ENVIRONMENT.get_template('parks.html')
		template_values = {}
		self.response.write(template.render(template_values))
	
class Sports_Facilities(webapp2.RequestHandler):
    def get(self):
		template = JINJA_ENVIRONMENT.get_template('sports_facilities.html')
		template_values = {}
		self.response.write(template.render(template_values))

class Heritage(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('heritage.html')
	template_values = {}
	self.response.write(template.render(template_values))

class SubmitFront(webapp2.RequestHandler):
    def get(self):						#seems to have an issue with the post instead of get (got 405 method not allowed error)
        # for button that changes depending on whether user is logged in
		user = users.get_current_user()
		#if user is to check if user is already logged in, otherwise user.email will lead to error if user is not logged in 
		if user: 
			submitform = """<h2 style="margin:2vw;"> Submit an Event! </h2>
			<form method="post" style="margin:2vw;" action="/submitback" enctype="multipart/form-data">
			Event Name:<br>
			<input type="text" name="eventName" required><br><br>
			Event Image (image will be shown as a square):<br>
			<input type="file" name="eventImage"/><br><br>
			Event Date and Time:<br>
			<input type="datetime-local" name="datetime" required><br><br>
			Event Location:<br>
			<input type="text" name="eventLocation" required><br><br>
			Event Details:<br>
			<textarea name="event-details" style="width:50vw;height: 10vw;" required></textarea> <br><br>
			<input type="submit" value="Send">
			</form>
			<br><br>"""
			useremail = user.email()
			template_values = {
			useremail: useremail}
			template = JINJA_ENVIRONMENT.get_template('submit.html')
			self.response.write(template.render(template_values))
			self.response.write(submitform)
			self.response.write("<p id='credits'>Logged in as {0} (<a href='{1}'>Log out</a>)</p>".format(useremail, users.create_logout_url('/submit')))
		else:
			submitform = """<p id="response"><br> Please <a href='{0}'>log in</a> to your Google account before submitting your event</p>""".format(users.create_login_url('/submit'))
			template = JINJA_ENVIRONMENT.get_template('submit.html')
			template_values = {}
			self.response.write(template.render(template_values))
			self.response.write(submitform)


#handler to process user input data
class SubmitBack(webapp2.RequestHandler):
	def post(self):
		#gets the data from the previous page, from the different elements in the form with the respective names
		event = Event(parent = event_key())
		event.name = self.request.get('eventName')
		event.author = users.get_current_user().email()
		event.details = self.request.get('event-details')
		event.location = self.request.get('eventLocation')
		eventdate = self.request.get('datetime')
		eventdate = eventdate[:10] + ' ' + eventdate[11:]
		event.eventdate = eventdate
		image = str(self.request.get('eventImage'))
		event.image = image
		if image:
			event.haveimage = "True"
		else:
			event.haveimage = None
		#I think this puts the data into datastore using the parent datastore key above ^
		event.put()
		#redirects the user back to the submit page 
		self.redirect('/submit')
		
class Past(webapp2.RequestHandler):
    def get(self):
		template = JINJA_ENVIRONMENT.get_template('past.html')
		template_values = {}
		self.response.write(template.render(template_values))
		event_query = Event.query(ancestor=event_key()).order(-Event.eventdate)
		events = event_query.fetch(10000)
		for i in events:
			if str(datetime.now()) > i.eventdate:
				if i.haveimage:
					self.response.out.write('<div class="event"><img src="{0}" class="event-image" /><p class="event-title"><strong>{1}</strong> on {4}</p><br><br><p class="event-description">{3}</p><br><br><p class="event-author">Posted by {2}</p></div>'.format("/image?image="+i.key.urlsafe(), i.name, i.author, i.details, i.eventdate[:-3]))
				else:
					self.response.out.write("""<div class="event"><img src="/pictures/default.jpg" class="event-image" /><p class="event-title"><strong>{0}</strong> on {3}</p><br><br><p class="event-description">{2}</p><br><br><p class="event-author">Posted by {1}</p></div>""".format(i.name, i.author, i.details, i.eventdate[:-3]))

class Future(webapp2.RequestHandler):
    def get(self):
		template = JINJA_ENVIRONMENT.get_template('future.html')
		template_values = {}
		self.response.write(template.render(template_values))
		event_query = Event.query(ancestor=event_key()).order(-Event.eventdate)
		events = event_query.fetch(10000)
		for i in events:
			if str(datetime.now())[:10] != i.eventdate[:10] and str(datetime.now()) < i.eventdate:
				if i.haveimage:
					self.response.out.write('<div class="event"><img src="{0}" class="event-image" /><p class="event-title"><strong>{1}</strong> on {4}</p><br><br><p class="event-description">{3}</p><br><br><p class="event-author">Posted by {2}</p></div>'.format("/image?image="+i.key.urlsafe(), i.name, i.author, i.details, i.eventdate[:-3]))
				else:
					self.response.out.write("""<div class="event"><img src="/pictures/default.jpg" class="event-image" /><p class="event-title"><strong>{0}</strong> on {3}</p><br><br><p class="event-description">{2}</p><br><br><p class="event-author">Posted by {1}</p></div>""".format(i.name, i.author, i.details, i.eventdate[:-3]))
	
class Upcoming(webapp2.RequestHandler):
    def get(self):
		template = JINJA_ENVIRONMENT.get_template('upcoming.html')
		template_values = {}
		self.response.write(template.render(template_values))
		event_query = Event.query(ancestor=event_key()).order(-Event.eventdate)
		events = event_query.fetch(10000)
		for i in events:
			if str(datetime.now())[:10] == i.eventdate[:10] and str(datetime.now()) < i.eventdate:
				if i.haveimage:
					self.response.out.write('<div class="event"><img src="{0}" class="event-image" /><p class="event-title"><strong>{1}</strong> on {4}</p><br><br><p class="event-description">{3}</p><br><br><p class="event-author">Posted by {2}</p></div>'.format("/image?image="+i.key.urlsafe(), i.name, i.author, i.details, i.eventdate[:-3]))
				else:
					self.response.out.write("""<div class="event"><img src="/pictures/default.jpg" class="event-image" /><p class="event-title"><strong>{0}</strong> on {3}</p><br><br><p class="event-description">{2}</p><br><br><p class="event-author">Posted by {1}</p></div>""".format(i.name, i.author, i.details, i.eventdate[:-3]))
	
class Image(webapp2.RequestHandler):
	def get(self):
		event_key = ndb.Key(urlsafe=self.request.get('image'))
		event = event_key.get()
		if event.image:
			self.response.headers['Content-Type'] = 'image/png'
			self.response.out.write(event.image)
		else:
			self.response.out.write(' ')
	
app = webapp2.WSGIApplication([
    ('/', MainHandler),
	('/parks', Parks),
	('/sports_facilities', Sports_Facilities),
	('/heritage', Heritage),
	('/submit', SubmitFront),
	('/submitback', SubmitBack),
	('/past', Past),
	('/future', Future),
	('/upcoming', Upcoming),
	('/image', Image)
	
], debug=True)
