#!/usr/bin/python -u

'''
 _____         _ _   _                    
|_   _|       (_) | | |                   
  | |__      ___| |_| |_  ___  __ _  ___  
  | |\ \ /\ / / | __| __|/ _ \/ _` |/ _ \ 
  | | \ V  V /| | |_| |_|  __/ (_| | (_) |
  \_/  \_/\_/ |_|\__|\__|\___|\__, |\___/ 
                               __/ |      
                              |___/     

Twitter based intelligence

Martin Obiols
@olemoudi
''
'''

import sys
import re
import time
import json
import httplib
from datetime import datetime
import random
from urllib import FancyURLopener
from random import choice
import math

import logging
logging.basicConfig(format='%(asctime)s %(message)s', filename='twittego.log', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)
info = logging.info



MAX_RETRIES = 3
SLEEP_TIME = 3 # seconds between retries


user_agents = ['Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2. 0.0.11', 'Opera/9.25 (Windows NT 5.1; U; en)', 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1;  SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)', 'Mozilla/5.0 (compatible; Konqueror/3.5; Linux) KHTML/3.5.5 (like Gecko) (Kubuntu)', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.12) Gecko/20070731 Ubuntu/dapper-security Firefox/1.5.0.12', 'Lynx/2.8.5rel.1 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/1.2.  9' ]


class MyOpener(FancyURLopener, object):
    '''
    Just to spoof user agent
    '''
    version = choice(user_agents)



def getIDs(screen_name, call='followers', cursor=-1):
    '''
    '''
    ids = []

    decoded_data = callAPI('http://api.twitter.com/1/%s/ids.json?screen_name=%s&cursor=%i' % (call, screen_name, cursor))

    ids += decoded_data['ids']

    if decoded_data['next_cursor'] != 0:
        ids += getIDs(screen_name, call, int(decoded_data['next_cursor']))

    return ids


'''
Interesting fields:
    "created_at": "Wed May 23 06:01:13 +0000 2007",
    "location": "San Francisco, CA",
    "protected": false,
    "followers_count": 335343,
    "description": "The Real Twitter API. I tweet about API changes, service issues and happily answer questions about Twitter and our API. Don't get an answer? It's on my website.",
     "friends_count": 20,
     "statuses_count": 2404,
     "screen_name": "twitterapi",
'''
def getUsersData(user_ids, nicks=False):

    result = []

    if len(user_ids) > 100:
        for i in list(chunks(user_ids, 100)):
            result += getUsersData(i)
    else:
        ids = ",".join(['%s' % e for e in user_ids])
        if nicks:
            result = callAPI('http://api.twitter.com/1/users/lookup.json?screen_name=%s' % str(ids))
        else:

            result = callAPI('http://api.twitter.com/1/users/lookup.json?user_id=%s' % str(ids))

    return result

'''
call = all o memberships
"name": "team",
"id" para conseguir subscribers
para memberships {'lists' : []}
'''
def getLists(screen_name, call='all'):

    result = callAPI('http://api.twitter.com/1/lists/%s.json?screen_name=%s' % (call, str(screen_name)))

    return result

def getListMemberships(screen_name, cursor=-1):
    '''
    '''
    lists = []

    decoded_data = callAPI('http://api.twitter.com/1/lists/memberships.json?screen_name=%s&cursor=%i' % (screen_name, cursor))

    lists += decoded_data['lists']

    if decoded_data['next_cursor'] != 0:
        lists += getListMemberships(screen_name, int(decoded_data['next_cursor']))

    return lists

def getListMembers(list_id, cursor=-1):
    '''
    '''
    members = []

    decoded_data = callAPI('http://api.twitter.com/1/lists/members.json?screen_name=%s&cursor=%i' % (list_id, cursor))

    members += decoded_data['users']

    if decoded_data['next_cursor'] != 0:
        members += getListMembers(list_id, int(decoded_data['next_cursor']))

    return members

'''
{"users" : [] }
'''
def getListSubscribers(list_id):

    result = callAPI('http://api.twitter.com/1/lists/subscribers.json?list_id=%s' % (str(list_id)))

    return result


def callAPI(url, check=True):

    sys.stdout.flush()

    if check:
        getLimits()

    mo = MyOpener()

    for i in range(MAX_RETRIES):

        try:

            apidata = mo.open(url).read()
            result = json.loads(apidata)

            if isinstance(result, dict) and result.has_key('error'):
                print ""
                print "Error: " +result['error']        
                print "Context: callAPI(%s)" % (str(url))

                if i == 4:
                    print "Max number of retries reached..."
                    raise Exception
                else:
                    print "Retrying..."
            else:

                break

        except Exception as e:
            print ""
            print e
            print "Connection Error: maybe twitter is overcapacity? maybe one of the profiles is protected?"
            print "Context: callAPI(%s)" % (str(url))
            if i == 4:
                print "Max number of retries reached, exiting..."
                raise Exception
            else:
                print "Retrying..."

        time.sleep(SLEEP_TIME)

    return result


def scrapeUserData(user_id):
    pass

def intersect(a, b):
     return list(set(a) & set(b))

def substract(a, b):
    return list(set(a) - set(b))

def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]


def getLimits():

    result = callAPI('http://api.twitter.com/1/account/rate_limit_status.json', False)

    if result['remaining_hits'] == 0:
        print ""
        print "[*] API calls limit reached"
        print "[*] Waiting for limit to be reset at %s or sooner (hopefully)" % datetime.fromtimestamp(result['reset_time_in_seconds']).strftime("%H:%M")
        while waitForLimits():
            time.sleep(random.randint(1, 30))

    return result

def waitForLimits():

    result = callAPI('http://api.twitter.com/1/account/rate_limit_status.json', False)
    if result['remaining_hits'] == 0:
        return True
    else:
        return False



def confirm(prompt=None, resp=False):
    """prompts for yes or no response from the user. Returns True for yes and
    False for no.

    'resp' should be set to the default value assumed by the caller when
    user simply types ENTER.
    """
    
    if prompt is None:
        prompt = 'Confirm'

    if resp:
        prompt = '%s [%s/%s]: ' % (prompt, 'Y', 'n')
    else:
        prompt = '%s [%s/%s]: ' % (prompt, 'y', 'N')
        
    while True:
        ans = raw_input(prompt)
        if not ans:
            return resp
        if ans not in ['y', 'Y', 'n', 'N']:
            print 'please enter y or n.'
            continue
        if ans == 'y' or ans == 'Y':
            return True
        if ans == 'n' or ans == 'N':
            return False

def banner():
    
    print '''
\t _____         _ _   _                    
\t|_   _|       (_) | | |                   
\t  | |__      ___| |_| |_  ___  __ _  ___  
\t  | |\ \ /\ / / | __| __|/ _ \/ _` |/ _ \ 
\t  | | \ V  V /| | |_| |_|  __/ (_| | (_) |
\t  \_/  \_/\_/ |_|\__|\__|\___|\__, |\___/ 
\t                               __/ |      
\t                              |___/     

\t\t Twitter based intelligence

\t\t\t\t\t Martin Obiols
\t\t\t\t\t @olemoudi
'''

def usage():
    print ""
    print "Usage: %s <screen_name1> <screen_name2>" % sys.argv[0]
    print "Usage: %s check" % sys.argv[0]
    print

if __name__ == '__main__':

    banner()

    if len(sys.argv) < 3:
        if len(sys.argv) > 1 and sys.argv[1] == 'check':
            limits = getLimits()
            print ""
            print "[*] Current API calls left: %i" % limits['remaining_hits']
            print ""
        else:
            usage()

        sys.exit(1)


    limits = getLimits()
    print ""
    print "[*] Current API calls left: %i" % limits['remaining_hits']
    print ""



    user1 = sys.argv[1].strip().lower()
    user2 = sys.argv[2].strip().lower()

    store = {}

    while True:
        
        try:

            info("Starting analysis between %s and %s" % (user1, user2))

            if user1 in store.keys():
                print "[*] Using cached info for %s" % user1
                data_user1 = store[user1]
            else: 
                data_user1 = {'screen_name' : user1}

            if user2 in store.keys():
                print "[*] Using cached info for %s" % user2
                data_user2 = store[user2]
            else:
                data_user2 = {'screen_name' : user2}


            print "[*] Getting info for %s and %s ... " % (user1, user2),
            data = getUsersData([user1, user2], True)
            for d in data:
                if d['screen_name'].lower() == data_user1['screen_name'].lower():
                    data_user1['info'] = d
                if d['screen_name'].lower() == data_user2['screen_name'].lower():
                    data_user2['info'] = d
            print "[OK]"

            total = 0.0
            for user in data:
                if user['screen_name'].lower() in store.keys(): continue
                total += (user['followers_count'] + user['friends_count'])/300

            if total > limits['remaining_hits']:
                print ""
                print "[WARNING] API calls left for current hour will be exhausted"
                print "[*] You need roughly %i API calls for this scan (could be less, try it anyway)" % math.ceil(total+9)
                print ""
                if not confirm('Do you wish to proceed?', False):
                    print ""
                    if confirm('Do you wish to perform another analysis?', True):
                        user1 = raw_input("Screen name #1: ").strip().lower()
                        user2 = raw_input("Screen name #2: ").strip().lower()
                        print ""
                        continue                
                    print ""
                    print "[*] API calls left: %i (reset on %s)"  % (limits['remaining_hits'], datetime.fromtimestamp(limits['reset_time_in_seconds']).strftime("%H:%M"))
                    print ""
                    sys.exit(1)
            else:
                print ""
                print "[*] Roughly %i API calls will be consumed" % math.ceil(total+9)
                print ""

            if user1 not in store.keys():
                print "[*] Getting friends for %s ... " % user1,
                data_user1['friends'] = getIDs(user1, 'friends')
                print "[OK]"
                print "[*] Getting followers for %s ... " % user1,
                data_user1['followers'] = getIDs(user1)
                print "[OK]"

            if user2 not in store.keys():
                print "[*] Getting friends for %s ... " % user2,
                data_user2['friends'] = getIDs(user2, 'friends')
                print "[OK]"
                print "[*] Getting followers for %s ... " % user2,
                data_user2['followers'] = getIDs(user2)
                print "[OK]"

            
            follow12 = False
            follow21 = False

            if data_user1['info']['id'] in data_user2['followers']:
                follow12 = True
            if data_user2['info']['id'] in data_user1['followers']:
                follow21 = True

            if follow12 and follow21:
                print ""
                print "[***] %s and %s follow each other" % (user1, user2)
                print ""
                info("%s and %s follow each other" % (user1, user2))
            elif follow12:
                print ""
                print "[***] %s follows %s" % (user1, user2)
                print ""
                info("%s follows %s" % (user1, user2))
            elif follow21:
                print ""
                print "[***] %s follows %s" % (user2, user1)
                print ""
                info("%s follows %s" % (user2, user1))

            both_friends = intersect(data_user1['friends'], data_user2['friends'])
            both_followers = intersect(data_user1['followers'], data_user2['followers'])
            notfollowed1 = substract(data_user1['friends'], data_user2['friends'])
            notfollowed2 = substract(data_user2['friends'], data_user1['friends'])
            u1friends2u2followers = intersect(data_user1['friends'], data_user2['followers'])
            u2friends2u1followers = intersect(data_user2['friends'], data_user1['followers'])

            if len(both_friends) > 0:
                friendsdata = getUsersData(both_friends)
                print ""
                print "[***] %s and %s both follow: " % (user1, user2),
                s = "%s and %s both follow: " % (user1, user2)
                for friend in friendsdata:
                    print friend['screen_name']+", ",
                    s += friend['screen_name']+", "
                print ""
                print ""
                info(s)

            if len(both_followers) > 0:
                followersdata = getUsersData(both_followers)
                print ""
                print "[***] %s and %s are both followed by: " % (user1, user2),
                s = " %s and %s are both followed by: " % (user1, user2)
                for follower in followersdata:
                    print follower['screen_name']+", ",
                    s += follower['screen_name']+", "
                print ""
                print ""
                info(s)

            if len(notfollowed1) > 0:
                friendsdata = getUsersData(notfollowed1)
                print ""
                print "[***] %s follows and %s does not follow: " % (user1, user2),
                s = " %s follows and %s does not follow: " % (user1, user2)
                for follower in friendsdata:
                    print follower['screen_name']+", ",
                    s += follower['screen_name']+", "
                print ""
                print ""
                info(s)
                
            if len(notfollowed2) > 0:
                friendsdata = getUsersData(notfollowed2)
                print ""
                print "[***] %s follows and %s does not follow: " % (user2, user1),
                s = " %s follows and %s does not follow: " % (user2, user1)
                for follower in friendsdata:
                    print follower['screen_name']+", ",
                    s += follower['screen_name']+", "
                print ""
                print ""
                info(s)

            if len(u1friends2u2followers) > 0:
                bridges = getUsersData(u1friends2u2followers)
                print ""
                print "[***] The following relationships have been found connecting %s => %s :" % (user1, user2)
                s = "The following relationships have been found connecting %s => %s :" % (user1, user2)
                for bridge in bridges:
                    print "%s => %s => %s " % (user1, bridge['screen_name'], user2)
                    s +=  "%s => %s => %s, " % (user1, bridge['screen_name'], user2)
                print ""
                info(s)

            if len(u2friends2u1followers) > 0:
                bridges = getUsersData(u2friends2u1followers)
                print ""
                print "[***] The following relationships have been found connecting %s => %s :" % (user2, user1)
                s = "The following relationships have been found connecting %s => %s :" % (user2, user1)
                for bridge in bridges:
                    print "%s => %s => %s " % (user2, bridge['screen_name'], user1)
                    s +=  "%s => %s => %s, " % (user2, bridge['screen_name'], user1)
                print ""
                info(s)


            if user1 not in store.keys():
                print "[*] Getting lists following %s ... " % user1,
                data_user1['followedlists'] = getLists(user1)
                print "[OK]"

            if user2 not in store.keys():
                print "[*] Getting lists following %s ... " % user2,
                data_user2['followedlists'] = getLists(user2)
                print "[OK]"

            list_ids = []
            for l in data_user1['followedlists']:
                list_ids.append(l['id'])
            data_user1['followedlistids'] = list_ids
            list_ids = []
            for l in data_user2['followedlists']:
                list_ids.append(l['id'])
            data_user2['followedlistids'] = list_ids
                

            common_lists = intersect(data_user1['followedlistids'], data_user2['followedlistids'])
            if len(common_lists) > 0:
                print ""
                print "[***] %s and %s both follow these lists: " % (user1, user2)
                s = "%s and %s both follow these lists: " % (user1, user2)
                for i in common_lists:
                    for l in data_user1['followedlists']:
                        if i == l['id']:
                            print "%s" % l['uri'] + ", ",
                            s +=  "%s" % l['uri'] + ", "
                print ""
                print ""
                info(s)

            
            if user1 not in store.keys():
                print "[*] Getting lists %s is member of ... " % user1,
                data_user1['listsmembership'] = getListMemberships(user1)
                print "[OK]"

            if user2 not in store.keys():
                print "[*] Getting lists %s is member of ... " % user2,
                data_user2['listsmembership'] = getListMemberships(user2)
                print "[OK]"

            list_ids = []
            for l in data_user1['listsmembership']:
                list_ids.append(l['id'])
            data_user1['listsmembershipids'] = list_ids
            list_ids = []
            for l in data_user2['listsmembership']:
                list_ids.append(l['id'])
            data_user2['listsmembershipids'] = list_ids
                

            common_lists = intersect(data_user1['listsmembershipids'], data_user2['listsmembershipids'])
            if len(common_lists) > 0:
                print ""
                print "[***] %s and %s are both followed by these lists: " % (user1, user2),
                s = "%s and %s are both followed by these lists: " % (user1, user2)
                for i in common_lists:
                    for l in data_user1['listsmembership']:
                        if i == l['id']:
                            try:
                                print "%s" % l['uri'] + ", ",
                                s += "%s" % l['uri'] + ", "
                            except:
                                continue
                print ""
                print ""
                info(s)


            limits = getLimits()            
            print ""
            print "[*] API calls left after scan: %i (reset on %s)"  % (limits['remaining_hits'], datetime.fromtimestamp(limits['reset_time_in_seconds']).strftime("%H:%M"))

            store[user1] = data_user1
            store[user2] = data_user2
            
        except:
            print ""
            print "Something went wrong :C"

        print ""
        if confirm('Do you wish to perform another analysis?', True):
            user1 = raw_input("Screen name #1: ").strip().lower()
            user2 = raw_input("Screen name #2: ").strip().lower()
            print ""
            continue
        else:
            print "[*] Have a nice day :)"
            sys.exit(1)



