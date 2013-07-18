aamnews
======

IRC feed parser with multiple channel/user capabilities.

Based on a very stripped down version of a fork of the IRC bot phenny by [mutantmonkey](https://github.com/mutantmonkey/phenny)


Requirements
------------
* Python 3.2+
* [python-requests](http://docs.python-requests.org/en/latest/)
* [feedparser](https://code.google.com/p/feedparser/) - however right now it's manually overridden since some issues with python3 are not yet fixed in upstream.

Installation
------------
1. Edit config.py
2. Run ./phenny -c config.py
3. Enjoy!

Usage
-------
The owner of the bot should join the bot control channel, which is where the he can issue administrative commands and where the bot reports feed parsing errors, user actions, etc. 

Right now, authentication for the owner is done by hostname (very easy on oftc since there are registered username cloaks), however this might not be ideal for all networks. 

Commands: 
##### As bot owner
> .join_channels - Will join all channels 

List channels (in control channel)

> .list_channels

Add a channel (in control channel, bot will join) (limit should be 0 for unlimited blasts)

> .add_channel "#channel" "owner_hostname" "limit_blast_per_feed_in_seconds"

Delete a channel (in control channel, bot will part)

> .del_channel "#channel"


##### As channel owner
Add a feed to a channel (to do in said channel)

> .add_feed "Feed Name" "http://feed.url"

Delete a feed from a channel (to do in said channel)

> .del_feed "Feed Name"

##### As anyone
List feeds for current channel
> .list_feeds


#### Logging:
- Phenny's own console output will show details for every run (time spent, feeds that had items to blast, etc) 
- The control channel will report feed parsing errors and non-owner actions


To Do
-----
- A lot of refactoring
- Use SQLAlchemy
- Allow multiple owners for a channel



Author
-------
Andrei Marcu, http://andreim.net/
