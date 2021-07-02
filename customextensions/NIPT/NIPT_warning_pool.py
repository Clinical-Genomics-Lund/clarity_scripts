import sys
import getopt
import xml.dom.minidom
import pprint
import glsapiutil
from xml.dom.minidom import parseString

HOSTNAME = ""
VERSION = ""
BASE_URI = ""

DEBUG = False
api = None

ARTIFACTS = None
CACHE_IDS = []

def setupGlobalsFromURI( uri ):

	global HOSTNAME
	global VERSION
	global BASE_URI

	tokens = uri.split( "/" )
	HOSTNAME = "/".join(tokens[0:3])
	VERSION = tokens[4]
	BASE_URI = "/".join(tokens[0:5]) + "/"

	if DEBUG is True:
		print HOSTNAME
		print BASE_URI

def PoolWarning():
	api.reportScriptStatus( args[ "stepURI" ], "OK", 'OBS! Var god notera nedan:\n -   Alla prov som anvands som input till detta steg ska poolas i EN pool.\n -   Inga prov kan poolas in i poolen i efterhand.\n Om du ar medveten om ovan kriterier, tryck OK och fortsatt.' )  

def main():

	global api
	global args

	args = {}

	opts, extraparams = getopt.getopt(sys.argv[1:], "l:u:p:s:")

	for o,p in opts:
		if o == '-l':
			args[ "limsid" ] = p
		elif o == '-u':
			args[ "username" ] = p
		elif o == '-p':
			args[ "password" ] = p
		elif o == '-s':
			args[ "stepURI" ] = p

	setupGlobalsFromURI( args[ "stepURI" ] )
	api = glsapiutil.glsapiutil()
	api.setHostname( HOSTNAME )
	api.setVersion( VERSION )
	api.setup( args[ "username" ], args[ "password" ] )

	## at this point, we have the parameters the EPP plugin passed, and we have network plumbing
	## so let's get this show on the road!

	PoolWarning()

if __name__ == "__main__":
	main()
