import urllib2
import json
import urllib
from hashlib import md5

#https://community.vtiger.com/help/vtigercrm/developers/third-party-app-integration.html#query-operation

#https://wiki.vtiger.com/index.php/Webservices_tutorials

### define the account specific information
# find the Access Key under preferences > User Advanced Options
accessKey = ''

vtigerserver = ''

url = '%s/webservice.php' % vtigerserver

username = ''


### let's set up the session
# get the token using 'getchallenge' operation
values = {'operation':'getchallenge', 'username': username}
data = urllib.urlencode(values)
req = urllib2.Request('%s?%s' % (url,data))
response = urllib2.urlopen(req).read()
token = json.loads(response)['result']['token']

# use the token to + accesskey to create the tokenized accessKey
key = md5(token + accessKey)
tokenizedAccessKey = key.hexdigest()
values['accessKey'] = tokenizedAccessKey

# now that we have an accessKey tokenized, let's perform a login operation 
values['operation']  = 'login'
data = urllib.urlencode(values)
req = urllib2.Request(url, data)
response = urllib2.urlopen(req)
response = json.loads(response.read())

# set the sessionName
values['sessionName'] = response['result']['sessionName']

### now let's do stuff
# listtypes
values['operation'] = 'listtypes'
data = urllib.urlencode(values)
# added data a parameter here makes this a POST
req = urllib2.Request(url,data)
response = urllib2.urlopen(req)
print 'here are the available types'
print json.loads(response.read())


# find out about a particular vTiger Object Type
# we'll look at 'Potentials'
values.pop('username', False)
values.pop('accessKey', False)
print "\n\nPotentials", values
values['operation'] = 'describe'
values['elementType'] = 'Contacts'
#values['id'] = u'5'
data = urllib.urlencode(values)
# must be a get according to docs
# so we append data to url
req = urllib2.Request("%s?%s" % (url,data))
response = urllib2.urlopen(req)
print 'about desc contacts'
print values
print json.loads(response.read())['result']


# Query
# find out about a particular vTiger Object Type
# we'll look at 'Contacts'
values['operation'] = 'query'
values['query'] = 'select * from Contacts;'
data = urllib.urlencode(values)
# must be a get according to docs
# so we append data to url
req = urllib2.Request("%s?%s" % (url,data))
response = urllib2.urlopen(req)
print 'about Contacts'
print json.loads(response.read())


# find out about a particular vTiger Object Type
# we'll look at 'Contacts'
#values['operation'] = 'retrieve'
#values['id'] = '4x56'
##values['elementType'] = 'Contacts'
#data = urllib.urlencode(values)
##data += '&query=select * from Contacts'
## must be a get according to docs
## so we append data to url
#req = urllib2.Request("%s?%s" % (url,data))
#response = urllib2.urlopen(req)
#print 'about contacts'
#print json.loads(response.read())
