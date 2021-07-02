import sys
import getopt
import glsapiutil
import smtplib
from xml.dom.minidom import parseString
from email.mime.text import MIMEText
import subprocess

HOSTNAME = ""
VERSION = ""
BASE_URI = ""

api = None
SIMULATE = False

def setupGlobalsFromURI( uri ):

	global HOSTNAME
	global VERSION
	global BASE_URI

	tokens = uri.split( "/" )
	HOSTNAME = "/".join(tokens[0:3])
	VERSION = tokens[4]
	BASE_URI = "/".join(tokens[0:5]) + "/"


def email_template(eMailInfo ):
	body = []

	if len(eMailInfo) == 1:
		body.append( "This is an automated message from ClarityLIMS. The following sample is finished in Scout and is ready for report in Coyote/RS-LIMS:\n\n") 
	else :
		body.append( "This is an automated message from ClarityLIMS. The following samples are finished in Scout and are ready for report in Coyote/RS-LIMS:\n\n") 

	for dict in eMailInfo:
		body.append( "Lims ID:\t\t" + dict["limsID"] + "\n")
		body.append( "Submitted ID:\t\t" + dict["name"] + "\n")
		body.append( "Analysis:\t\t" + dict["analysis"] + "\n")
		body.append( "Sample Type:\t\t" + dict["sample type"] + "\n\n")

	body = "".join( body )
	return body


def send_email( email_SUBJECT_line, email_body, receiver ):

	cmd = """echo "{b}" | mailx -s "{s}" "{to}" 2>/dev/null""".format(b=email_body, s=email_SUBJECT_line, to=receiver)
	p=subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
	output, errors = p.communicate()
	print errors,output

def main():

	global api
	global args

	args = {}

	opts, extraparams = getopt.getopt(sys.argv[1:], "s:u:p:")

	for o,p in opts:
		if o == '-s':
			args[ "stepURI" ] = p
		elif o == '-u':
			args[ "username" ] = p
		elif o == '-p':
			args[ "password" ] = p

	setupGlobalsFromURI( args[ "stepURI" ] )
	api = glsapiutil.glsapiutil2()
	api.setHostname( HOSTNAME )
	api.setVersion( VERSION )
	api.setup( args[ "username" ], args[ "password" ] )

	detailsURI = args[ "stepURI" ]
	detailsXML = api.GET( detailsURI )
	detailsDOM = parseString( detailsXML )

	IOMaps = detailsDOM.getElementsByTagName( "input-output-map" )

	tmpList = []

	for IOMap in IOMaps:
		Nodes = IOMap.getElementsByTagName( "output" )
		if Nodes[0].getAttribute( "output-generation-type" ) == "PerInput" :
			oURI = Nodes[0].getAttribute( "uri" )
			if oURI not in tmpList:
				tmpList.append(oURI)

	eMailListOvarial = []

	for URI in tmpList:
		XML = api.GET( URI )
 		DOM = parseString( XML )
		name = DOM.getElementsByTagName( "name" )[0].firstChild.data
		sURI = DOM.getElementsByTagName( "sample" )[0].getAttribute( "uri" )

		# Only check unpaired samples
		if len(DOM.getElementsByTagName( "sample" )) == 1:
			sDOM = parseString(api.GET(sURI))
			analysis = api.getUDF( sDOM, "Analysis" )
			sampleType = api.getUDF( sDOM, "Sample Type" )

			#Filter out samples for mail notification
			if ("Ovarialcancer" in analysis and (sampleType == 'Normal' or sampleType == 'Normalprov') ) :
				limsID = sDOM.getElementsByTagName( "smp:sample" )[0].getAttribute( "limsid" )
                        	name = sDOM.getElementsByTagName( "name" )[0].firstChild.data
	                        eMailListOvarial.append( { "limsID" : limsID, "name":name, "analysis":analysis, "sample type":sampleType } )

	email_SUBJECT_line = 'ClarityLIMS notification'

	if len(eMailListOvarial) >=1 :
		email_body = email_template(eMailListOvarial)
		send_email( email_SUBJECT_line, email_body, 'Bella.Sinclair@skane.se' )
		send_email( email_SUBJECT_line, email_body, 'Morten.Grauslund@skane.se' )
		send_email( email_SUBJECT_line, email_body, 'Heike.Kotarsky@skane.se' )
		send_email( email_SUBJECT_line, email_body, 'Per.Leveen@skane.se' )
		send_email( email_SUBJECT_line, email_body, 'Maria.Strandh@skane.se' )

if __name__ == "__main__":
	main()

