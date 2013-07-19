# -*- coding: utf-8 -*-

"""
aamnews.py - Feed Parsing Module
Copyright 2013, Andrei Marcu, andreim.net

https://github.com/andreimarcu/aamnews
"""
from time import time, ctime, sleep
import localfeedparser as feedparser
from modules.short import shorten_url
import requests
import sqlite3
import re


running = False


def init(p):
    """Performed on startup"""
    conn = sqlite3.connect("aamnews.db")
    c = conn.cursor()

    # Init db
    c.execute("CREATE TABLE IF NOT EXISTS feeds (name, url, channels)")
    c.execute("CREATE TABLE IF NOT EXISTS items (feed_name, title, link)")
    c.execute("CREATE TABLE IF NOT EXISTS channels"
              + " (name, owner_host, max_blast)")
    conn.commit()

    c.execute("SELECT * from channels")
    channels = [a[0] for a in c.fetchall()]
    channels = set(channels)
    if len(channels) > 0:
        for channel in channels:
            p.write(['JOIN'], channel)

    conn.close()


def aamnews_loop(p):
    global running

    if running:
        return p.msg(p.config.control_channel, "Already running.")
    else:
        running = True
        p.msg(p.config.control_channel, "Starting..")

        conn = sqlite3.connect("aamnews.db")
        c = conn.cursor()

        # Delete existing items
        c.execute("DELETE FROM items")
        conn.commit()

        first_run = True
        timeouted = set()

        while True:
            if not running:
                return p.msg(p.config.control_channel, "Stopped.")

            c.execute("SELECT * FROM feeds")
            feeds = c.fetchall()

            run_start = time()

            for feed in feeds:
                if not running:
                    return p.msg(p.config.control_channel, "Stopped.")

                feed_name, feed_url, feed_channels = feed
                channels = feed_channels.split(",")

                try:
                    r = requests.get(feed_url, timeout=25)
                except Exception as e:
                    r = type('obj', (object,), {'text': ''})
                    p.msg(p.config.control_channel, feed_name
                          + " made a requests timeout: " + str(e))
                    timeouted.add(feed_name)
                    print(feed_name + " made a requests timeout: " + str(e))
                    continue

                try:
                    c.execute("SELECT link FROM items WHERE feed_name=?",
                             (feed_name,))
                    entries = [e[0] for e in c.fetchall()]

                    to_blast = []

                    d = feedparser.parse(r.text)

                    for entry in d.entries:
                        try:
                            entry.id
                        except:
                            entry.id = entry.link

                        if not running:
                            return p.msg(p.config.control_channel,
                                         "Stopped.")

                        if entry.id not in entries:
                            try:
                                c.execute("INSERT INTO items (feed_name,"
                                          + " title,link) VALUES (?, ?, ?)",
                                          (feed_name, entry.title, entry.id))
                                conn.commit()

                                if p.config.shorten_urls:
                                    blast_url = shorten_url(entry.link)
                                else:
                                    blast_url = entry.link

                                if not feed_name in timeouted and not first_run:
                                    to_blast.append("\x02" + feed_name
                                                    + "\x02: " + entry.title
                                                    + " [ " + blast_url + " ]")

                            except Exception as e:
                                try:
                                    p.msg(p.config.control_channel, "ENTRY: "
                                          + feed_name + " for entry "
                                          + entry.title + " " + str(e))
                                    print("ENTRY: " + feed_name + " for entry "
                                          + entry.title + " " + str(e))
                                except Exception as e:
                                    p.msg(p.config.control_channel, "ENTRY: "
                                          + feed_name + " FAILED entry.title"
                                          + " with url: " + entry.id
                                          + " " + str(e))
                                    print("ENTRY: " + feed_name + " FAILED "
                                          + "entry.title with url: " + entry.id
                                          + " " + str(e))

                    for channel in channels:
                        c.execute("SELECT * FROM channels WHERE name=?",
                                  (channel,))

                        max_blast = c.fetchone()[2]
                        if max_blast:
                            max_blast = int(max_blast)
                            if max_blast == 0:
                                max_blast = None

                        for i, blast in enumerate(to_blast):
                            if max_blast and i < max_blast or not max_blast:

                                reached_limit = (max_blast and
                                                 i == (max_blast - 1) and
                                                 max_blast < len(to_blast))
                                if reached_limit:
                                    remaining = str(len(to_blast) - max_blast)
                                    p.msg(channel, blast + " [ +" + remaining
                                          + " more ]")
                                else:
                                    p.msg(channel, blast)

                    if len(d.entries) > 0 and feed_name in timeouted:
                        timeouted.remove(feed_name)
                        print(feed_name + " removed from timeouted.")

                    if len(to_blast) > 0:
                        print(feed_name + " blasted " + str(len(to_blast))
                              + " for " + str(len(channels)) + " channels")

                    sleep(p.config.sleep_interval)

                except Exception as e:
                    p.msg(p.config.control_channel, "FEED: " + feed_name
                          + ": " + str(e))
                    print("FEED: " + feed_name + ": " + str(e))

            if first_run:
                print("\n--> Did first run in " + str(round(time() - run_start,
                      2)) + "s at " + ctime() + "\n")
            else:
                print("\n--> Did run in " + str(round(time() - run_start,
                      2)) + "s at " + ctime() + "\n")

            first_run = False


def start_aamnews(p, i):
    global running

    if i.host == p.config.owner_host and i.sender == p.config.control_channel:
        if running:
            return p.say("Already running.")
        else:
            return aamnews_loop(p)

start_aamnews.commands = ['start']
start_aamnews.threading = True
start_aamnews.priority = "medium"


def stop_aamnews(p, i):
    global running

    if i.host == p.config.owner_host and i.sender == p.config.control_channel:
        if running:
            running = False
            return p.msg(p.config.control_channel, "Ordered to stop.")
        else:
            return p.msg(p.config.control_channel, "Already stopped.")

stop_aamnews.commands = ['stop']
stop_aamnews.threading = True
stop_aamnews.priority = "medium"


def join_channels(p, i):

    if i.sender == p.config.control_channel and i.host == p.config.owner_host:
        conn = sqlite3.connect("aamnews.db")
        c = conn.cursor()
        c.execute("SELECT * from channels")
        channels = [a[0] for a in c.fetchall()]
        channels = set(channels)

        if len(channels) > 0:
            for channel in channels:
                p.write(['JOIN'], channel)
            conn.close()
            return p.msg(p.config.control_channel,
                         "Joined " + ", ".join(channels))
        else:
            return p.msg(p.config.control_channel, "No channels to join")

join_channels.commands = ['join_channels']
join_channels.threading = True
join_channels.priority = "medium"


def add_feed(p, i):
    try:
        m = re.match(r'.add_feed "(.*)" "(.*)"', i.group(0))
        feed_name = m.group(1)
        feed_url = m.group(2)
        feed_channel = i.sender
    except:
        return p.say('.add_feed "Feed Name" "http://feed.tld/rss"')

    conn = sqlite3.connect("aamnews.db")
    c = conn.cursor()
    # determine if person owns channel
    c.execute("SELECT * FROM channels WHERE name=?", (feed_channel,))
    result = c.fetchone()
    if result:
        if i.host == result[1] or i.host == p.config.owner_host:
            # person is owner
            c.execute("SELECT * FROM feeds WHERE url=?", (feed_url,))
            potential_feed = c.fetchone()
            if potential_feed:
                # feed is in db, check if current channel is set
                feed_name, feed_url, feed_channels = potential_feed
                channels = feed_channels.split(",")
                if feed_channel in channels:
                    # feed already for channel
                    conn.close()
                    p.msg(p.config.control_channel, i.nick
                          + " tried adding: " + feed_name + " in "
                          + feed_channel + " but it was already there.")
                    return p.say(feed_name + " is already there.")
                else:
                    # feed there but not associated with channel
                    try:
                        channels.append(feed_channel)
                        channels = ",".join(channels)
                        c.execute("UPDATE feeds SET channels=? WHERE url=?",
                                 (channels, feed_url))
                        conn.commit()
                        conn.close()

                        if i.host != p.config.owner_host:
                            p.msg(p.config.control_channel, i.nick
                                  + " added existing" + feed_name
                                  + " in " + feed_channel)
                            print(i.nick + " added existing" + feed_name
                                  + " in " + feed_channel)

                        return p.say(feed_name + " added.")

                    except Exception as e:
                        print("NEWFEED: " + feed_name + ": " + str(e))
                        p.msg(p.config.control_channel, i.nick
                              + " failed to add " + feed_name + " in "
                              + feed_channel + ": " + str(e))
                        p.say("Failed to add " + feed_name + ": " + str(e))

            else:
                # feed is not in db
                try:

                    r = requests.get(feed_url, timeout=25)
                    d = feedparser.parse(r.text)

                    if len(d.entries) == 0:
                        conn.close()
                        return p.say("Bad feed URL.")

                    for entry in d.entries:
                        try:
                            c.execute("INSERT INTO items (feed_name, title,"
                                      + " link) VALUES (?, ?, ?)",
                                      (feed_name, entry.title, entry.id))
                            conn.commit()
                        except Exception as e:
                            try:
                                print("ENTRYLVL1: " + feed_name + " for entry "
                                      + entry.title + " " + str(e))
                            except Exception as e:
                                print("ENTRYLVL1: " + feed_name
                                      + " FAILED entry.title with url: "
                                      + entry.id + " " + str(e))

                    print("Done adding from new feed " + feed_name)

                    c.execute("INSERT INTO feeds (name, url, channels) VALUES "
                              + "(?, ?, ?)", (feed_name, feed_url,
                                              feed_channel))
                    conn.commit()
                    conn.close()

                    if i.host != p.config.owner_host:
                        p.msg(p.config.control_channel, i.nick
                              + " added new" + feed_name + " in "
                              + feed_channel)
                        print(i.nick + " added new" + feed_name
                              + " in " + feed_channel)

                    return p.say(feed_name + " added.")

                except Exception as e:
                    print("NEWFEED: " + feed_name + ": " + str(e))
                    p.msg(p.config.control_channel, i.nick
                          + " failed to add new " + feed_name + " in "
                          + feed_channel + ": " + str(e))
                    p.say("Failed to add new " + feed_name + ": " + str(e))
    else:
        conn.close()
        # return p.say("You are not listed as owner of this channel.")
add_feed.commands = ["add_feed"]
add_feed.priority = "medium"
add_feed.threading = True


def delete_feed(p, i):
    try:
        m = re.match(r'.del_feed "(.*)"', i.group(0))
        feed_name = m.group(1)
        feed_channel = i.sender
    except:
        return p.say('.del_feed "Feed Name"')

    conn = sqlite3.connect("aamnews.db")
    c = conn.cursor()
    c.execute("SELECT * FROM channels WHERE name=?", (feed_channel,))

    result = c.fetchone()

    if result:
        if i.host == result[1] or i.host == p.config.owner_host:
            # person is channel or global owner
            c.execute("SELECT * FROM feeds WHERE name=?", (feed_name,))
            potential_feed = c.fetchone()
            if potential_feed:
                # feed is in db, check if current channel is set
                feed_name, feed_url, feed_channels = potential_feed
                channels = feed_channels.split(",")
                if feed_channel in channels:
                    #DELETE HERE
                    channels.remove(feed_channel)

                    if len(channels) == 0:
                        c.execute("DELETE FROM feeds WHERE url=?", (feed_url,))
                    else:
                        channels = ",".join(channels)
                        c.execute("UPDATE feeds SET channels=? WHERE url=?",
                                  (channels, feed_url))

                    conn.commit()
                    conn.close()
                    p.msg(p.config.control_channel, i.nick + " deleted "
                          + feed_name + " in " + feed_channel)
                    return p.say(feed_name + " has been deleted.")
                else:
                    conn.close()
                    return p.say(feed_name + " is not there.")
                    p.msg(p.config.control_channel, i.nick
                          + " tried to delete nonassociated " + feed_name
                          + " in " + feed_channel)
            else:
                # feed is not in db
                conn.close()
                p.msg(p.config.control_channel, i.nick
                      + " tried to delete nonexisting " + feed_name
                      + " in " + feed_channel)
                return p.say(feed_name + " is not there.")
        else:
            conn.close()
            # return phenny.say("You are not listed as owner of this channel.")
delete_feed.commands = ["del_feed"]
delete_feed.priority = "medium"
delete_feed.threading = True


def list_feeds(p, i):
    channel = i.sender
    conn = sqlite3.connect("aamnews.db")
    c = conn.cursor()
    c.execute("SELECT * FROM feeds")
    results = c.fetchall()
    conn.close()

    feeds = []

    for result in results:
        name, url, channels = result
        channels = channels.split(",")
        if channel in channels:
            feeds.append(name)

    if len(feeds) == 0:
        p.msg(p.config.control_channel, i.nick
              + " listed (empty) feeds for " + channel)
        return p.say("No feeds for " + channel)
    else:
        p.msg(p.config.control_channel, i.nick
              + " listed feeds for " + channel)
        return p.say("Feeds: " + ", ".join(feeds))

list_feeds.commands = ["list_feeds"]
list_feeds.priority = "medium"
list_feeds.threading = True


def add_channel(p, i):
    if i.host == p.config.owner_host and i.sender == p.config.control_channel:
        try:
            m = re.match(r'.add_channel "(.*)" "(.*)" "(.*)"', i.group(0))
            channel_name = m.group(1)
            channel_owner = m.group(2)
            channel_limit = int(m.group(3))
        except:
            return p.say('.add_channel "#channel" "owner.hostname"'
                         + ' "limit_blast_per_feed_in_seconds"')

        conn = sqlite3.connect("aamnews.db")
        c = conn.cursor()
        c.execute("SELECT * FROM channels WHERE name=?", (channel_name,))

        result = c.fetchone()

        if result:
            conn.close()
            return p.say(channel_name + " already exists.")
        else:
            c.execute("INSERT INTO channels (name, owner_host, max_blast)"
                      + " VALUES (?, ?, ?)",
                      (channel_name, channel_owner, channel_limit))
            conn.commit()
            conn.close()
            p.write(['JOIN'], channel_name)
            return p.say("Added " + channel_name)

add_channel.commands = ["add_channel"]
add_channel.priority = "medium"
add_channel.threading = True


def delete_channel(p, i):
    if i.host == p.config.owner_host and i.sender == p.config.control_channel:
        try:
            m = re.match(r'.del_channel "(.*)"', i.group(0))
            channel_name = m.group(1)
        except:
            return p.say('.del_channel "#channel"')

        conn = sqlite3.connect("aamnews.db")
        c = conn.cursor()
        c.execute("SELECT * FROM channels WHERE name=?", (channel_name,))

        result = c.fetchone()
        if not result:
            conn.close()
            return p.say("No such channel")
        else:

            c.execute("SELECT * FROM feeds")
            feeds = c.fetchall()

            for feed in feeds:
                feed_name, feed_url, feed_channels = feed
                channels = feed_channels.split(",")

                if channel_name in channels:
                    channels.remove(channel_name)

                    if len(channels) == 0:
                        c.execute("DELETE FROM feeds WHERE url=?", (feed_url,))
                    else:
                        channels = ",".join(channels)
                        c.execute("UPDATE feeds SET channels=? WHERE url=?",
                                  (channels, feed_url))

                    conn.commit()

            c.execute("DELETE FROM channels WHERE name=?", (channel_name,))

            conn.commit()
            conn.close()

            p.write(['PART'], channel_name)

            return p.say("Deleted " + channel_name)

delete_channel.commands = ["del_channel"]
delete_channel.priority = "medium"
delete_channel.threading = True


def list_channels(p, i):

    if i.host == p.config.owner_host and i.sender == p.config.control_channel:

        conn = sqlite3.connect("aamnews.db")
        c = conn.cursor()
        c.execute("SELECT * FROM channels")
        results = c.fetchall()
        conn.close()

        channels = []
        for channel in results:
            name, owner_host, max_blast = channel
            channels.append("{} ({}, {})".format(name, owner_host, max_blast))

        if len(channels) == 0:
            return p.say("No channels")
        else:
            return p.say("Channels: " + ", ".join(channels))

list_channels.commands = ["list_channels"]
list_channels.priority = "medium"
list_channels.threading = True


def insert_feeds_from_array(feeds_to_insert):
    feeds_to_insert = []

    for feed in feeds_to_insert:
        feed_name, feed_url, feed_channels = feed

        conn = sqlite3.connect("aamnews.db")
        c = conn.cursor()
        c.execute("SELECT * FROM feeds WHERE name=?", (feed_name,))
        if c.fetchone():
            # print "Inserting " + feed[0]
            c.execute("INSERT INTO feeds (name, url, channels) "
                      + "VALUES (?, ?, ?)",
                      (feed_name, feed_url, feed_channels))
            conn.commit()
        #else:
            #print feed[0] + " already there."
