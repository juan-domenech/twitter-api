from twitter_api import TwitterAPI
import pymongo
import datetime
import time
import sys


# Print Debug messages
def print_DEBUG(message):
    if DEBUG:
        print 'DEBUG: '+message


# Print help message
def print_help():
    print '--queue      process messages in the queue and exit'
    print '--dry-run    run in dry-run mode (no messages will be sent)'
    print '--debug      enable debug mode'
    print '--help       print this message'
    print


# MongoDB datasource
def mongo_connect(database='test'):
    try:
        connection = pymongo.MongoClient()
        print "Mongo is connected!"
        return connection[database]

    except pymongo.errors.ConnectionFailure, e:
        print "Could not connect to MongoDB: %s" % e


def check_today_run():
    # Get today entries in collection track (stats)
    #execute = {'time_stamp' : { '$gte' : 'new ISODate('+str(time.strftime("%Y-%m-%d"))+')' } }
    #if DEBUG:
    #    print "Mongo:",execute
    #result = collection_track.find( execute )

    # Get the latest entry in the collection
    result = collection_track.find().sort([('_id', -1)]).limit(1)
    if DEBUG:
        print result[0]

    # Search for today date (in '2016, 4, 3' format) present in the last entry of the collection
    if time.strftime("%Y,%_m,%_d") in str(result[0]):
        # Today date present. This task ran sometime today.
        if DEBUG:
            print "Entries present in collection_track for today."
        return True
    else:
        # Today not present. This task hasn't run today.
        if DEBUG:
            print "No entries in collection_track for today."
        return False


def store_stats(current_followers, new_followers_today, lost_followers_today, queue_size):
    if DEBUG:
        print "collection_stats.insert current_followers:",current_followers,"new_followers_today:",new_followers_today,"lost_followers_today",lost_followers_today,"queue_size:",queue_size
    collection_track.insert( {'time_stamp':datetime.datetime.utcnow(), 'current_followers':current_followers, 'new_followers_today':new_followers_today,'lost_followers_today':lost_followers_today,'queue_size':queue_size } )


# Add message to the queue for later delivery
def add_to_queue(screen_name, message, priority='low'):

    insert = '@'+screen_name+' '+message
    if len(insert) > 140 :
        print 'ERROR: Message too long',insert,len(insert)
    else:
        if DEBUG:
            print 'Adding to the queue: message:"'+insert+'"  time_stamp: '+ str(datetime.datetime.utcnow())+' with priority: '+str(priority)
        collection_statuses_queue.insert( {'screen_name':screen_name,'message':insert,'time_stamp':datetime.datetime.utcnow(), 'priority':priority } )


# Send a single Twitter message and delete any other pending messages for that user
def send_one_message_and_remove(screen_name, message):

    print 'Sending message to:',screen_name
    print_DEBUG(str(message))

    if dry_run:
        print "We are in dry_run. NOT sending this message:",message
    else:
        twitter.send(message)

    if dry_run:
        print "We are in dry_run. NOT removing any message from the queue for screen_name:",screen_name
        return
    else:
        # Remove ALL the messages for this user to make sure that we won't send old stuff later
        print_DEBUG('Removing message(s) for screen_name: '+screen_name+' from the queue')
        collection_statuses_queue.remove({'screen_name':screen_name})
        return


# Process the outbound message queue and send one message out
def process_message_queue( dry_run ):

    # In either case send one message tops
    limit = 1

    if dry_run:
        print "process_message_queue() is in dry_run mode. No messages will be sent and the queue won't be altered."

    # When no queue -> exit
    if collection_statuses_queue.count() == 0 :
        print 'No message in the queue. Nothing to do.'
        return 0

    # If there is something in the queue with priority == high. Process and return.
    elif collection_statuses_queue.find({'priority':'high'}).count() != 0 :

        # Get oldest message with priority == high (sort by time_stamp, the oldest first)
        item = next( collection_statuses_queue.find({'priority':'high'}).sort([('time_stamp', 1)]).limit(limit) )
        print_DEBUG('Result for priority == high: '+str(item))

        # print_DEBUG('No messages with priority == high pending to send.')
        screen_name = item['screen_name']
        message = item['message']
        send_one_message_and_remove(screen_name, message)

        queue_size = collection_statuses_queue.find({'priority':'high'}).count()
        print 'Messages pending in the queue with priority == high: ',queue_size

        total_queue_size = collection_statuses_queue.count()
        print 'Total messages pending in the queue: ',collection_statuses_queue.count()
        return total_queue_size


    # Not hit for high priority. Let's try any other priority (sort by time_stamp, the oldest first)
    else:

        print_DEBUG("No messages for priority = high. Checking for any other priority.")
        item = next( collection_statuses_queue.find({'priority':{'$ne':'high'}}).sort([('time_stamp', 1)]).limit(limit) )
        print_DEBUG("Result for priority != high: "+str(item))

        screen_name = item['screen_name']
        message = item['message']
        send_one_message_and_remove(screen_name, message)

        queue_size = collection_statuses_queue.find({'priority':{'$ne':'high'}}).count()
        print 'Messages pending in the queue with priority low or med: ',queue_size

        total_queue_size = collection_statuses_queue.count()
        print 'Total messages in pending the queue: ',total_queue_size
        return total_queue_size



### Main

# Obtaining argument list form command line
arguments = sys.argv

# The first argument is our program name. Let's use it.
running_name = arguments[0]

# Discarding first elements of the list
arguments = arguments[1:]

# Set DEBUG mode
if '--debug' in arguments:
    DEBUG = True
    print_DEBUG('Running '+str(running_name))
    print_DEBUG('Debug enabled')
else:
    DEBUG = False


# Is '--help' present? Then print Help and exit(0)
if '--help' in arguments:
    print_DEBUG('Help called')
    print_help()
    exit(0)


twitter = TwitterAPI()


# Collections

# Mongo DB Name 'twitter_bot'
connection = mongo_connect('twitter_bot')

# Mongo Collection name = 'track' to store a couple of metrics
# Is going to be helpful to detect whether or not we already run today
collection_track = connection['track']

# Mongo Collection name = 'followers' for our current followers
collection_followers = connection['followers']

# Mongo Collection name = 'followers_archive' to keep track of former followers
collection_followers_archive = connection['followers_archive']

# Mongo Collection name = 'queue' for Outbound tweets queue
collection_statuses_queue = connection['queue']



# Check for "--dry-run". When enabled no messages from the queue will be sent.
if '--dry-run' in arguments:
    dry_run = True
    print_DEBUG('--dry-run == True')
else:
    dry_run = False
    print_DEBUG('--dry-run == False')


# Check for "process only queue command" present on the command line. In that case process+exit
if '--queue' in arguments:
    print "--queue == True. Processing Queue only."

    # Check the message queue and send one message out if there is any
    process_message_queue( dry_run )

    exit(0)


# Check whether we ran this task today already
# We want this task to run only once a day
if check_today_run():
    if DEBUG:
        print "Task already executed today. Exiting."
    exit(0)
else:
    if DEBUG:
        print "Task not executed today. Let's run."


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
        add_to_queue( item['screen_name'], welcome_message, priority='high' )

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
        add_to_queue( item['screen_name'], farewell_message, priority='low' )

    print "DB updated."
else:
    print "No followers lost since the last execution! :)"


# Check the message queue and send one message out if there is any
queue_size = process_message_queue( dry_run )

# Store stats
store_stats(len(followers_in_twitter), len(new_followers_today), len(lost_followers_today), queue_size)

del collection_followers
del collection_followers_archive
del collection_statuses_queue
del collection_track
del connection
