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

def already_achieved(challenge_name, team_email):
    team_query = db.GqlQuery("SELECT * FROM Team " +
                                    "WHERE team_email = :1", team_email)

    already_achieved = False

    if (team_query.count() == 1): 
        teams = team_query.run(limit=1)
    
        achievement_query = db.GqlQuery("SELECT * FROM Achievement " +
                "WHERE team_email = :1 AND challenge_name = :2", team_email, challenge_name)

        for team in teams:
            if (achievement_query.count() > 0):
                return True

    return False

# def team_standings():
#     # need to sort Achievements by challenge, and then by time.
#     # if team is not already in the list then add to scoreboard list
#     # print team_name (doing query by team_email)

def get_team_achievements(team_email):
    achievements_query = db.GqlQuery("SELECT * FROM Achievement " +
                                            "WHERE team_email = :1 " +
                                            "ORDER BY challenge_number DESC", team_email)

    return achievements_query.run()

def get_users_team_name(user):
    team_query = db.GqlQuery("SELECT * FROM Team " +
                                    "WHERE team_email = :1", user.email())
    team_name = ""
    
    team_results = team_query.run()

    if (team_query.count() == 1):
        team_results = team_query.run(limit=1)
        for team in team_results:
            team_name = team.get_team_name()

    return team_name

def get_users_team_members(user):
    team_member_query = db.GqlQuery("SELECT * FROM TeamMember " +
                                    "WHERE team_email = :1", user.email())
    if (team_member_query.count() == 1) or (team_member_query.count() == 2):
        team_members = team_member_query.run()
        return team_members


class Challenge(db.Model):
    name = db.StringProperty(required=True)
    url = db.LinkProperty(required=True)
    order_number = db.IntegerProperty(required=True)

    def get_name(self):
        return self.name

class Achievement(db.Model):
    challenge_name = db.StringProperty(required=True)
    team_email = db.StringProperty(required=True)
    time_of_achievement = db.DateTimeProperty(auto_now_add=True)
    challenge_url = db.LinkProperty(required=True)
    challenge_number = db.IntegerProperty(required=True)

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
    team_email = db.StringProperty(required=True) #using as PK
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
    team_email = db.StringProperty(required=True)

    def get_team_name(self):
        return self.team_name

    def get_team_email(self):
        return self.team_email

    def get_member_name(self):
        return self.member_name

class HomePage(webapp2.RequestHandler):


    def get(self):

        # challenges = []

        # first_clue_challenge = Challenge(name="first_clue", url=db.Link("http://saadiyatgames.appspot.com/firstclue"), order_number=1)
        # challenges.append(first_clue_challenge)

        # goose_chase_challenge = Challenge(name="goose_chase", url=db.Link("http://saadiyatgames.appspot.com/goose_chase"), order_number=2)
        # challenges.append(goose_chase_challenge)


        # for challenge in challenges:
        #     challenge_query = db.GqlQuery("SELECT * FROM Challenge " +
        #                                 "WHERE name = :1", challenge.get_name())
        #     if not challenge_query.run():
        #         challenge.put()


        user = users.get_current_user()

        team_name = ""

        if user:
            log_in_out_url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'

            team_name = get_users_team_name(user)

        else:
            log_in_out_url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = { 
            'user' : user,
            'url': log_in_out_url,
            'url_linktext': url_linktext,
            'team_name': team_name
        }   
    
        template = JINJA_ENVIRONMENT.get_template('home_page.html')
        self.response.write(template.render(template_values))

class Scoreboard(webapp2.RequestHandler):

    def get(self):
        user = users.get_current_user()

        team_name = ""

        if user:
            log_in_out_url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            team_name = get_users_team_name(user)

        else:
            log_in_out_url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = { 
            'user' : user,
            'url': log_in_out_url,
            'url_linktext': url_linktext,
            'team_name': team_name
        }   
    
        template = JINJA_ENVIRONMENT.get_template('scoreboard.html')
        self.response.write(template.render(template_values))



class Registration(webapp2.RequestHandler):

    def post(self):
        user = users.get_current_user()

        if user:
            log_in_out_url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            log_in_out_url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        
        message = ""
        new_team_name = self.request.get('team_name')
        new_team_email = self.request.get('team_email')
        new_team_member1 = self.request.get('team_member1')
        new_team_member2 = self.request.get('team_member2')


        existing_teams_with_new_team_email_query = db.GqlQuery("SELECT * FROM Team " +
                                            "WHERE team_email = :1", new_team_email)
        existing_teams_with_new_team_name_query = db.GqlQuery("SELECT * FROM Team " +
                                            "WHERE team_name = :1", new_team_name)

        existing_teams_with_new_team_email = existing_teams_with_new_team_email_query.run()
        existing_teams_with_new_team_name = existing_teams_with_new_team_name_query.run()

        can_register = True

        for team in existing_teams_with_new_team_email:
            if (team.get_team_email() == new_team_email):
                message += "Email is already tied to an account.\n"
                can_register = False
        
        for team in existing_teams_with_new_team_name:
            if (team.get_team_name() == new_team_name):
                message += "Team Name is already taken.\n"
                can_register = False

        if not new_team_member1:
            can_register = False
            message += "Team Member 1 must not be blank.\n"

        if not new_team_email:
            can_register = False
            message += "Team Email must not be blank.\n"

        if (can_register):
            new_team = Team(team_name = new_team_name, team_email = new_team_email)
            new_team.put()
            team_member1 = TeamMember(team_name = new_team_name, 
                member_name = new_team_member1, team_email = new_team_email)
            team_member1.put()

            if new_team_member2:
                team_member2 = TeamMember(team_name = new_team_name, 
                    member_name = new_team_member2, team_email = new_team_email)
                team_member2.put()

            message = "Successful registration!"

            template_values = { 
                'user' : user,
                'url': log_in_out_url,
                'url_linktext': url_linktext,
                'message': message,
                'team_name': new_team_name,
                'team_email': new_team_email,
                'registered': can_register
            } 

            template = JINJA_ENVIRONMENT.get_template('registration.html')
            self.response.write(template.render(template_values))

        else:
            template_values = { 
                'user' : user,
                'url': log_in_out_url,
                'url_linktext': url_linktext,
                'message': message,
                'team_name': new_team_name
            }   
        
            template = JINJA_ENVIRONMENT.get_template('registration.html')
            self.response.write(template.render(template_values))

    def get(self):
        user = users.get_current_user()
        team_name = ""
        message = ""

        if users.get_current_user():
            log_in_out_url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            team_name = get_users_team_name(user)
        else:
            log_in_out_url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = { 
            'user' : user,
            'url': log_in_out_url,
            'url_linktext': url_linktext,
            'message': message,
            'team_name': team_name
        }   
    
        template = JINJA_ENVIRONMENT.get_template('registration.html')
        self.response.write(template.render(template_values))

class GooseChase(webapp2.RequestHandler):

    def get(self):
        user = users.get_current_user()

        clue = "Get your next clue from this professor."

        if users.get_current_user():
            log_in_out_url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            log_in_out_url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = { 
            'user' : user,
            'url': log_in_out_url,
            'url_linktext': url_linktext,
            'clue_text': clue
        }   
    
        template = JINJA_ENVIRONMENT.get_template('goose_chase.html')
        self.response.write(template.render(template_values))

class FirstClue(webapp2.RequestHandler):

    def post(self):
        user = users.get_current_user()
        team_name = get_users_team_name(user)
        challenge_name = "Special Digit"
        message = ""
        clue = "There is a special ten digit number. Each digit of the number is a count. The first digit is how many 0s are in the number, the second digit is how many 1s are in the number, the third digit is how many 2s are in the number, the fourth digit is how many 3s are in the number, ... , the tenth digit is how many 9s are in the number. What is this number?"

        answer = "6210001000"
        attempted_answer = self.request.get('attempted_answer')
        attempted_answer = attempted_answer.strip()

        if users.get_current_user():
            log_in_out_url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            log_in_out_url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'


        if (attempted_answer == answer):
            #put logged answer time code here
            message = "Correct!\n"
            if not already_achieved(challenge_name, user.email()):
                new_achievement = Achievement(challenge_name = challenge_name, team_email = user.email(), challenge_url = db.Link("http://www.saadiyatgames.appspot.com/firstclue"), challenge_number = 1)
                new_achievement.put()
                message += "New achievement added.\n"


            # self.redirect('/goose_chase')

        else:
            message = "Incorrect answer. Try again."

        template_values = { 
            'user' : user,
            'url': log_in_out_url,
            'url_linktext': url_linktext,
            'clue_text': clue,
            'team_name': team_name,
            'message': message
        }   
    
        template = JINJA_ENVIRONMENT.get_template('first_clue.html')
        self.response.write(template.render(template_values))

    def get(self):
        user = users.get_current_user()

        if users.get_current_user():
            log_in_out_url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            log_in_out_url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        clue = "There is a special ten digit number. Each digit of the number is a count. The first digit is how many 0s are in trhe number, the second digit is how many 1s are in the number, the third digit is how many 2s are in the number, the fourth digit is how many 3s are in the number, ... , the tenth digit is how many 9s are in the number. What is this number?"

        template_values = { 
            'user' : user,
            'url': log_in_out_url,
            'url_linktext': url_linktext,
            'clue_text': clue
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
            log_in_out_url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            template_url = 'home_page.html'
            log_in_out_url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        blog_query= db.GqlQuery("SELECT * FROM Blog " +
                "WHERE author = :1", user)
        blogs = blog_query.run(limit=1000)

        template_values = { 
            'user' : user,
            'url': log_in_out_url,
            'url_linktext': url_linktext,
            'blogs' : blogs
        } 

        template = JINJA_ENVIRONMENT.get_template(template_url)
        self.response.write(template.render(template_values))

# needs to be edited
class TeamHome(webapp2.RequestHandler):

    def get(self, team_name):
        user = users.get_current_user()
        team_members = {}
        team_member_names = []
        team_achievements = {}

        if user:
            log_in_out_url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'

            users_team_name = get_users_team_name(user)
            if users_team_name != team_name:
                self.redirect('/')
            else:
                url = users.create_logout_url(self.request.uri)
                url_linktext = 'Logout'
                team_members = get_users_team_members(user)
                for member in team_members:
                    team_member_names.append(member.get_member_name())
                team_achievements = get_team_achievements(user.email())


        else:
            self.redirect('/')

        template_values = { 
            'user' : user,
            'url': log_in_out_url,
            'url_linktext': url_linktext,
            'team_name': team_name,
            'team_member_names': team_member_names,
            'team_achievements': team_achievements
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
    (r'/scoreboard', Scoreboard),
    (r'/team/(.*)', TeamHome),
    (r'/firstclue', FirstClue),
    (r'/goose_chase', GooseChase),
    (r'/user/', UserHome),
    (r'/blog/(.*)/(.*)', BlogHome),
    (r'/post/(.*)/(.*)/(.*)', BlogpostPage),
    (r'/search/(.*)/(.*)/(.*)', TagSearchPage)
], debug=True)
