import requests


nick = 'botnickname'
host = 'irc.oftc.net'
port = 6697
ssl = True
ipv6 = False

### OPTIONAL: password is the NickServ password, serverpass, the server password
# password = 'nickserv_password'
# serverpass = 'server_password'

## Your nickname for use with admin.py functionality
admins = owner = 'my_owner'

# Your hostname to be recognized as global owner
owner_host = "my_owner_hostname"

# Time in seconds to wait between two feed requests
sleep_interval = 5

# Use with caution, certificate verification for https requests
ssl_verify = False

# User Agent (You are responsible for respectul usage)
user_agent = "aamnews"

### Ignore nicknames
ignore = ['']

# URL shortening
# Use any of the two and modify to use your shortner

def shorten_url(url):
	"""
	Use this to avoid shortening URLs
	"""
	return url

# Example: 
#
# def shorten_url(url):
#     """
#     To be modified to be used with your service of choice
#     Keep in mind that this will do a lot of queries at a time.
#     """
#
#     payload = {"format": "simple",
#                "action": "shorturl",
#                "url": url}
#
#     return requests.get("http://off.st/api.php", params=payload).text



