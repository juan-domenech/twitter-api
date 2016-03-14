DEBUG = True

import time
import tweepy
from tweepy import OAuthHandler

execfile('creds.py')

class TwitterAPI:
    def __init__ (self ) :
        try:
            auth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
            auth.set_access_token(OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
            self.twitter = tweepy.API(auth)
            if DEBUG:
                print "Connected to Twitter!"
        except tweepy.TweepError as e:
            print "ERROR connecting to Twitter API!"
            print e.message[0]['code']
            print e.args[0][0]['code']

    def __del__( self ):
        if hasattr(self, 'twitter'):
            #self.twitter.close()
            if DEBUG:
                print "Twitter Connection Closed."


    # Get the whole list of followers by user name
    def get_followers(self,user):
        if DEBUG:
            print 'Getting Followers for user:',user

        list = []
        user = tweepy.Cursor(self.twitter.followers, screen_name=user).items()

        while True:
            try:
                u = next(user)
                list.append(str(u.screen_name))
                if DEBUG:
                    print "Screen Name:",u.screen_name, "Name:",u.name, "ID:",u.id, "Followers:",u.followers_count, "Friends:",u._json['friends_count'], "Location:",u._json['location'], "Lang:",u._json['lang'], "Time Zone:",u._json['time_zone']
            except tweepy.TweepError as e:
                print "ERROR connecting to Twitter API!"
                print e.message[0]['code']
                print e.args[0][0]['code']
                print 'We got a timeout ... Sleeping for 15 minutes'
                time.sleep(15*60)
                u = next(user)
                list.append(str(u.screen_name))
            except StopIteration:
                break

        if DEBUG:
            print "Total followers:",len(list)
            print list
        return list

