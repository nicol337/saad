import webapp2

class MainPage(webapp2.RequestHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/plain'
		self.response.write('Hello, Nicole and the Rest of the World!!!')

application = webapp2.WSGIApplication([
	('/', MainPage),
], debug=True)
