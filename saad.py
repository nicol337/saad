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

class ScoreboardStanding:
    def __init__(self, team_name, team_birth, team_members, highest_achievement = None):
        self.team_name = team_name
        self.team_birth = team_birth
        self.team_members = team_members
        if highest_achievement:
            self.highest_challenge_number = highest_achievement.challenge_number
            self.highest_challenge_name = highest_achievement.challenge_name
            self.time_of_achievement = highest_achievement.time_of_achievement
        else:
            self.highest_challenge_number = -1
            self.highest_challenge_name = ""
            self.time_of_achievement = db.DateTimeProperty()
        self.standings = -1

    def set_standings(self, standing):
        self.standings = standing

    def __getitem__(self, key = None):
        if key == 0:
            return self.team_name
        elif key == 1:
            return self.team_birth
        elif key == 2:
            return self.team_members
        elif key ==3:
            return self.highest_challenge_number
        elif key == 4:
            return self.time_of_achievement
        else:
            return self.team_name
  

def get_team_standings():
    # need to sort Achievements by challenge, and then by time.
    # if team is not already in the list then add to scoreboard list
    # print team_name (doing query by team_email)
    teams = Team.all()
    achieved_teams = []
    unachieved_teams = []

    # separate teams into achieved_teams and unachieved_teams
    for team in teams:
        team_name = team.team_name
        team_email = team.team_email
        team_birth = team.team_birth
        highest_achievement = get_highest_achievement(team.team_email)
        team_members = get_team_members(team.team_email)

        new_entry = ScoreboardStanding(team_name, team_birth, team_members, highest_achievement)

        if not highest_achievement:
            unachieved_teams.append(new_entry)
        else:
            achieved_teams.append(new_entry)




    unachieved_teams.sort(key=lambda x: x.team_birth)

    achieved_teams.sort(key=lambda x: (-x[3], x[4]))


    standings_itr = 1
    for each_team in achieved_teams:
        each_team.set_standings(standings_itr)
        standings_itr+=1


    return achieved_teams, unachieved_teams

def get_team_achievements(team_email, orderby = "DESC"):
    achievements_query = db.GqlQuery("SELECT * FROM Achievement " +
                                            "WHERE team_email = :1 " +
                                            "ORDER BY challenge_number " + orderby, team_email)

    return achievements_query.run()


def get_highest_achievement(team_email):
    achievements = get_team_achievements(team_email)
    if not achievements: 
        return False
    for achievement in achievements:
        return achievement



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
 
def get_team_members(team_email):
    team_member_query = db.GqlQuery("SELECT * FROM TeamMember " +
                                    "WHERE team_email = :1", team_email)
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

        user = users.get_current_user()

        team_name = ""

        if user:
            log_in_out_url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'

            team_name = get_users_team_name(user)
            if not team_name:
                self.redirect('/registration')

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
        # teams = Team.all()
        achieved_teams,unachieved_teams = get_team_standings()


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
            'team_name': team_name,
            'achieved_teams': achieved_teams,
            'unachieved_teams': unachieved_teams
        }   
    
        template = JINJA_ENVIRONMENT.get_template('scoreboard.html')
        self.response.write(template.render(template_values))

class Registration(webapp2.RequestHandler):

    def post(self):
        user = users.get_current_user()
        already_has_team = get_users_team_name(user)

        message = ""
        new_team_name = self.request.get('team_name')
        new_team_email = self.request.get('team_email')
        new_team_member1 = self.request.get('team_member1')
        new_team_member2 = self.request.get('team_member2')        

        if user:
            log_in_out_url = users.create_logout_url(self.request.uri)
            if not already_has_team:
                new_team_email = user.email()
            url_linktext = 'Logout'
        else:
            log_in_out_url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'



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

        if user:
            team_name = get_users_team_name(user)
            log_in_out_url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            
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

class TemkeenGame(webapp2.RequestHandler):

    def post(self):
        user = users.get_current_user()
        team_name = get_users_team_name(user)
        challenge_name = "Temkeen Game"
        challenge_number = 8
        message = ""
        
        clue = "Some of the executives of Temkeen are playing a game on the map of the Saadiyat campus. The game is played on an eight by eight square of the campus and the rules are like this: each player gets a turn to place eight pieces on the board that can attack vertically, horizontally, and diagonally from that space. However, a player&rsquo;s pieces are not allowed to be in spaces that can directly attack each other (i.e. cannot have two pieces in the same row, column, or diagonal).  Then the other player places their eight pieces in spots, maximizing the number of pieces that cannot be attacked by their opponents pieces.  Each player can choose to not put all eight however there are certains ways for the first player to place all eight perfectly so that all spaces are &ldquo;attackable&rdquo; One pieces has been placed for you. Find the rest of the pieces so that they obey the rules, cover all the spaces, and are on squares that contain a purple building (squares with only partial purple count as in D17)"

        attempted_answer = self.request.get_all("number")

        answer = [u'6', u'8', u'10', u'12', u'18', u'56', u'102']

        all_correct = True

        if (len(attempted_answer) != len(answer)):
            all_correct = False
        else:
            for itr in range(len(answer)):
                if (attempted_answer[itr] != answer[itr]):
                    all_correct = False


        if users.get_current_user():
            log_in_out_url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            log_in_out_url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'


        if (all_correct):
            #put logged answer time code here
            message = "Correct!\n"
            if not already_achieved(challenge_name, user.email()):
                new_achievement = Achievement(challenge_name = challenge_name, team_email = user.email(), challenge_url = db.Link("http://saadiyatgames.appspot.com/apartments"), challenge_number = challenge_number)
                # may have issues with this link being absolute or not
                new_achievement.put()
                message += "New achievement added.\n"

            # self.redirect('/the next challenge')

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
    
        template = JINJA_ENVIRONMENT.get_template('temkeen_game.html')
        self.response.write(template.render(template_values))

    def get(self):
        user = users.get_current_user()
        team_name = ""

        if users.get_current_user():
            log_in_out_url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            team_name = get_users_team_name(user)
        else:
            log_in_out_url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        clue = "Some of the executives of Temkeen are playing a game on the map of the Saadiyat campus. The game is played on an eight by eight square of the campus and the rules are like this: each player gets a turn to place eight pieces on the board that can attack vertically, horizontally, and diagonally from that space. However, a player&rsquo;s pieces are not allowed to be in spaces that can directly attack each other (i.e. cannot have two pieces in the same row, column, or diagonal).  Then the other player places their eight pieces in spots, maximizing the number of pieces that cannot be attacked by their opponents pieces.  Each player can choose to not put all eight however there are certains ways for the first player to place all eight perfectly so that all spaces are &ldquo;attackable&rdquo; One pieces has been placed for you. Find the rest of the pieces so that they obey the rules, cover all the spaces, and are on squares that contain a purple building (squares with only partial purple count as in D17)"

        template_values = { 
            'user' : user,
            'url': log_in_out_url,
            'url_linktext': url_linktext,
            'clue_text': clue,
            'team_name': team_name
        }   
    
        template = JINJA_ENVIRONMENT.get_template('temkeen_game.html')
        self.response.write(template.render(template_values))

class CampusWalk(webapp2.RequestHandler):

    def post(self):
        user = users.get_current_user()
        team_name = get_users_team_name(user)
        challenge_name = "Long Day on Campus"
        challenge_number = 7 
        message = ""
        
        clue = "The first day of class is very busy for Ray. Because he&rsquo;s on the track team he starts his day at the gym. Because Ray is trying to find a new life direction by being involved in everything on campus, he needs to travel to all the other 12 building on campus today but end up at the gym. If Ray starts and ends his day at the gym and visits every other building on campus once, how many different ways can he structure his building visits?"

        answer = "479001600"
        lazy_answer = "12!"
        attempted_answer = self.request.get('attempted_answer').strip().upper()


        if users.get_current_user():
            log_in_out_url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            log_in_out_url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'


        if (attempted_answer == answer) or (attempted_answer == lazy_answer):
            #put logged answer time code here
            message = "Correct!\n"
            if not already_achieved(challenge_name, user.email()):
                new_achievement = Achievement(challenge_name = challenge_name, team_email = user.email(), challenge_url = db.Link("http://saadiyatgames.appspot.com/apartments"), challenge_number = challenge_number)
                # may have issues with this link being absolute or not
                new_achievement.put()
                message += "New achievement added.\n"

            # self.redirect('/the next challenge')

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
    
        template = JINJA_ENVIRONMENT.get_template('campus_walk.html')
        self.response.write(template.render(template_values))

    def get(self):
        user = users.get_current_user()
        team_name = ""

        if users.get_current_user():
            log_in_out_url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            team_name = get_users_team_name(user)
        else:
            log_in_out_url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        clue = "The first day of class is very busy for Ray. Because he&rsquo;s on the track team he starts his day at the gym. Because Ray is trying to find a new life direction by being involved in everything on campus, he needs to travel to all the other 12 building on campus today but end up at the gym. If Ray starts and ends his day at the gym and visits every other building on campus once, how many different ways can he structure his building visits?"

        template_values = { 
            'user' : user,
            'url': log_in_out_url,
            'url_linktext': url_linktext,
            'clue_text': clue,
            'team_name': team_name
        }   
    
        template = JINJA_ENVIRONMENT.get_template('campus_walk.html')
        self.response.write(template.render(template_values))

class MeetingParty(webapp2.RequestHandler):

    def post(self):
        user = users.get_current_user()
        team_name = get_users_team_name(user)
        challenge_name = "Meet and Greet"
        challenge_number = 6
        message = ""
        
        clue = "Yesterday there was a party of incoming students where no one had met each other before. Everyone except for one person left the party having met three people, that one person had only met one other person. How many people could possibly have been at this party? Tick off all the possible numbers:"

        attempted_answer = self.request.get_all("number")

        answer = [u'6', u'8', u'10', u'12', u'18', u'56', u'102']

        all_correct = True

        if (len(attempted_answer) != len(answer)):
            all_correct = False
        else:
            for itr in range(len(answer)):
                if (attempted_answer[itr] != answer[itr]):
                    all_correct = False


        if users.get_current_user():
            log_in_out_url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            log_in_out_url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'


        if (all_correct):
            #put logged answer time code here
            message = "Correct!\n"
            if not already_achieved(challenge_name, user.email()):
                new_achievement = Achievement(challenge_name = challenge_name, team_email = user.email(), challenge_url = db.Link("http://saadiyatgames.appspot.com/apartments"), challenge_number = challenge_number)
                # may have issues with this link being absolute or not
                new_achievement.put()
                message += "New achievement added.\n"

            # self.redirect('/the next challenge')

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
    
        template = JINJA_ENVIRONMENT.get_template('meeting_party.html')
        self.response.write(template.render(template_values))

    def get(self):
        user = users.get_current_user()
        team_name = ""

        if users.get_current_user():
            log_in_out_url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            team_name = get_users_team_name(user)
        else:
            log_in_out_url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        clue = "Yesterday there was a party of incoming students where no one had met each other before. Everyone except for one person left the party having met three people, that one person had only met one other person. How many people could possibly have been at this party? Tick off all the possible numbers:"

        template_values = { 
            'user' : user,
            'url': log_in_out_url,
            'url_linktext': url_linktext,
            'clue_text': clue,
            'team_name': team_name
        }   
    
        template = JINJA_ENVIRONMENT.get_template('meeting_party.html')
        self.response.write(template.render(template_values))

class Painters(webapp2.RequestHandler):

    def post(self):
        user = users.get_current_user()
        team_name = get_users_team_name(user)
        challenge_name = "Painting Party"
        challenge_number = 5
        message = ""
        
        clue = "A group of friends are unhappy with the wall color of their new 4 sided common room so they want to paint it. They went to ACE hardware and got gray, blue, yellow, peach, and green paint. They&#39;ve decided that neighboring walls should not be the same color. How many ways can they paint the common room with the colors they have?"

        answer = "260"
        attempted_answer = self.request.get('attempted_answer').strip().upper()


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
                new_achievement = Achievement(challenge_name = challenge_name, team_email = user.email(), challenge_url = db.Link("http://saadiyatgames.appspot.com/apartments"), challenge_number = challenge_number)
                # may have issues with this link being absolute or not
                new_achievement.put()
                message += "New achievement added.\n"

            # self.redirect('/the next challenge')

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
    
        template = JINJA_ENVIRONMENT.get_template('painters_riddle.html')
        self.response.write(template.render(template_values))

    def get(self):
        user = users.get_current_user()
        team_name = ""

        if users.get_current_user():
            log_in_out_url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            team_name = get_users_team_name(user)
        else:
            log_in_out_url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        clue = "A group of friends are unhappy with the wall color of their new 4 sided common room so they want to paint it. They went to ACE hardware and got gray, blue, yellow, peach, and green paint. They&#39;ve decided that neighboring walls should not be the same color. How many ways can they paint the common room with the colors they have?"

        template_values = { 
            'user' : user,
            'url': log_in_out_url,
            'url_linktext': url_linktext,
            'clue_text': clue,
            'team_name': team_name
        }   
    
        template = JINJA_ENVIRONMENT.get_template('painters_riddle.html')
        self.response.write(template.render(template_values))

class Posters(webapp2.RequestHandler):

    def post(self):
        user = users.get_current_user()
        team_name = get_users_team_name(user)
        challenge_name = "Palms and Posters"
        challenge_number = 4
        message = ""
        
        clue = "<p> At the Saadiyat campus, Cara, Rumi, Arya, Elena, and Jose have started pinning posters to the palm trees by the student center. The students use three trees in particular and each tree has different colored rocks surrounding it. Each person only pins posters to trees that are surrounded by rocks of their favorite color. For example, before Jessica left to study abroad, she would put posters on trees that had blue rocks around it.</p>\n<p>This semester, the tallest tree is surrounded by pink, teal, and violet rocks. The second tallest tree is surrounded by gray, violet, and white rocks. The shortest tree is surrounded by gray, violet, and green rocks. Trees can also be surrounded by blue, brown, and yellow rocks.</p>\n<p>One person hanging posters likes teal and another person likes brown. Facilities is eager to keep the campus clean and each night they take down the posters from the trees so students try to pin posters as often as possible. Students are also kind enough to support each other&rsquo;s causes so students hang each other&rsquo;s posters making it impossible to differential who hung which poster.</p>\n<p>On the first day of class Arya, Cara, and Elena went to hang some posters. The tallest tree had 1 poster, the second tallest had 1 poster, and the shortest had 2 posters on it. On the second day of class Arya, Cara, and Jose went to hang some posters. The tallest tree had no posters, and the second tallest and shortest had two posters each. On the third day of class Arya, Cara, and Rumi went to hang some posters. The tallest tree had no posters, the second tallest had one poster, and the shortest has two posters. On the fourth day of class Rumi, Elena, and Jose hung some posters. The tallest tree and second tallest trees had one poster each, the shortest tree had no posters. On the fifth day of class, Arya, Elena and Jose hung the last of their posters. The tallest tree had one poster, the second tallest had two posters, and the shortest had one poster.</p>\n<p>According to these events, which color does each person like?</p>"

        answer = "Red"
        attempted_answer = self.request.get('attempted_answer')
        attempted_answer = attempted_answer.strip()
        attempted_answer = attempted_answer.upper()

        cara_attempt = self.request.get('Cara').strip().upper()
        rumi_attempt = self.request.get('Rumi').strip().upper()
        arya_attempt = self.request.get('Arya').strip().upper()
        elena_attempt = self.request.get('Elena').strip().upper()
        jose_attempt = self.request.get('Jose').strip().upper()

        attempts = [cara_attempt, rumi_attempt, arya_attempt, elena_attempt, jose_attempt]
        answers = ["GREEN", "BROWN", "GRAY", "TEAL", "WHITE"]

        if users.get_current_user():
            log_in_out_url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            log_in_out_url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        all_correct = True

        for itr in range(len(answers)):
            if attempts[itr] != answers[itr]:
                all_correct = False


        if all_correct:
            #put logged answer time code here
            message = "Correct!\n"
            if not already_achieved(challenge_name, user.email()):
                new_achievement = Achievement(challenge_name = challenge_name, team_email = user.email(), challenge_url = db.Link("http://saadiyatgames.appspot.com/palmsandposters"), challenge_number = challenge_number)
                # may have issues with this link being absolute or not
                new_achievement.put()
                message += "New achievement added.\n"

            # self.redirect('/the next challenge')

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
    
        template = JINJA_ENVIRONMENT.get_template('posters_riddle.html')
        self.response.write(template.render(template_values))

    def get(self):
        user = users.get_current_user()
        team_name = ""

        if users.get_current_user():
            log_in_out_url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            team_name = get_users_team_name(user)
        else:
            log_in_out_url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        clue = "<p> At the Saadiyat campus, Cara, Rumi, Arya, Elena, and Jose have started pinning posters to the palm trees by the student center. The students use three trees in particular and each tree has different colored rocks surrounding it. Each person only pins posters to trees that are surrounded by rocks of their favorite color. For example, before Jessica left to study abroad, she would put posters on trees that had blue rocks around it.</p>\n<p>This semester, the tallest tree is surrounded by pink, teal, and violet rocks. The second tallest tree is surrounded by gray, violet, and white rocks. The shortest tree is surrounded by gray, violet, and green rocks. Trees can also be surrounded by blue, brown, and yellow rocks.</p>\n<p>One person hanging posters likes teal and another person likes brown. Facilities is eager to keep the campus clean and each night they take down the posters from the trees so students try to pin posters as often as possible. Students are also kind enough to support each other&rsquo;s causes so students hang each other&rsquo;s posters making it impossible to differential who hung which poster.</p>\n<p>On the first day of class Arya, Cara, and Elena went to hang some posters. The tallest tree had 1 poster, the second tallest had 1 poster, and the shortest had 2 posters on it. On the second day of class Arya, Cara, and Jose went to hang some posters. The tallest tree had no posters, and the second tallest and shortest had two posters each. On the third day of class Arya, Cara, and Rumi went to hang some posters. The tallest tree had no posters, the second tallest had one poster, and the shortest has two posters. On the fourth day of class Rumi, Elena, and Jose hung some posters. The tallest tree and second tallest trees had one poster each, the shortest tree had no posters. On the fifth day of class, Arya, Elena and Jose hung the last of their posters. The tallest tree had one poster, the second tallest had two posters, and the shortest had one poster.</p>\n<p>According to these events, which color does each person like?</p>"

        template_values = { 
            'user' : user,
            'url': log_in_out_url,
            'url_linktext': url_linktext,
            'clue_text': clue,
            'team_name': team_name
        }   
    
        template = JINJA_ENVIRONMENT.get_template('posters_riddle.html')
        self.response.write(template.render(template_values))

class Apartments(webapp2.RequestHandler):

    def post(self):
        user = users.get_current_user()
        team_name = get_users_team_name(user)
        challenge_name = "Apartment Riddle"
        challenge_number = 3
        message = ""
        
        clue = "In one of the Saadiyat apartments, the contractors had an option of how to build the double and single rooms. The requirements were that on one side of a hallway there needed to be six bedrooms but the builders could make them all doubles with two bedrooms in one room, all singles with one bedroom per room, or a mix of both. How many different ways could they have modeled the six bedrooms?"

        answer = "13"
        attempted_answer = self.request.get('attempted_answer')
        attempted_answer = attempted_answer.strip()
        attempted_answer = attempted_answer.upper()

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
                new_achievement = Achievement(challenge_name = challenge_name, team_email = user.email(), challenge_url = db.Link("http://saadiyatgames.appspot.com/apartments"), challenge_number = challenge_number)
                # may have issues with this link being absolute or not
                new_achievement.put()
                message += "New achievement added.\n"

            # self.redirect('/the next challenge')

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
    
        template = JINJA_ENVIRONMENT.get_template('apartments_puzzle.html')
        self.response.write(template.render(template_values))

    def get(self):
        user = users.get_current_user()
        team_name = ""

        if users.get_current_user():
            log_in_out_url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            team_name = get_users_team_name(user)
        else:
            log_in_out_url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        clue = "In one of the Saadiyat apartments, the contractors had an option of how to build the double and single rooms. The requirements were that on one side of a hallway there needed to be six bedrooms but the builders could make them all doubles with two bedrooms in one room, all singles with one bedroom per room, or a mix of both. How many different ways could they have modeled the six bedrooms?"

        template_values = { 
            'user' : user,
            'url': log_in_out_url,
            'url_linktext': url_linktext,
            'clue_text': clue,
            'team_name': team_name
        }   
    
        template = JINJA_ENVIRONMENT.get_template('apartments_puzzle.html')
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

class LiarsRiddle(webapp2.RequestHandler):

    def post(self):
        user = users.get_current_user()
        team_name = get_users_team_name(user)
        challenge_name = "Liars Riddle"
        message = ""
        
        clue = "Seven students have been caught cheating on a test and the administration is cracking down to see if they all cheated with each other and if perhaps a cheating ring is starting at NYUAD. During the interrogations, no one has said exactly who they&rsquo;ve cheated with but they have said how many other people they&rsquo;ve cheated with.\n Janet has admitted to cheating with all six other students, Bobby has admitted to cheating with five of the other students, Nir has admitted to cheating with four, Dias with three, Celine with two, Farhat with two, and Gustave with one of the other students.\n No student would say they&rsquo;re cheating with more people than they have been, but a few may say they&rsquo;ve cheated with fewer people than they have been.\n An anonymous tip says that Farhat is telling the truth and there is only one liar. Who is the liar if this is the case?"

        answer = "CELINE"
        attempted_answer = self.request.get('attempted_answer')
        attempted_answer = attempted_answer.strip()
        attempted_answer = attempted_answer.upper()

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
                new_achievement = Achievement(challenge_name = challenge_name, team_email = user.email(), challenge_url = db.Link("http://saadiyatgames.appspot.com/liarliar"), challenge_number = 2)
                # may have issues with this link being absolute or not
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
    
        template = JINJA_ENVIRONMENT.get_template('liars_riddle.html')
        self.response.write(template.render(template_values))

    def get(self):
        user = users.get_current_user()
        team_name = ""

        if users.get_current_user():
            log_in_out_url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            team_name = get_users_team_name(user)
        else:
            log_in_out_url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        clue = "Seven students have been caught cheating on a test and the administration is cracking down to see if they all cheated with each other and if perhaps a cheating ring is starting at NYUAD. During the interrogations, no one has said exactly who they&rsquo;ve cheated with but they have said how many other people they&rsquo;ve cheated with.\n Janet has admitted to cheating with all six other students, Bobby has admitted to cheating with five of the other students, Nir has admitted to cheating with four, Dias with three, Celine with two, Farhat with two, and Gustave with one of the other students.\n No student would say they&rsquo;re cheating with more people than they have been, but a few may say they&rsquo;ve cheated with fewer people than they have been.\n An anonymous tip says that Farhat is telling the truth and there is only one liar. Who is the liar if this is the case?"

        template_values = { 
            'user' : user,
            'url': log_in_out_url,
            'url_linktext': url_linktext,
            'clue_text': clue,
            'team_name': team_name
        }   
    
        template = JINJA_ENVIRONMENT.get_template('liars_riddle.html')
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
                new_achievement = Achievement(challenge_name = challenge_name, team_email = user.email(), challenge_url = db.Link("http://saadiyatgames.appspot.com/firstclue"), challenge_number = 1)
                # may have issues with this link being absolute or not
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
        team_name = ""

        if users.get_current_user():
            log_in_out_url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            team_name = get_users_team_name(user)
        else:
            log_in_out_url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        clue = "There is a special ten digit number. Each digit of the number is a count. The first digit is how many 0s are in trhe number, the second digit is how many 1s are in the number, the third digit is how many 2s are in the number, the fourth digit is how many 3s are in the number, ... , the tenth digit is how many 9s are in the number. What is this number?"

        template_values = { 
            'user' : user,
            'url': log_in_out_url,
            'url_linktext': url_linktext,
            'clue_text': clue,
            'team_name': team_name
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
                team_achievements = get_team_achievements(user.email(), "ASC")


        else:
            log_in_out_url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
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
    # Week 1
    (r'/firstclue', FirstClue),
    (r'/goose_chase', GooseChase),
    (r'/liarliar', LiarsRiddle),
    # Week 2
    (r'/apartments', Apartments),
    (r'/palmsandposters', Posters),
    # Week 3
    (r'/painters', Painters),
    (r'/meetandgreet', MeetingParty),
    # Week 4
    (r'/campuswalk', CampusWalk),
    (r'/temkeen', TemkeenGame),
    (r'/user/', UserHome),
    (r'/blog/(.*)/(.*)', BlogHome),
    (r'/post/(.*)/(.*)/(.*)', BlogpostPage),
    (r'/search/(.*)/(.*)/(.*)', TagSearchPage)
], debug=True)
