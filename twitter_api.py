DEBUG = True

import time
import tweepy
from tweepy import OAuthHandler

execfile('creds.py')

list = []
#follower = {}



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

    def contruct_user_object(self,user):

        follower = {}

        if DEBUG:
            print "User:",user

        follower['screen_name'] = user.screen_name
        follower['name'] = user.name
        follower['_id'] = user.id
        follower['description'] = user.description
        follower['url'] = user.url
        follower['followers'] = user.followers_count
        follower['following'] = user.friends_count
        follower['listed_count'] = user.listed_count
        follower['location'] = user.location
        follower['lang'] = user.lang
        follower['time_zone'] = user.time_zone
        follower['utc_offset'] = user.utc_offset
        follower['created_at'] = str(user.created_at)

        if DEBUG:
            print "User Object:",follower

        return follower


    # Get the whole list of followers by user name
    def get_followers(self,user):
        if DEBUG:
            print 'Getting Followers for user:',user

        list = []
        follower = {}
        user = tweepy.Cursor(self.twitter.followers, screen_name=user).items()

        while True:
            try:
                u = next(user)
                #list.append(str(u.screen_name))
                list.append(self.contruct_user_object(u))
                if DEBUG:
                    print "Screen Name:",u.screen_name, "Name:",u.name, "ID:",u.id, "Followers:",u.followers_count, "Following:",u._json['friends_count'], "Location:",u._json['location'], "Lang:",u._json['lang'], "Time Zone:",u._json['time_zone']
            except tweepy.TweepError as e:
                print "ERROR connecting to Twitter API!"
                print e.message[0]['code']
                print e.args[0][0]['code']
                print 'We got a timeout ... Sleeping for 15 minutes'
                time.sleep(15*60)
                u = next(user)
                list.append(self.contruct_user_object(u))
            except StopIteration:
                break

        if DEBUG:
            print "Twitter returned a total of %i followers (Sometimes there are duplicates)." % len(list)
            for item in list:
                print item
                print
        return list


    def get_difference(self,followers_a, followers_b):

        result = []

        for item_b in range(0,len(followers_b)) :

            present = False

            for item_a in range(0,len(followers_a)) :

                if followers_b[item_b]['_id'] == followers_a[item_a]['_id']:
                    present = True

            if not present:
                result.append(followers_b[item_b])
                if DEBUG:
                    print "Difference add item:",followers_b[item_b]

        if DEBUG:
            print "Difference Total: ",result

        return result


    # Place_ID for 'Dublin City, Ireland'
    def send(self,message, location = '7dde0febc9ef245b' ):

        if len(message) > 140 :
            print "ERROR: Message ' %s ' too long: %i" % (message, len(message) )
            return False

        self.twitter.update_status( status = message, place_id = location )

        if DEBUG:
            print "Message '%s' sent!" % message


