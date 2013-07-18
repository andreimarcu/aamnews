import requests


def shorten_url(url):
    """
    To be modified to be used with your service of choice

    Keep in mind that this will do a lot of queries at a time.

    """

    payload = {"format": "simple",
               "action": "shorturl",
               "url": url}

    return requests.get("http://off.st/api.php", params=payload).text
