from fabric.api import env
import pytz

#user name to ssh to hosts
env.user = 'root'
#user password (the better is to use pubkey authentication)
env.password = 'thumbtack'

env.show = ['debug']

env.roledefs = {
    #list of client hosts
    'client': [ "%s%02d" % ('client',x) for x in range(1,8+1)],

    #list of DB server hosts
    'server': [ "%s%02d" % ('server',x) for x in range(1,24+1)],

    #list of all available hosts
    'all_client': [ "%s%02d" % ('client',x) for x in range(1,8+1)],
}

#hosts timezone (required to correctly schedule ycsb tasks)
timezone = pytz.timezone('US/Pacific')
