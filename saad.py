import os
import cgi
import urllib
import re

from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext import db

import jinja2
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

ViewingPage = 0

def to_link(str):
    new_link='<a href="'+str+'">'+str+'</a>'
    if str.endswith(".jpg") or str.endswith(".png") or str.endswith(".gif"):
        new_link = str
    return jinja2.Markup(new_link)

class Blog(db.Model):
    author = db.UserProperty(required=True)
    title = db.StringProperty(required=True)

class Blogpost(db.Model):
    author = db.UserProperty(required=True)
    title = db.StringProperty(required=True)
    content = db.TextProperty()
    tags = db.StringListProperty()
    blog = db.StringProperty(required=True)
    date = db.DateTimeProperty(auto_now_add=True)

    def update(self,new_title,new_content, new_tags):
        self.title = new_title
        self.content = new_content
        self.tags = new_tags
        self.put()

class Team(db.Model):
    team_name = db.StringProperty(required=True)
    team_email = db.StringProperty(required=True)
    team_birth = db.DateTimeProperty(auto_now_add=True)


    def get_team_email(self):
        return self.team_email

    def get_team_name(self):
        return self.team_name

    def get_team_brith(self):
        return self.team_birth


class TeamMember(db.Model):
    team_name = db.StringProperty(required=True)
    member_name = db.StringProperty(required=True)

    def get_team_name(self):
        return self.team_name



class HomePage(webapp2.RequestHandler):

    def get(self):
        user = users.get_current_user()

        team_name = ""

        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'

            team_query = db.GqlQuery("SELECT * FROM Team " +
                                    "WHERE team_email = :1", user.email())

            team_results = team_query.run()
            



            if (team_query.count() == 1):
                team_results = team_query.run(limit=1)
                for team in team_results:
                    team_name = team.get_team_name()

        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = { 
            'user' : user,
            'url': url,
            'url_linktext': url_linktext,
            'team_name': team_name
        }   
    
        template = JINJA_ENVIRONMENT.get_template('home_page.html')
        self.response.write(template.render(template_values))

class Registration(webapp2.RequestHandler):

    def post(self):

        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        user = users.get_current_user()
        error_msg = ""
        new_team_name = self.request.get('team_name')
        new_team_email = self.request.get('team_email')


        existing_team_emails_query = db.GqlQuery("SELECT * FROM Team " +
                                            "WHERE team_email = :1", new_team_email)
        existing_team_names_query = db.GqlQuery("SELECT * FROM Team " +
                                            "WHERE team_name = :1", new_team_name)

        existing_team_emails = existing_team_emails_query.run()
        existing_team_names = existing_team_names_query.run()

        can_register = True

        for email in existing_team_emails:
            if (email == new_team_email):
                error_msg += "Email is already tied to an account.\n"
                can_register = False
        
        for name in existing_team_names:
            if (name == new_team_name):
                error_msg += "Team Name is already taken.\n"
                can_register = False

        if (can_register):
            new_team = Team(team_name = new_team_name, team_email = new_team_email)
            new_team.put()

            template_values = { 
                'user' : user,
                'url': url,
                'url_linktext': url_linktext,
                'team_name': new_team_name,
                'team_email': new_team_email
            } 

            template = JINJA_ENVIRONMENT.get_template('team_home_page.html')
            self.response.write(template.render(template_values))
            self.redirect('/team/' + new_team_name)

        else:
            template_values = { 
                'user' : user,
                'url': url,
                'url_linktext': url_linktext,
                'error_msg': error_msg,
                'team_name': new_team_name,
                'team_email': new_team_email
            }   
        
            template = JINJA_ENVIRONMENT.get_template('registration.html')
            self.response.write(template.render(template_values))



    def get(self):
        user = users.get_current_user()

        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = { 
            'user' : user,
            'url': url,
            'url_linktext': url_linktext
        }   
    
        template = JINJA_ENVIRONMENT.get_template('registration.html')
        self.response.write(template.render(template_values))


class FirstClue(webapp2.RequestHandler):

    def get(self):
        user = users.get_current_user()

        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = { 
            'user' : user,
            'url': url,
            'url_linktext': url_linktext
        }   
    

        template = JINJA_ENVIRONMENT.get_template('first_clue.html')
        self.response.write(template.render(template_values))

class UserHome(webapp2.RequestHandler):

    def post(self):
        if self.request.get('blog_title'):
            new_blog_name = self.request.get('blog_title')
            new_blog = Blog(author=users.get_current_user(),title=new_blog_name)
            new_blog.put()
            self.redirect('/blog/'+new_blog_name+'/')
        else:
            self.redirect('/user/')

    def get(self):
        user = users.get_current_user()

        if users.get_current_user():
            template_url= 'user_home_page.html'
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            template_url = 'home_page.html'
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        blog_query= db.GqlQuery("SELECT * FROM Blog " +
                "WHERE author = :1", user)
        blogs = blog_query.run(limit=1000)

        template_values = { 
            'user' : user,
            'url': url,
            'url_linktext': url_linktext,
            'blogs' : blogs
        } 

        template = JINJA_ENVIRONMENT.get_template(template_url)
        self.response.write(template.render(template_values))

# needs to be edited
class TeamHome(webapp2.RequestHandler):

    def post(self, blog_name, page_number):
        user = users.get_current_user()


    def get(self, team_name):

        user = users.get_current_user()

        template_values = { 
            'user' : user,
        }
       
        template = JINJA_ENVIRONMENT.get_template("team_home_page.html")
        self.response.write(template.render(template_values))

class BlogHome(webapp2.RequestHandler):

    def post(self, blog_name, page_number):
        if self.request.get('blogpost_title') and self.request.get('blogpost_content'):
            blogpost_title = self.request.get('blogpost_title')
            blogpost_content = self.request.get('blogpost_content')
            
            blogpost_tags = self.request.get('blogpost_tags')
            tag_tokens = blogpost_tags.split(',')  

            blogpost = Blogpost(author=users.get_current_user(), title=blogpost_title, content=blogpost_content, blog=blog_name, tags=tag_tokens)
            blogpost.put()

            self.redirect('/blog/' + blog_name + '/')
        else:
            self.redirect('/blog/' + blog_name + '/')  


    def get(self, blog_name, page_number):

        if page_number and isinstance(page_number, int):
            ViewingPage = int(page_number[0])
        else:
            ViewingPage = 0

        user = users.get_current_user()
        owner = False
        if users.get_current_user():
            log_in_out_url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            template_url = 'home_page.html'
            log_in_out_url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        one_blog_query = db.GqlQuery("SELECT * FROM Blog " +
                "WHERE title = :1", blog_name)

        one_blog = one_blog_query.run(limit=1)
        
        for blog in one_blog:
            if user == blog.author:
                owner = True
            else:
                owner = False

        blogpost_query = db.GqlQuery("SELECT * FROM Blogpost " +
                "WHERE blog = :1 " +
                "ORDER BY date DESC", blog_name)

        blogposts = blogpost_query.run(offset=(ViewingPage+1)*10)

        number_of_posts_left = 0

        for blog in blogposts:
            number_of_posts_left+=1

        if number_of_posts_left:
            moreposts = True
        else:
            moreposts = False

        blogposts = blogpost_query.run(offset=ViewingPage*10,limit=10)

        blogpost_content = {}
        for post in blogpost_query.run(offset=ViewingPage*10,limit=10):
            blogpost_content[post.title]=post.content
            if len(post.content) > 500:
                blogpost_content[post.title]=post.content[:500]

        for key in blogpost_content.keys():
            text_tokens = blogpost_content[key].split(' ')
            for tok in text_tokens:
                if tok.startswith("http://") or tok.startswith("https://"):
                    blogpost_content[key]=blogpost_content[key].replace(tok,to_link(tok))

        blog_tags=[]
        for post in blogpost_query.run():
            for tag in post.tags:
                if tag not in blog_tags:
                    blog_tags.append(tag)
            

        blog_query = db.GqlQuery("SELECT * FROM Blog " +
                "WHERE author = :1 " +
                "ORDER BY title", user)
        blogs = blog_query.run(limit=1000)    

        template_values = { 
            'user' : user,
            'url': log_in_out_url,
            'url_linktext': url_linktext,
            'blogs' : blogs,
            'blogposts' : blogposts,
            'blog_name': blog_name,
            'one_blog': one_blog,
            'blogpost_content' : blogpost_content,
            'blog_tags': blog_tags,
            'owner' : owner,
            'moreposts' : moreposts,
            'page_counter': ViewingPage
        } 
        template = JINJA_ENVIRONMENT.get_template("blog_home_page.html")
        self.response.write(template.render(template_values))

class BlogpostPage(webapp2.RequestHandler):
    def post(self, blog_name, blogpost_name, mode):

        user = users.get_current_user()
        owner = False

        one_blog_query = db.GqlQuery("SELECT * FROM Blog " +
                "WHERE title = :1", blog_name)

        one_blog = one_blog_query.run(limit=1)
        
        for blog in one_blog:
            if user == blog.author:
                owner = True
            else:
                owner = False

        if mode == "edit" and owner == True:
            edit = True
        else:
            edit = False

        blogpost_query = db.GqlQuery("SELECT * FROM Blogpost " +
                "WHERE blog = :1 AND title = :2 " +
                "ORDER BY date DESC", blog_name, blogpost_name)

        blogpost = blogpost_query.run(limit=1)
        new_title = self.request.get('blogpost_title')
        new_content = self.request.get('blogpost_content')
        tag_str = self.request.get('blogpost_tags')
        new_tags = tag_str.split(',')

        if edit and owner:
            for post in blogpost:
                post.update(new_title, new_content, new_tags)

        self.redirect('/post/'+ blog_name+'/'+new_title+"/view")

    def get(self, blog_name, blogpost_name, mode):

        user = users.get_current_user()
        owner = False

        if users.get_current_user():
            log_in_out_url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            template_url = 'home_page.html'
            log_in_out_url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        one_blog_query = db.GqlQuery("SELECT * FROM Blog " +
                "WHERE title = :1", blog_name)

        one_blog = one_blog_query.run(limit=1)
        
        for blog in one_blog:
            if user == blog.author:
                owner = True
            else:
                owner = False

        if mode == "edit" and owner == True:
            edit = True
        else:
            edit = False

        blog_tags_query = db.GqlQuery("SELECT * FROM Blogpost " +
                "WHERE blog = :1 " +
                "ORDER BY date DESC", blog_name)

        blogpost_query = db.GqlQuery("SELECT * FROM Blogpost " +
                "WHERE blog = :1 AND title = :2 " +
                "ORDER BY date DESC", blog_name, blogpost_name)

        blog_tags=[]
        for post in blog_tags_query.run(limit=1000):
            for tag in post.tags:
                if tag not in blog_tags:
                    blog_tags.append(tag)

        for post in blogpost_query.run(limit=1):
            post.content.split(' ')
            text_tokens = post.content.split(' ')
            for tok in text_tokens:
                if tok.startswith("http://") or tok.startswith("https://"):
                    post.content=post.content.replace(tok,to_link(tok))
            blogpost = post

        blog_query = db.GqlQuery("SELECT * FROM Blog " +
                "WHERE author = :1 " +
                "ORDER BY title", user)
        blogs = blog_query.run(limit=1000)   

        template_values = { 
            'user' : user,
            'url': log_in_out_url,
            'url_linktext': url_linktext,
            'blogs' : blogs,
            'blogpost' : blogpost,
            'blog_name': blog_name,
            'one_blog': one_blog,
            'owner' : owner,
            'blog_tags' : blog_tags,
            'edit' : edit
        } 

        template = JINJA_ENVIRONMENT.get_template("blog_post_page.html")
        self.response.write(template.render(template_values))

class TagSearchPage(webapp2.RequestHandler):

    def get(self, blog_name, tag_name, page_number):

        if page_number and isinstance(page_number, int):
            ViewingPage = int(page_number[0])
        else:
            ViewingPage = 0

        user = users.get_current_user()
        owner = False

        if users.get_current_user():
            log_in_out_url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            template_url = 'home_page.html'
            log_in_out_url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        one_blog_query = db.GqlQuery("SELECT * FROM Blog " +
                "WHERE title = :1", blog_name)

        one_blog = one_blog_query.run(limit=1)
        
        for blog in one_blog:
            if user == blog.author:
                owner = True
            else:
                owner = False
        
        blogpost_query = db.GqlQuery("SELECT * FROM Blogpost " +
                "WHERE blog = :1 AND tags = :2 " +
                "ORDER BY date DESC", blog_name, tag_name)

        blogposts = blogpost_query.run(offset=(ViewingPage+1)*10)

        number_of_posts_left = 0

        for blog in blogposts:
            number_of_posts_left+=1

        if number_of_posts_left:
            moreposts = True
        else:
            moreposts = False

        blogposts = blogpost_query.run(offset=ViewingPage*10,limit=10)

        blogpost_content = {}

        for post in blogpost_query.run(offset=ViewingPage*10,limit=10):
            blogpost_content[post.title]=post.content
            if len(post.content) > 500:
                blogpost_content[post.title]=post.content[:500]

        for key in blogpost_content.keys():
            text_tokens = blogpost_content[key].split(' ')
            for tok in text_tokens:
                if tok.startswith("http://") or tok.startswith("https://"):
                    blogpost_content[key]=blogpost_content[key].replace(tok,to_link(tok))

        blog_tags_query = db.GqlQuery("SELECT * FROM Blogpost " +
                "WHERE blog = :1 " +
                "ORDER BY date DESC", blog_name)
        blog_tags=[]
        for post in blog_tags_query.run(limit=1000):
            for tag in post.tags:
                if tag not in blog_tags:
                    blog_tags.append(tag)

        blog_query = db.GqlQuery("SELECT * FROM Blog " +
                "WHERE author = :1 " +
                "ORDER BY title", user)
        blogs = blog_query.run(limit=1000)   

        template_values = { 
            'user' : user,
            'url': log_in_out_url,
            'url_linktext': url_linktext,
            'blogs' : blogs,
            'blogposts' : blogposts,
            'blogpost_content': blogpost_content,
            'blog_name': blog_name,
            'one_blog': one_blog,
            'tag_name' : tag_name,
            'blog_tags' : blog_tags,
            'owner' : owner,
            'moreposts': moreposts,
            'page_counter': ViewingPage
        } 

        template = JINJA_ENVIRONMENT.get_template("tag_search_page.html")
        self.response.write(template.render(template_values))

application = webapp2.WSGIApplication([
    ('/', HomePage),
    (r'/registration', Registration),
    (r'/team/(.*)', TeamHome),
    (r'/firstclue/(.*)', FirstClue),
    (r'/user/', UserHome),
    (r'/blog/(.*)/(.*)', BlogHome),
    (r'/post/(.*)/(.*)/(.*)', BlogpostPage),
    (r'/search/(.*)/(.*)/(.*)', TagSearchPage)
], debug=True)
