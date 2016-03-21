#from mysql import MySQLDatabase
from twitter_api import TwitterAPI
import pymongo
import datetime

DEBUG = True

# MySQL datasource
#db = MySQLDatabase('twitter','twitter','twitter','localhost')

twitter = TwitterAPI()

# MongoDB datasource
def mongo_connect(database='test'):
    try:
        connection = pymongo.MongoClient()
        print "Mongo is connected!"
        return connection[database]

    except pymongo.errors.ConnectionFailure, e:
        print "Could not connect to MongoDB: %s" % e


# Add message to the queue for later delivery
def add_to_queue(screen_name, message):

    insert = '@'+screen_name+' '+message
    if len(insert) > 140 :
        print "ERROR: Message too long",insert,len(insert)
        return

    if DEBUG:
        print 'Adding to the queue: message:"@'+insert+'"  time_stamp: '+ str(datetime.datetime.utcnow())
    collection_statuses_queue.insert( {'message':insert,'time_stamp': datetime.datetime.utcnow() } )


# Mongo DB Name 'twitter_stream'
connection = mongo_connect('twitter')

# Mongo Collection name = 'my_collection'
collection_followers = connection['followers']

# To keep track of former followers
collection_followers_archive = connection['followers_archive']

# Outbound tweets queue
collection_statuses_queue = connection['queue']



# Get your current followers list from DB
followers_in_db = list (collection_followers.find())
if DEBUG:
    print "Print Followers in DB:", len(followers_in_db), followers_in_db

# Update this with your Twitter screen_name
#followers_in_twitter = twitter.get_followers('juan_domenech')
followers_in_twitter = [ {'lang': u'en', 'utc_offset': None, 'description': u'graphic designer, photographer, typography addict, avid hiker, foodie, wine lover & aspiring cake builder...', 'url': None, 'created_at': '2013-03-14 16:29:38', 'time_zone': None, 'name': u'Tara Shain', 'followers': 63, 'location': u'Barcelona, Catalonia', 'following': 134, '_id': 1267455212, 'listed_count': 10, 'screen_name': u'TaraShain'}, {'lang': u'es', 'utc_offset': 3600, 'description': u'Swapsee es tu mercado de talento local y plataforma de intercambio de habilidades. Haz networking, encuentra trabajos, talento, descuentos y mucho m\xe1s.', 'url': u'http://t.co/nWdqdPOnVO', 'created_at': '2012-10-15 10:57:14', 'time_zone': u'Madrid', 'name': u'Swapsee', 'followers': 1255, 'location': u'Barcelona, Madrid', 'following': 3205, '_id': 882085885, 'listed_count': 105, 'screen_name': u'myswapsee'}, {'lang': u'en', 'utc_offset': 3600, 'description': u'#Ecommerce can eliminate Homelessness. What are you doing to help homeless people? #HomelessEntrepreneur #eShowBCN16 #TransformingDigitalPeople', 'url': u'https://t.co/IcZlB8b78i', 'created_at': '2009-07-28 20:34:45', 'time_zone': u'Madrid', 'name': u'Andrew Funk', 'followers': 25732, 'location': u'Barcelona, Spain +34 697877089', 'following': 27547, '_id': 61011524, 'listed_count': 608, 'screen_name': u'andrewfunkspain'}, {'lang': u'en', 'utc_offset': -14400, 'description': u'Chief Strategist @vieodesign | Proud Mom | Gold #HubPartner | #HubSpotUserGroup Leader | \u2764\ufe0f#InboundMarketing, Psychology, digital media, wine, & chocolate', 'url': u'https://t.co/XjBUVXoEoU', 'created_at': '2010-06-16 05:30:09', 'time_zone': u'Eastern Time (US & Canada)', 'name': u'Holly Yalove', 'followers': 1784, 'location': u'Knoxville, TN', 'following': 1756, '_id': 156166657, 'listed_count': 164, 'screen_name': u'HollyYalove'}, {'lang': u'es', 'utc_offset': None, 'description': u'', 'url': None, 'created_at': '2010-12-20 21:58:04', 'time_zone': None, 'name': u'Marina Pie', 'followers': 65, 'location': u'', 'following': 84, '_id': 228862238, 'listed_count': 1, 'screen_name': u'MarinaPiegari'}, {'lang': u'en', 'utc_offset': 3600, 'description': u'The American Society of Barcelona is a non-profit organization providing English language business & social events in Barcelona.', 'url': u'http://t.co/gpS0T4EZZt', 'created_at': '2011-02-04 16:07:10', 'time_zone': u'Madrid', 'name': u'American Society BCN', 'followers': 1420, 'location': u'Barcelona, Spain', 'following': 2067, '_id': 247341544, 'listed_count': 47, 'screen_name': u'AmerSoc'}]

if DEBUG:
    print "Print Followers in Twitter:",len(followers_in_twitter), followers_in_twitter


# Compare Followers in Twitter with DB (to find new)
new_followers_today = twitter.get_difference(followers_in_db, followers_in_twitter)
if DEBUG:
    print "New Followers:", len(new_followers_today), new_followers_today

# Compare Followes in DB with Twitter (to find lost)
lost_followers_today = twitter.get_difference(followers_in_twitter, followers_in_db)
if DEBUG:
    print "Lost Followers:", len(lost_followers_today), lost_followers_today

welcome_message = 'Thanks for following! (This message has been sent using #Python. Would you like to know more? http://t.co/aaaaa )'
farewell_message = 'We are sad to see you go... Good luck! (This message has been sent using #Python. Would you like to know more? http://t.co/aaaaa )'

# Print out list of new followers
if new_followers_today:
    print "You have %i new followers!" % len(new_followers_today)
    for item in new_followers_today:

        print "Follower screen_name:",item['screen_name']," Inserting it into DB..."
        collection_followers.insert( item )

        print "Adding welcome message to the queue..."
        add_to_queue( item['screen_name'], welcome_message )

    print "DB updated."
    #collection_followers.insert_many( new_followers_today )
else:
    print "No new followers since the last execution :("

# Print out list of lost followers
if lost_followers_today:
    print "You have lost %i followers since the last execution :(" % len(lost_followers_today)
    for item in lost_followers_today:

        print "Follower screen_name:",item['screen_name'],"  Removing from DB..."
        collection_followers_archive.insert( item )
        collection_followers.remove( {'_id': item['_id'] } )

        print "Adding farewell message to the queue..."
        add_to_queue( item['screen_name'], farewell_message )

    print "DB updated."
else:
    print "No followers lost since the last execution! :)"




del collection_followers
del collection_followers_archive
del collection_statuses_queue
del connection
