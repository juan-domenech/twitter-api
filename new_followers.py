from mysql import MySQLDatabase
from twitter_api import TwitterAPI

DEBUG = True

db = MySQLDatabase('twitter','twitter','twitter','localhost')

twitter = TwitterAPI()

followers_in_db = db.get_followers()
if DEBUG:
    print "Print Followers in DB:", followers_in_db

followers_in_twitter = twitter.get_followers('juan_domenech')
if DEBUG:
    print "Print Followers in Twitter:",followers_in_twitter

new_followers_today =  [item for item in set(followers_in_twitter) - set(followers_in_db) ]
if DEBUG:
    print new_followers_today

if new_followers_today:
    print "You have %i new followers!" % len(new_followers_today)
    print new_followers_today
    print "Inserting into DB..."
    db.insert_followers(new_followers_today)
else:
    print "No new followers today :("
