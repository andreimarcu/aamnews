# -*- coding: utf-8 -*-

"""
aamnews.py - Feed Parsing Module
Copyright 2013-2015, Andrei Marcu, andreim.net

https://github.com/andreimarcu/aamnews
"""
from time import time, ctime, sleep
import localfeedparser as feedparser
from config import shorten_url
import requests
import sqlite3
import tweepy
import praw
import re

try:
    import html.parser
    unescape = html.parser.HTMLParser().unescape
except:
    import html
    unescape = html.unescape


running = False

def init(p):
    """Performed on startup"""
    conn = sqlite3.connect("aamnews.db")

    if p.config.ssl_verify == False:
        requests.packages.urllib3.disable_warnings()

    # Init db
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS feeds (id integer primary key autoincrement, type_name)")
    c.execute("CREATE TABLE IF NOT EXISTS feed_rss (id integer primary key autoincrement, feed_id, url)")
    c.execute("CREATE TABLE IF NOT EXISTS feed_reddit_subreddit (id integer primary key autoincrement, feed_id, name, sort)")
    c.execute("CREATE TABLE IF NOT EXISTS feed_reddit_comments (id integer primary key autoincrement, feed_id, article_id)")
    c.execute("CREATE TABLE IF NOT EXISTS feed_reddit_search (id integer primary key autoincrement, feed_id, subreddit_name, query)")
    c.execute("CREATE TABLE IF NOT EXISTS feed_twitter_user (id integer primary key autoincrement, feed_id, username, replies)")
    c.execute("CREATE TABLE IF NOT EXISTS feed_twitter_search (id integer primary key autoincrement, feed_id, query)")
    c.execute("CREATE TABLE IF NOT EXISTS items (id integer primary key autoincrement, feed_id, unique_id)")
    c.execute("CREATE TABLE IF NOT EXISTS channels (id integer primary key autoincrement, name, max_blast)")
    c.execute("CREATE TABLE IF NOT EXISTS owners (id integer primary key autoincrement, hostname)")
    c.execute("CREATE TABLE IF NOT EXISTS channel_owners (id integer primary key autoincrement, owner_id, channel_id)")
    c.execute("CREATE TABLE IF NOT EXISTS channel_feeds (id integer primary key autoincrement, feed_id, channel_id, name)")

    # Delete existing items
    c.execute("DELETE FROM items")
    conn.commit()

    # Join channels we currently have in the db
    c.execute("SELECT name from channels")
    channels = [a[0] for a in c.fetchall()]

    conn.close()

    if len(channels) > 0:
        for channel in channels:
            p.write(['JOIN'], channel)


def join_channels(p, i):
    if i.host == p.config.owner_host:

        conn = sqlite3.connect("aamnews.db")
        c = conn.cursor()
    
        c.execute("SELECT name from channels")
        channels = [a[0] for a in c.fetchall()]

        conn.close()

        if len(channels) > 0:
            for channel in channels:
                p.write(['JOIN'], channel)

            return p.say("Joined " + ", ".join(channels))
        else:
            return p.say("No channels to join")

join_channels.commands = ['join_channels']
join_channels.threading = True
join_channels.priority = "medium"


def add_feed_to_channel(p, i):
    try:
        m = re.match(r'(\w+)\s"([^"]+)"\s"([^"]+)"\s"([^"]+)"(?:\s"([^"]+)")?', i.group(2))
        type = m.group(1)

        try:
            channel = m.group(2)
            name = m.group(3)
            option_1 = m.group(4)
            option_2 = m.group(5)

            if type == "rss":
                url = option_1

                return aamnews_add_feed_rss_to_channel(p, i, channel, name, url)

            elif type == "reddit_subreddit":
                subreddit = option_1
                sort = option_2

                return aamnews_add_feed_reddit_subreddit(p, i, channel, name, subreddit, sort)

            elif type == "reddit_comments":
                url = option_1

                return aamnews_add_feed_reddit_comments(p, i, channel, name, url)

            elif type =="reddit_search":
                subreddit = option_1
                query = option_2

                return aamnews_add_feed_reddit_search(p, i, channel, name, subreddit, query)

            elif type == "twitter_user":
                user = option_1
                replies = 1 if option_2 == "yes" else 0

                return aamnews_add_feed_twitter_user(p, i, channel, name, user, replies)

            elif type == "twitter_search":
                query = option_1

                return aamnews_add_feed_twitter_search(p, i, channel, name, query)

            else:
                return p.say("Feed type not recognized.")

        except:
            if type == "rss":
                return p.say('.add_feed_to_channel rss "<channel>" "<name>" "<url>"')
            elif type == "reddit_subreddit":
                return p.say('.add_feed_to_channel reddit_subreddit "<channel>" "<name>" "<subreddit>" "<sort>"')
            elif type == "reddit_comments":
                return p.say('.add_feed_to_channel reddit_comments "<channel>" "<name>" "<url>"')
            elif type == "reddit_search":
                return p.say('.add_feed_to_channel reddit_search "<channel>" "<name>" "<subreddit>" "<query>"')
            elif type == "twitter_user":
                return p.say('.add_feed_to_channel twitter_user "<channel>" "<name>" "<twitter_user>" "<replies (yes|no)>"')
            elif type == "twitter_search":
                return p.say('.add_feed_to_channel twitter_search "<channel>" "<name>" "<query>"')
            else:
                raise
    except:
        return p.say('.add_feed_to_channel <type> "<channel>" "<name>" ("<options>", ...)')

add_feed_to_channel.commands = ["add_feed_to_channel"]
add_feed_to_channel.priority = "medium"
add_feed_to_channel.threading = True


def add_feed(p, i):
    channel = i.sender
    hostname = i.host

    try:
        m = re.match(r'(\w+)\s"([^"]+)"\s"([^"]+)"(?:\s"([^"]+)")?', i.group(2))
        type = m.group(1)

        try:
            name = m.group(2)
            option_1 = m.group(3)
            option_2 = m.group(4)

            if type == "rss":
                url = option_1
                return aamnews_add_feed_rss_to_channel(p, i, channel, name, url)

            elif type == "reddit_subreddit":
                subreddit = option_1
                sort = option_2

                return aamnews_add_feed_reddit_subreddit(p, i, channel, name, subreddit, sort)

            elif type == "reddit_comments":
                url = option_1

                return aamnews_add_feed_reddit_comments(p, i, channel, name, url)

            elif type =="reddit_search":
                subreddit = option_1
                query = option_2

                return aamnews_add_feed_reddit_search(p, i, channel, name, subreddit, query)

            elif type == "twitter_user":
                user = option_1
                replies = 1 if option_2 == "yes" else 0

                return aamnews_add_feed_twitter_user(p, i, channel, name, user, replies)

            elif type == "twitter_search":
                query = option_1

                return aamnews_add_feed_twitter_search(p, i, channel, name, query)

            else:
                return p.say("Feed type not recognized.")

        except:
            if type == "rss":
               return p.say('.add_feed rss "<name>" "<url>"')
            elif type == "reddit_subreddit":
                return p.say('.add_feed reddit_subreddit "<name>" "<subreddit>" "<sort>"')
            elif type == "reddit_comments":
                return p.say('.add_feed reddit_comments "<name>" "<url>"')
            elif type == "reddit_search":
                return p.say('.add_feed reddit_search "<name>" "<subreddit>" "<query>"')
            elif type == "twitter_user":
                return p.say('.add_feed twitter_user "<name>" "<twitter_user>" "<replies (yes|no)>"')
            elif type == "twitter_search":
                return p.say('.add_feed twitter_search "<name>" "<query>"')
            else:
                raise
    except:
        return p.say('.add_feed <type> "<name>" ("<options>", ...)')

add_feed.commands = ["add_feed"]
add_feed.priority = "medium"
add_feed.threading = True


def delete_feed(p, i):

    name = i.group(2)
    channel = i.sender

    if not name:
        return p.say(".del_feed <name>")

    conn = sqlite3.connect("aamnews.db")
    c = conn.cursor()

    # Get channel's id
    c.execute("SELECT id FROM channels WHERE name=?", (channel,))
    channel_id = c.fetchone()[0]

    # determine if person owns channel
    if not aamnews_owns_channel(p, channel_id, i.host):
        conn.close()
        return p.say("You must be a channel owner.")

    # Check if valid feed and get feed_id
    c.execute("SELECT feed_id FROM channel_feeds WHERE name=? AND channel_id=?", (name, channel_id))
    result = c.fetchone()

    if result == None:
        return p.say("Feed does not exist.")

    feed_id = result[0]

    # remove from this channel
    c.execute("DELETE FROM channel_feeds WHERE feed_id=? AND channel_id=?", (feed_id, channel_id))

    # check if orphan
    c.execute("SELECT channel_id FROM channel_feeds WHERE feed_id=?", (feed_id,))
    if c.fetchone() == None:
        # Delete any of its items
        c.execute("DELETE FROM items WHERE feed_id=?", (feed_id,))

        # Get feed type
        c.execute("SELECT type_name FROM feeds WHERE id=?", (feed_id,))
        feed_type = c.fetchone()[0]

        if feed_type == "rss":
            # Delete from feed_rss
            c.execute("DELETE FROM feed_rss WHERE feed_id=?", (feed_id,))

        elif feed_type == "reddit_subreddit":
            c.execute("DELETE FROM feed_reddit_subreddit WHERE feed_id=?", (feed_id,))

        elif feed_type == "reddit_comments":
            c.execute("DELETE FROM feed_reddit_comments WHERE feed_id=?", (feed_id,))

        elif feed_type == "reddit_search":
            c.execute("DELETE FROM feed_reddit_search WHERE feed_id=?", (feed_id,))
        
        elif feed_type == "twitter_user":
            c.execute("DELETE FROM feed_twitter_user WHERE feed_id=?", (feed_id,))
        
        elif feed_type == "twitter_search":
            c.execute("DELETE FROM feed_twitter_search WHERE feed_id=?", (feed_id,))

        # Delete from feeds
        c.execute("DELETE FROM feeds WHERE id=?", (feed_id,))

    conn.commit()
    conn.close()

    return p.say(name + " has been deleted.")

delete_feed.commands = ["del_feed"]
delete_feed.priority = "medium"
delete_feed.threading = True


def list_feeds(p, i):
    channel = i.sender

    conn = sqlite3.connect("aamnews.db")
    c = conn.cursor()

    # Get channel's id
    c.execute("SELECT id FROM channels WHERE name=?", (channel,))
    channel_id = c.fetchone()[0]

    # Get chanel's feeds
    c.execute("SELECT name FROM channel_feeds WHERE channel_id=?", (channel_id,))
    feeds = [e[0] for e in c.fetchall()]

    conn.close()

    if len(feeds) == 0:
        return p.say("No feeds for " + channel)
    else:
        return p.say("Feeds: " + ", ".join(feeds))

list_feeds.commands = ["list_feeds"]
list_feeds.priority = "medium"
list_feeds.threading = True


def add_channel(p, i):

    hostname = i.host

    if hostname == p.config.owner_host:

        try:
            m = re.match(r'"(.*)"\s(\d+)', i.group(2))
            channel = m.group(1)
            max_blast = m.group(2)

            conn = sqlite3.connect("aamnews.db")
            c = conn.cursor()

            # check if channel already exists.
            c.execute("SELECT id FROM channels WHERE name=?", (channel,))
            result = c.fetchone()

            if result != None:
                return p.say("Channel already exists.")

            c.execute("INSERT INTO channels (name, max_blast) VALUES (?,?)", (channel, max_blast))
            conn.commit()
            conn.close()

            p.write(['JOIN'], channel)
            return p.say("Added and trying to join " + channel)

        except:
            return p.say('.add_channel "<channel_name>" <max_blast>')

    else:
        return p.say("Command is global owner only.")

add_channel.commands = ["add_channel"]
add_channel.priority = "medium"
add_channel.threading = True



def delete_channel(p, i):
    hostname = i.host

    if hostname == p.config.owner_host:
        channel = i.group(2)

        if not channel:
            return p.say(".del_channel <channel_name>")

        conn = sqlite3.connect("aamnews.db")
        c = conn.cursor()

        # check if channel exists.
        c.execute("SELECT id FROM channels WHERE name=?", (channel,))
        result = c.fetchone()

        if result == None:
            conn.close()
            return p.say("Channel doesn't exist.")

        channel_id = result[0]

        # Get list of owners ids
        c.execute("SELECT owner_id FROM channel_owners WHERE channel_id=?", (channel_id,))
        owners = [e[0] for e in c.fetchall()]

        # Delete owners from channel_owners
        c.execute("DELETE FROM channel_owners WHERE channel_id=?", (channel_id,))

        # Check if previous owners have any other channels
        for owner_id in owners:
            c.execute("SELECT channel_id FROM channel_owners WHERE owner_id=?", (owner_id,))
            result = c.fetchone()

            if result == None:
                # Owner has no other channels, delete.
                c.execute("DELETE FROM owners WHERE id=?", (owner_id,))

        # Get list of feeds ids
        c.execute("SELECT feed_id FROM channel_feeds WHERE channel_id=?", (channel_id,))
        feeds = [e[0] for e in c.fetchall()]

        # Delete from channel_feeds
        c.execute("DELETE FROM channel_feeds WHERE channel_id=?", (channel_id,))

        # Check if previous feeds have any other channels, if not delete 
        for feed_id in feeds:
            c.execute("SELECT channel_id FROM channel_feeds WHERE feed_id=?", (feed_id,))
            result = c.fetchone()

            if result == None:
                # Feed has no other channels, delete
                aamnews_delete_feed(feed_id)

        # Delete from channels
        c.execute("DELETE FROM channels WHERE name=?", (channel,))
        conn.commit()
        conn.close()

        p.write(['PART'], channel)
        return p.say("Deleted and parted channel " + channel)

delete_channel.commands = ["del_channel"]
delete_channel.priority = "medium"
delete_channel.threading = True


def add_owner(p, i):
    if i.host == p.config.owner_host:
        channel = i.sender
        hostname = i.group(2)

        conn = sqlite3.connect("aamnews.db")
        c = conn.cursor()

        # Get channel's id
        c.execute("SELECT id FROM channels WHERE name=?", (channel,))
        channel_id = c.fetchone()[0]

        # Get chanel's owners
        c.execute("SELECT owners.hostname FROM owners INNER JOIN channel_owners ON owners.id=channel_owners.owner_id WHERE channel_id=?", (channel_id,))
        owners = [p.config.owner_host] + [e[0] for e in c.fetchall()]

        if hostname in owners:
            conn.close()
            return p.say("Owner already exists.")
        else:
            # check if owner in owners 
            c.execute("SELECT id FROM owners where hostname=?", (hostname,))
            result = c.fetchone()

            if result:
                owner_id = result[0]
            else:
                c.execute("INSERT INTO owners (hostname) VALUES (?)", (hostname,))
                owner_id = c.lastrowid

            c.execute("INSERT INTO channel_owners (owner_id, channel_id) VALUES (?,?)", (owner_id, channel_id))

            conn.commit()
            conn.close()

            return p.say("Added owner.")

    else:
        return p.say("Command is global owner only.")

add_owner.commands = ["add_owner"]
add_owner.priority = "medium"
add_owner.threading = True


def del_owner(p, i):
    if i.host == p.config.owner_host:
        channel = i.sender
        hostname = i.group(2)

        conn = sqlite3.connect("aamnews.db")
        c = conn.cursor()

        # Get channel's id
        c.execute("SELECT id FROM channels WHERE name=?", (channel,))
        channel_id = c.fetchone()[0]

        # Get chanel's owners
        c.execute("SELECT owners.hostname FROM owners INNER JOIN channel_owners ON owners.id=channel_owners.owner_id WHERE channel_id=?", (channel_id,))
        owners = [p.config.owner_host] + [e[0] for e in c.fetchall()]

        if hostname in owners:
            # Get owner_id
            c.execute("SELECT id FROM owners where hostname=?", (hostname,))
            owner_id = c.fetchone()[0]

            c.execute("DELETE FROM channel_owners WHERE owner_id=? AND channel_id=?", (owner_id, channel_id))

            # Check if owner has other channels
            c.execute("SELECT channel_id FROM channel_owners WHERE owner_id=?", (owner_id,))
            result = c.fetchone()

            if not result:
                c.execute("DELETE FROM owners WHERE id=?", (owner_id,))

            conn.commit()
            conn.close()

            return p.say("Deleted owner.")

        else:
            conn.close()
            return p.say("Owner doesn't exist.")
    else:
        return p.say("Command is global owner only.")

del_owner.commands = ["del_owner"]
del_owner.priority = "medium"
del_owner.threading = True


def list_owners(p, i):

    channel = i.sender

    conn = sqlite3.connect("aamnews.db")
    c = conn.cursor()

    # Get channel's id
    c.execute("SELECT id FROM channels WHERE name=?", (channel,))
    channel_id = c.fetchone()[0]

    # Get chanel's owners
    c.execute("SELECT owners.hostname FROM owners INNER JOIN channel_owners ON owners.id=channel_owners.owner_id WHERE channel_id=?", (channel_id,))
    owners = [p.config.owner_host] + [e[0] for e in c.fetchall()]

    conn.close()

    return p.say("Channel owned by: " + ", ".join(owners))

list_owners.commands = ["list_owners"]
list_owners.priority = "medium"
list_owners.threading = True


def list_channels(p, i):
    hostname = i.host

    if hostname == p.config.owner_host:

        conn = sqlite3.connect("aamnews.db")
        c = conn.cursor()

        c.execute("SELECT name FROM channels")
        channels = [e[0] for e in c.fetchall()]

        conn.close()

        if len(channels) == 0:
            return p.say("No channels")
        else:
            return p.say("Channels: " + ", ".join(channels))

list_channels.commands = ["list_channels"]
list_channels.priority = "medium"
list_channels.threading = True


def max_blast(p, i):

    hostname = i.host
    channel = i.sender
    max_blast = i.group(2)

    conn = sqlite3.connect("aamnews.db")
    c = conn.cursor()

    # Get channel's id
    c.execute("SELECT id FROM channels WHERE name=?", (channel,))
    channel_id = c.fetchone()[0]


    if max_blast != None and aamnews_owns_channel(p, channel_id, hostname):
        try:
            max_blast = int(max_blast)
    
            c.execute("UPDATE channels SET max_blast=? WHERE id=?", (max_blast, channel_id))
            conn.commit()
            conn.close()

            return p.say("Max blast for this channel is now " + str(max_blast))
        except:
            conn.close()
            return p.say(".max_blast (<max_blast>)")

    else:
        c.execute("SELECT max_blast FROM channels WHERE id=?", (channel_id,))
        max_blast = c.fetchone()[0]
        
        conn.close()

        return p.say("Max blast for this channel is " + str(max_blast))

max_blast.commands = ["max_blast"]
max_blast.priority = "medium"
max_blast.threading = True


def start_aamnews(p, i):
    global running

    if i.host == p.config.owner_host:
        if running:
            return p.say("Already running.")
        else:
            return aamnews_loop(p)

start_aamnews.commands = ['start']
start_aamnews.threading = True
start_aamnews.priority = "medium"


def stop_aamnews(p, i):
    global running

    if i.host == p.config.owner_host:
        if running:
            running = False
            return p.say("Ordered to stop.")
        else:
            return p.say("Already stopped.")

stop_aamnews.commands = ['stop']
stop_aamnews.threading = True
stop_aamnews.priority = "medium"


def aamnews_owns_channel(p, channel_id, hostname):
    conn = sqlite3.connect("aamnews.db")
    c = conn.cursor()

    c.execute("SELECT hostname FROM owners INNER JOIN channel_owners ON owners.id=channel_owners.owner_id")
    owners = [e[0] for e in c.fetchall()]

    conn.close()

    return hostname in owners or hostname == p.config.owner_host


def aamnews_delete_feed(feed_id):
    conn = sqlite3.connect("aamnews.db")
    c = conn.cursor()

    c.execute("SELECT channel_id FROM channel_feeds WHERE feed_id=?", (feed_id,))
    if c.fetchone() == None:
        # Delete any of its items
        c.execute("DELETE FROM items WHERE feed_id=?", (feed_id,))

        # Get feed type
        c.execute("SELECT type_name FROM feeds WHERE id=?", (feed_id,))
        feed_type = c.fetchone()[0]

        if feed_type == "rss":
            # Delete from feed_rss
            c.execute("DELETE FROM feed_rss WHERE feed_id=?", (feed_id,))

        # Delete from feeds
        c.execute("DELETE FROM feeds WHERE id=?", (feed_id,))

    conn.commit()
    conn.close()


def aamnews_add_feed_reddit_subreddit(p, i, channel, name, subreddit, sort):
    hostname = i.host

    if not sort in ["hot", "new", "top"]:
        return p.say("Sort must be hot, new or top.")

    conn = sqlite3.connect("aamnews.db")
    c = conn.cursor()

    # Check if channel exists
    c.execute("SELECT id FROM channels WHERE name=?", (channel,))
    result = c.fetchone()

    if result == None:
        return p.say("Channel does not exist.")

    channel_id = result[0]

    # determine if person owns channel
    if not aamnews_owns_channel(p, channel_id, hostname):
        return p.say("You must be a channel owner.")

    # check if name is already in use for another feed in this channel
    c.execute("SELECT feed_id FROM channel_feeds WHERE channel_id=? AND name=?", (channel_id, name))
    if c.fetchone() != None:
        return p.say("Name is already in use for another feed in this channel.")

    try:
        # Check if feed already exists for another channel
        c.execute("SELECT feed_id FROM feed_reddit_subreddit WHERE name=? AND sort=?", (subreddit, sort))
        result = c.fetchone()

        if result == None:

            r = praw.Reddit("aamnews by /u/andreim at github.com/andreimarcu/aamnews")
            sub = r.get_subreddit(subreddit)

            if sort == "hot":
                items = [e for e in sub.get_hot(limit=100)]
            elif sort == "top":
                items = [e for e in sub.get_top(limit=100)]
            elif sort == "new":
                items = [e for e in sub.get_new(limit=100)]

            c.execute("INSERT INTO feeds (type_name) VALUES (?)", ("reddit_subreddit",))
            feed_id = c.lastrowid

            c.execute("INSERT INTO feed_reddit_subreddit (feed_id, name, sort) VALUES (?,?,?)", (feed_id, subreddit, sort))

            for item in items:
                c.execute("INSERT INTO items (feed_id, unique_id) VALUES (?,?)", (feed_id, item.id))

        else:
            feed_id = result[0]

        c.execute("INSERT INTO channel_feeds (feed_id, channel_id, name) VALUES (?,?,?)", (feed_id, channel_id, name))

        conn.commit()
        conn.close()

        return p.say("Added " + name)


    except Exception as exc:
        conn.close()
        return p.say("Connection Error: " + str(exc))


def aamnews_add_feed_reddit_comments(p, i, channel, name, url):
    hostname = i.host

    conn = sqlite3.connect("aamnews.db")
    c = conn.cursor()

    # Check if channel exists
    c.execute("SELECT id FROM channels WHERE name=?", (channel,))
    result = c.fetchone()

    if result == None:
        return p.say("Channel does not exist.")

    channel_id = result[0]

    # determine if person owns channel
    if not aamnews_owns_channel(p, channel_id, hostname):
        return p.say("You must be a channel owner.")

    # check if name is already in use for another feed in this channel
    c.execute("SELECT feed_id FROM channel_feeds WHERE channel_id=? AND name=?", (channel_id, name))
    if c.fetchone() != None:
        return p.say("Name is already in use for another feed in this channel.")

    try:
        r = praw.Reddit("aamnews by /u/andreim at github.com/andreimarcu/aamnews")
        sub = r.get_submission(url)

        # Check if feed already exists for another channel
        c.execute("SELECT feed_id FROM feed_reddit_comments WHERE article_id=? ", (sub.id,))
        result = c.fetchone()

        if result == None:

            c.execute("INSERT INTO feeds (type_name) VALUES (?)", ("reddit_comments",))
            feed_id = c.lastrowid

            c.execute("INSERT INTO feed_reddit_comments (feed_id, article_id) VALUES (?,?)", (feed_id, sub.id))

            items = [e for e in praw.helpers.flatten_tree(sub.comments)]

            for item in items:
                c.execute("INSERT INTO items (feed_id, unique_id) VALUES (?,?)", (feed_id, item.id))

        else:
            feed_id = result[0]

        c.execute("INSERT INTO channel_feeds (feed_id, channel_id, name) VALUES (?,?,?)", (feed_id, channel_id, name))

        conn.commit()
        conn.close()

        return p.say("Added " + name)


    except Exception as exc:
        conn.close()
        return p.say("Connection Error: " + str(exc))


def aamnews_add_feed_reddit_search(p, i, channel, name, subreddit, query):
    hostname = i.host

    conn = sqlite3.connect("aamnews.db")
    c = conn.cursor()

    # Check if channel exists
    c.execute("SELECT id FROM channels WHERE name=?", (channel,))
    result = c.fetchone()

    if result == None:
        return p.say("Channel does not exist.")

    channel_id = result[0]

    # determine if person owns channel
    if not aamnews_owns_channel(p, channel_id, hostname):
        return p.say("You must be a channel owner.")

    # check if name is already in use for another feed in this channel
    c.execute("SELECT feed_id FROM channel_feeds WHERE channel_id=? AND name=?", (channel_id, name))
    if c.fetchone() != None:
        return p.say("Name is already in use for another feed in this channel.")

    try:
        # Check if feed already exists for another channel
        c.execute("SELECT feed_id FROM feed_reddit_search WHERE subreddit_name=? AND query=?", (subreddit, query))
        result = c.fetchone()

        if result == None:

            c.execute("INSERT INTO feeds (type_name) VALUES (?)", ("reddit_search",))
            feed_id = c.lastrowid

            c.execute("INSERT INTO feed_reddit_search (feed_id, subreddit_name, query) VALUES (?,?,?)", (feed_id, subreddit, query))

            r = praw.Reddit("aamnews by /u/andreim at github.com/andreimarcu/aamnews")
            items = [e for e in r.search(query=query, subreddit=subreddit)]

            for item in items:
                c.execute("INSERT INTO items (feed_id, unique_id) VALUES (?,?)", (feed_id, item.id))


        else:
            feed_id = result[0]

        c.execute("INSERT INTO channel_feeds (feed_id, channel_id, name) VALUES (?,?,?)", (feed_id, channel_id, name))

        conn.commit()
        conn.close()

        return p.say("Added " + name)


    except Exception as exc:
        conn.close()
        return p.say("Connection Error: " + str(exc))


def aamnews_add_feed_twitter_user(p, i, channel, name, user, replies):
    hostname = i.host

    conn = sqlite3.connect("aamnews.db")
    c = conn.cursor()

    # Check if channel exists
    c.execute("SELECT id FROM channels WHERE name=?", (channel,))
    result = c.fetchone()

    if result == None:
        return p.say("Channel does not exist.")

    channel_id = result[0]

    # determine if person owns channel
    if not aamnews_owns_channel(p, channel_id, hostname):
        return p.say("You must be a channel owner.")

    # check if name is already in use for another feed in this channel
    c.execute("SELECT feed_id FROM channel_feeds WHERE channel_id=? AND name=?", (channel_id, name))
    if c.fetchone() != None:
        return p.say("Name is already in use for another feed in this channel.")

    try:
        # Check if feed already exists for another channel
        c.execute("SELECT feed_id FROM feed_twitter_user WHERE username=? AND replies=?", (user, replies))
        result = c.fetchone()

        if result == None:

            c.execute("INSERT INTO feeds (type_name) VALUES (?)", ("twitter_user",))
            feed_id = c.lastrowid

            c.execute("INSERT INTO feed_twitter_user (feed_id, username, replies) VALUES (?,?,?)", (feed_id, user, replies))

            auth = tweepy.OAuthHandler(p.config.twitter_creds["consumer_key"], p.config.twitter_creds["consumer_secret"])
            auth.set_access_token(p.config.twitter_creds["access_token"], p.config.twitter_creds["access_token_secret"])
            t = tweepy.API(auth)

            if replies:
                items = [e for e in t.user_timeline(user, count=100)]
            else:
                items = [e for e in t.user_timeline(user, count=100) if e.in_reply_to_user_id == None]

            for item in items:
                c.execute("INSERT INTO items (feed_id, unique_id) VALUES (?,?)", (feed_id, item.id))

        else:
            feed_id = result[0]

        c.execute("INSERT INTO channel_feeds (feed_id, channel_id, name) VALUES (?,?,?)", (feed_id, channel_id, name))

        conn.commit()
        conn.close()

        return p.say("Added " + name)


    except Exception as exc:
        conn.close()
        return p.say("Connection Error: " + str(exc))


def aamnews_add_feed_twitter_search(p, i, channel, name, query):
    hostname = i.host

    conn = sqlite3.connect("aamnews.db")
    c = conn.cursor()

    # Check if channel exists
    c.execute("SELECT id FROM channels WHERE name=?", (channel,))
    result = c.fetchone()

    if result == None:
        return p.say("Channel does not exist.")

    channel_id = result[0]

    # determine if person owns channel
    if not aamnews_owns_channel(p, channel_id, hostname):
        return p.say("You must be a channel owner.")

    # check if name is already in use for another feed in this channel
    c.execute("SELECT feed_id FROM channel_feeds WHERE channel_id=? AND name=?", (channel_id, name))
    if c.fetchone() != None:
        return p.say("Name is already in use for another feed in this channel.")

    try:
        # Check if feed already exists for another channel
        c.execute("SELECT feed_id FROM feed_twitter_search WHERE query=?", (query,))
        result = c.fetchone()

        if result == None:

            c.execute("INSERT INTO feeds (type_name) VALUES (?)", ("twitter_search",))
            feed_id = c.lastrowid

            c.execute("INSERT INTO feed_twitter_search (feed_id, query) VALUES (?,?)", (feed_id, query))

            auth = tweepy.OAuthHandler(p.config.twitter_creds["consumer_key"], p.config.twitter_creds["consumer_secret"])
            auth.set_access_token(p.config.twitter_creds["access_token"], p.config.twitter_creds["access_token_secret"])
            t = tweepy.API(auth)

            items = [e for e in t.search(query, rpp=100)]

            for item in items:
                c.execute("INSERT INTO items (feed_id, unique_id) VALUES (?,?)", (feed_id, item.id))

        else:
            feed_id = result[0]

        c.execute("INSERT INTO channel_feeds (feed_id, channel_id, name) VALUES (?,?,?)", (feed_id, channel_id, name))

        conn.commit()
        conn.close()

        return p.say("Added " + name)


    except Exception as exc:
        conn.close()
        return p.say("Connection Error: " + str(exc))


def aamnews_add_feed_rss_to_channel(p, i, channel, name, url):
    hostname = i.host

    conn = sqlite3.connect("aamnews.db")
    c = conn.cursor()

    # Check if channel exists
    c.execute("SELECT id FROM channels WHERE name=?", (channel,))
    result = c.fetchone()

    if result == None:
        return p.say("Channel does not exist.")

    channel_id = result[0]

    # determine if person owns channel
    if not aamnews_owns_channel(p, channel_id, hostname):
        return p.say("You must be a channel owner.")

    # check if name is already in use for another feed in this channel
    c.execute("SELECT feed_id FROM channel_feeds WHERE channel_id=? AND name=?", (channel_id, name))
    if c.fetchone() != None:
        return p.say("Name is already in use for another feed in this channel.")

    try:
        r = requests.get(url, headers={"User-Agent": p.config.user_agent}, timeout=10, verify=p.config.ssl_verify)

        if r.ok:
            f = feedparser.parse(r.text)

            # Check if feed already exists for another channel
            c.execute("SELECT feed_id FROM feed_rss WHERE url=?", (url,))
            result = c.fetchone()

            if result == None:
                c.execute("INSERT INTO feeds (type_name) VALUES (?)", ("rss",))
                feed_id = c.lastrowid

                c.execute("INSERT INTO feed_rss (feed_id, url) VALUES (?,?)", (feed_id, url))

                for entry in f.entries:
                    c.execute("INSERT INTO items (feed_id, unique_id) VALUES (?,?)", (feed_id, entry.link))

            else:
                feed_id = result[0]

            c.execute("INSERT INTO channel_feeds (feed_id, channel_id, name) VALUES (?,?,?)", (feed_id, channel_id, name))

            conn.commit()
            conn.close()

            return p.say("Added " + name)

        else:
            conn.close()
            return p.say("Could not make the request: Status " + r.status)

    except Exception as exc:
        conn.close()
        return p.say("Connection Error: " + str(exc))


def aamnews_loop(p):
    global running

    if running:
        return p.say("Already running.")
    else:
        running = True
        first_run = True
        unsuccessful = set()

        p.say("Starting...")

        while True:

            if not running:
                return p.say("Stopped.")

            run_start = time()

            conn = sqlite3.connect("aamnews.db")
            c = conn.cursor()

            c.execute("SELECT feeds.id, feeds.type_name, channel_feeds.name FROM feeds INNER JOIN channel_feeds ON feeds.id=channel_feeds.feed_id")
            feeds = c.fetchall()

            for feed_id, type_name, feed_name in feeds:
                if not running:
                    return p.say("Stopped.")


                # Check that I haven't been deleted in the meantime
                c.execute("SELECT id FROM feeds WHERE id=?", (feed_id,))
                if c.fetchone() == None:
                    continue

                # Get channels for this feed
                c.execute("SELECT channels.name, channels.max_blast, channel_feeds.name FROM channels INNER JOIN channel_feeds ON channels.id=channel_feeds.channel_id WHERE channel_feeds.feed_id=?", (feed_id,))
                channels = c.fetchall()

                to_blast = []

                if type_name == "rss":
                    # Get rss url
                    c.execute("SELECT url FROM feed_rss WHERE feed_id=?", (feed_id,))
                    url = c.fetchone()[0]

                    try:
                        r = requests.get(url, headers={"User-Agent": p.config.user_agent}, timeout=10, verify=p.config.ssl_verify)

                        if r.ok:
                            f = feedparser.parse(r.text)

                            # Get items we already have
                            c.execute("SELECT unique_id FROM items WHERE feed_id=?", (feed_id,))
                            items = [e[0] for e in c.fetchall()]

                            for entry in f.entries:
                                if not entry.link in items:
                                    c.execute("INSERT INTO items (feed_id, unique_id) VALUES (?,?)", (feed_id, entry.link))

                                    if not feed_id in unsuccessful and not first_run:
                                        blast_url = shorten_url(entry.link)
                                        to_blast.append("{} [ {} ]".format(unescape(entry.title[:250]), blast_url))

                            conn.commit()

                            if feed_id in unsuccessful:
                                unsuccessful.remove(feed_id)

                        else:
                            raise Exception("Status code" + r.status )

                    except Exception as exc:
                        print("Connection Error: " + str(exc) + " for " + url)
                        unsuccessful.add(feed_id)


                elif type_name == "reddit_subreddit":
                    c.execute("SELECT name, sort FROM feed_reddit_subreddit WHERE feed_id=?", (feed_id,))
                    subreddit, sort = c.fetchone()

                    try:

                        r = praw.Reddit("aamnews by /u/andreim at github.com/andreimarcu/aamnews")
                        sub = r.get_subreddit(subreddit)

                        if sort == "hot":
                            entries = [e for e in sub.get_hot(limit=100)]
                        elif sort == "top":
                            entries = [e for e in sub.get_top(limit=100)]
                        elif sort == "new":
                            entries = [e for e in sub.get_new(limit=100)]

                        # Get items we already have
                        c.execute("SELECT unique_id FROM items WHERE feed_id=?", (feed_id,))
                        items = [e[0] for e in c.fetchall()]

                        for entry in entries:
                            if not entry.id in items:
                                c.execute("INSERT INTO items (feed_id, unique_id) VALUES (?,?)", (feed_id, entry.id))

                                if not feed_id in unsuccessful and not first_run:
                                    blast_url = shorten_url(entry.url)

                                    if entry.is_self:
                                        to_blast.append("{} [ {} ]".format(entry.title[:250], blast_url))
                                    else:
                                        to_blast.append("{} [ {} ] [ {} ]".format(entry.title[:250], blast_url, entry.short_link))

                        conn.commit()

                        if feed_id in unsuccessful:
                            unsuccessful.remove(feed_id)

                    except Exception as exc:
                        print("Reddit error: {} for {}".format(str(exc), feed_name))
                        unsuccessful.add(feed_id)


                elif type_name == "reddit_comments":
                    c.execute("SELECT article_id FROM feed_reddit_comments WHERE feed_id=?", (feed_id,))
                    article_id = c.fetchone()[0]

                    try:
                        r = praw.Reddit("aamnews by /u/andreim at github.com/andreimarcu/aamnews")
                        sub = r.get_submission(submission_id=article_id)

                        entries = [e for e in praw.helpers.flatten_tree(sub.comments)]

                        # Get items we already have
                        c.execute("SELECT unique_id FROM items WHERE feed_id=?", (feed_id,))
                        items = [e[0] for e in c.fetchall()]

                        for entry in entries:
                            if not entry.id in items:
                                c.execute("INSERT INTO items (feed_id, unique_id) VALUES (?,?)", (feed_id, entry.id))

                                if not feed_id in unsuccessful and not first_run:
                                    blast_url = shorten_url(entry.permalink)
                                    to_blast.append("{} [ {} ]".format(entry.body[:250], blast_url))

                        conn.commit()

                        if feed_id in unsuccessful:
                            unsuccessful.remove(feed_id)

                    except Exception as exc:
                        print("Reddit error: {} for {}".format(str(exc), feed_name))
                        unsuccessful.add(feed_id)


                elif type_name == "reddit_search":
                    c.execute("SELECT subreddit_name, query FROM feed_reddit_search WHERE feed_id=?", (feed_id,))
                    subreddit, query = c.fetchone()

                    try:

                        r = praw.Reddit("aamnews by /u/andreim at github.com/andreimarcu/aamnews")
                        entries = [e for e in r.search(query=query, subreddit=subreddit)]

                        # Get items we already have
                        c.execute("SELECT unique_id FROM items WHERE feed_id=?", (feed_id,))
                        items = [e[0] for e in c.fetchall()]

                        for entry in entries:
                            if not entry.id in items:
                                c.execute("INSERT INTO items (feed_id, unique_id) VALUES (?,?)", (feed_id, entry.id))

                                if not feed_id in unsuccessful and not first_run:
                                    blast_url = shorten_url(entry.url)

                                    if entry.is_self:
                                        to_blast.append("{} [ {} ]".format(entry.title[:250], blast_url))
                                    else:
                                        to_blast.append("{} [ {} ] [ {} ]".format(entry.title[:250], blast_url, entry.short_link))

                        conn.commit()

                        if feed_id in unsuccessful:
                            unsuccessful.remove(feed_id)

                    except Exception as exc:
                        print("Reddit error: {} for {}".format(str(exc), feed_name))
                        unsuccessful.add(feed_id)


                elif type_name == "twitter_user":
                    c.execute("SELECT username, replies FROM feed_twitter_user WHERE feed_id=?", (feed_id,))
                    user, replies = c.fetchone()

                    try:

                        auth = tweepy.OAuthHandler(p.config.twitter_creds["consumer_key"], p.config.twitter_creds["consumer_secret"])
                        auth.set_access_token(p.config.twitter_creds["access_token"], p.config.twitter_creds["access_token_secret"])
                        t = tweepy.API(auth)

                        if replies:
                            entries = [e for e in t.user_timeline(user, count=100)]
                        else:
                            entries = [e for e in t.user_timeline(user, count=100) if e.in_reply_to_user_id == None]

                        # Get items we already have
                        c.execute("SELECT unique_id FROM items WHERE feed_id=?", (feed_id,))
                        items = [e[0] for e in c.fetchall()]

                        for entry in entries:
                            if not entry.id in items:
                                c.execute("INSERT INTO items (feed_id, unique_id) VALUES (?,?)", (feed_id, entry.id))

                                if not feed_id in unsuccessful and not first_run:
                                    blast_url = shorten_url("https://twitter.com/{}/status/{}".format(entry.author.screen_name, entry.id_str))

                                    to_blast.append("{} [ {} ]".format(unescape(entry.text[:250]), blast_url))

                        conn.commit()

                        if feed_id in unsuccessful:
                            unsuccessful.remove(feed_id)

                    except Exception as exc:
                        print("Twitter error: {} for {}".format(str(exc), feed_name))
                        unsuccessful.add(feed_id)


                elif type_name == "twitter_search":
                    c.execute("SELECT query FROM feed_twitter_search WHERE feed_id=?", (feed_id,))
                    query = c.fetchone()[0]

                    try:

                        auth = tweepy.OAuthHandler(p.config.twitter_creds["consumer_key"], p.config.twitter_creds["consumer_secret"])
                        auth.set_access_token(p.config.twitter_creds["access_token"], p.config.twitter_creds["access_token_secret"])
                        t = tweepy.API(auth)

                        entries = [e for e in t.search(query, rpp=100)]

                        # Get items we already have
                        c.execute("SELECT unique_id FROM items WHERE feed_id=?", (feed_id,))
                        items = [e[0] for e in c.fetchall()]

                        for entry in entries:
                            if not entry.id in items:
                                c.execute("INSERT INTO items (feed_id, unique_id) VALUES (?,?)", (feed_id, entry.id))

                                if not feed_id in unsuccessful and not first_run:
                                    blast_url = shorten_url("https://twitter.com/{}/status/{}".format(entry.author.screen_name, entry.id_str))

                                    to_blast.append("{} [ {} ]".format(unescape(entry.text[:250]), blast_url))

                        conn.commit()

                        if feed_id in unsuccessful:
                            unsuccessful.remove(feed_id)

                    except Exception as exc:
                        print("Twitter error: {} for {}".format(str(exc), feed_name))
                        unsuccessful.add(feed_id)


                for channel, max_blast, channel_feed_name in channels:
                    max_blast = int(max_blast)

                    for i, blast in enumerate(to_blast):

                        msg = "\x02{}\x02: {}".format(channel_feed_name, blast)

                        if i < max_blast:

                            reached_limit = (max_blast and
                                             i == (max_blast - 1) and
                                             max_blast < len(to_blast))
                            if reached_limit:
                                remaining = str(len(to_blast) - max_blast)
                                p.msg(channel, "{} [ +{} more ]".format(msg, str(remaining)))
                                break

                        p.msg(channel, msg)

                if len(to_blast) > 0:
                    print(feed_name + " blasted " + str(len(to_blast))
                          + " for " + str(len(channels)) + " channels")

                
                sleep(p.config.sleep_interval)

            if first_run:
                print("\n--> Did first run in " + str(round(time() - run_start,
                      2)) + "s at " + ctime() + "\n")
            else:
                print("\n--> Did run in " + str(round(time() - run_start,
                      2)) + "s at " + ctime() + "\n")

            first_run = False
