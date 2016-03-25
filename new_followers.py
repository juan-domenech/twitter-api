from twitter_api import TwitterAPI
import pymongo
import datetime

DEBUG = True

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
        print 'ERROR: Message too long',insert,len(insert)
    else:
        if DEBUG:
            print 'Adding to the queue: message:"'+insert+'"  time_stamp: '+ str(datetime.datetime.utcnow())
        collection_statuses_queue.insert( {'screen_name':screen_name,'message':insert,'time_stamp':datetime.datetime.utcnow() } )


# Process the outbound message queue and send one of them out
def process_message_queue( count=1 ):

    queue_size = collection_statuses_queue.count()
    print 'Message queue size:',queue_size
    if queue_size == 0:
        print 'No message in the queue. Nothing to do.'
    else:
        for number in range (0, count):
            #item = collection_statuses_queue.find_one()

            # Get get the most recent message for a user and ignore possibly older ones
            item = collection_statuses_queue.find().sort([('_id', -1)]).limit(1)

            for element in item:
                if DEBUG:
                    print element
                message = element['message']
                screen_name = element['screen_name']

            # Message ready to send
            print 'Sending message from the queue: "'+message+'"'

            #
            twitter.send(message)
            #

            # Remove ALL the messages for this user to make sure that we won't send old stuff later
            if DEBUG:
                print 'Removing message(s) for screen_name: '+screen_name+' from the queue'
            collection_statuses_queue.remove({'screen_name':screen_name})

        print 'Message queue size when exiting:',collection_statuses_queue.count()


# Collections

# Mongo DB Name 'twitter_bot'
connection = mongo_connect('twitter_bot')

# Mongo Collection name = 'followers' for our current followers
collection_followers = connection['followers']

# Mongo Collection name = 'followers_archive' to keep track of former followers
collection_followers_archive = connection['followers_archive']

# Mongo Collection name = 'queue' for Outbound tweets queue
collection_statuses_queue = connection['queue']


# Get your current followers list from DB
followers_in_db = list (collection_followers.find())
if DEBUG:
    print "Print Followers in DB:", len(followers_in_db), followers_in_db

# Update this with your Twitter screen_name
followers_in_twitter = twitter.get_followers('juan_domenech')

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


# Preconfigured messages
welcome_message = 'Thanks for following! ( Message sent using #Python. Learn more at http://bit.ly/python-bot )'
farewell_message = 'We are sad to see you go... Good luck! ( Message sent using #Python. Learn more at http://bit.ly/python-bot )'


# Print out list of new followers
if new_followers_today:
    print "You have %i new followers!" % len(new_followers_today)
    for item in new_followers_today:

        print "Follower screen_name:",item['screen_name']," Inserting it into DB..."
        collection_followers.insert( item )

        print "Adding welcome message to the queue..."
        add_to_queue( item['screen_name'], welcome_message )

    print "DB updated."
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


# Check the message queue and send one message out if there is any
process_message_queue( count=1 )

del collection_followers
del collection_followers_archive
del collection_statuses_queue
del connection
