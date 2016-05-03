# Twitter-Bot


## Description

Simple Twitter-Bot with functions to get your followers list, store them (MongoDB) and send them welcome/farewell messages.

### twitter_api.py

Twitter functions Class.

### new_followers.py

#### Main module

`twitter.followers` call has 400ms sleeping time to avoid Twitter API time-outs. Several fields are extracted from the followers list (like description, location, lang, etc.) and stored into a MongoDB collection (into the `twitter_bot` database). New followers and lost followers are tracked. The collection `followers` is updated accordingly. Lost followers are keep track in a separate collection: `followers_archive`.

#### Messages

A preconfigured message is created for the new followers and a different one for the lost followers. The messages are inserted into a MongoDB collection called `queue`. In every execution (every time the code runs) a single message is extracted from the queue and sent. The oldest message is selected. After sending the message is deleted from the queue and also every other message waiting to be send to the same destination. This is done to avoid sending multiple greeting/farewell messages to spamers.

Note: No message will be send to a former follower.

### creds.py

Import file with your Twitter App credentials:

```
CONSUMER_KEY = 'xxxxxxxxxxxxxxxxxxxxxxxxx'
CONSUMER_SECRET = 'xxxxxxxxxxxxxxxxxxxxxxxxx'
OAUTH_TOKEN = 'xxxxxxxxxxxxxxxxxxxxxxxxx'
OAUTH_TOKEN_SECRET = 'xxxxxxxxxxxxxxxxxxxxxxxxx'
```

