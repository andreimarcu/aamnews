aamnews
======
IRC feed parser with multiple channel/user capabilities.

Based on a very stripped down version of a fork of the IRC bot phenny by [mutantmonkey](https://github.com/mutantmonkey/phenny)

Requirements
------------
* Python 3.2+
* [python-requests](http://docs.python-requests.org/en/latest/)
* [tweepy](https://github.com/tweepy/tweepy)
* [praw](https://praw.readthedocs.org/en/v2.1.20/)
* ~~[feedparser](https://code.google.com/p/feedparser/)~~ - however right now it's manually overridden since some issues with python3 are not yet fixed in upstream.

Installation
------------

1. ```git clone https://github.com/andreimarcu/aamnews.git```
2. ```pip3 install -r requirements.txt```
3. Copy config.example.py to config.py and edit.
4. ```python3 phenny -c config.py```

Design
------
__Feeds__ are things you want updates from (RSS feeds, etc).  
__Channels__ have feeds.  
__Owners__ have channels.


Usage
-------

Once the bot connects to the IRC network, you can message it commands.  
The global owner, as defined in the config, can issue all commands and does not to need to be added to every channel's owners.

Right now, authentication for owners is done by hostname (very easy on oftc since there are registered username cloaks), however this might not be ideal for all networks. 

Commands
--------

#### Global owner (in any channel or in private message)

Start updating feeds
```
.start
```

Stop updating feeds
```
.stop
```

Add a channel (max_blast is the number of items to blast maximum per update, should be 0 for unlimited blasts) and join  
```
.add_channel "#channel" max_blast
```

Delete a channel and part
```
.del_channel #channel
```

List channels
```
.list_channels
```

Join all channels (happens at startup, but if bot was kicked, it can be useful)  
```
.join_channels
```

Add owner to a channel (to be done in said channel)
```
.add_owner hostname
```
Delete an owner from a channel (to be done in said channel)
```
.del_owner hostname
```

Add feeds to a (different) channel  
```
.add_feed_to_channel <type> "<channel>" "<name>" ("<options>", ...)  
```
```
.add_feed_to_channel rss "#channel" "Feed Name" "https://url"  
```
```
.add_feed_to_channel reddit_subreddit "#channel" "Feed Name" "subreddit_name" "new|top|hot"  
```
```
.add_feed_to_channel reddit_comments "#channel" "Feed Name" "https://url"  
```
```
.add_feed_to_channel reddit_search "#channel" "Feed Name" "subreddit_name" "search query"  
```
```
.add_feed_to_channel twitter_user "#channel" "Feed Name" "twitter_screenname" "yes|no" (with replies or without)   
```
```
.add_feed_to_channel twitter_search "#channel" "Feed Name" "search terms"  
```

#### Channel owner

Get max_blast
```
.max_blast
```

Set max_blast
```
.max_blast <max_blast>
```

Add a feed to a channel (to do in said channel)  
```
.add_feed <type> "<name>" ("<options>", ...)  
```
```
.add_feed rss "Feed Name" "https://url"  
```
```
.add_feed reddit_subreddit "Feed Name" "subreddit_name" "new|top|hot"  
```
```
.add_feed reddit_comments "Feed Name" "https://url"  
```
```
.add_feed reddit_search "Feed Name" "subreddit_name" "search query"  
```
```
.add_feed twitter_user "Feed Name" "twitter_screenname" "yes|no" (with replies or without)  
```
```
.add_feed twitter_search "Feed Name" "search terms"    
```

Delete a feed from a channel (to do in said channel)  
```
.del_feed Feed Name
```

##### Anyone
List feeds for current channel
```
.list_feeds
```

List owners for the current channel (to be done in said channel)
```
.list_owners
```


Logging
-------

Phenny's own console output will show details for every run (time spent, feeds that had items to blast, etc) 

Author
-------
Andrei Marcu, http://andreim.net/
