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
		body.append( "This is an automated message from ClarityLIMS. The following sample is ready for data analysis:\n\n") 
	else :
		body.append( "This is an automated message from ClarityLIMS. The following samples are ready for data analysis:\n\n") 

	for dict in eMailInfo:
		body.append( "Lims ID:\t\t" + dict["limsID"] + "\n")
		body.append( "Submitted ID:\t\t" + dict["name"] + "\n")
		body.append( "Analysis:\t\t" + dict["analysis"] + "\n\n")

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

	#Get sample information
	actionsURI = args[ "stepURI" ] + "/actions"
	actionsDOM = parseString(api.GET(actionsURI))
	Inputs = actionsDOM.getElementsByTagName( "next-action" )
	artifactGoingNextStep = {}
	eMailListONCO = []
	eMailListOvarial = []

	for i in Inputs :
		iURI = i.getAttribute( "artifact-uri" )
		action = i.getAttribute( "action" ) 
		if action == "nextstep" :
			step = i.getAttribute( "step-uri" )
			artifactGoingNextStep[iURI] = step
	for a in artifactGoingNextStep:
		aDOM = parseString(api.GET(a))
		sURI = aDOM.getElementsByTagName( "sample" )[0].getAttribute( "uri" )
		sDOM = parseString(api.GET(sURI))
		#Warn for incorrect nextstep choice
		analysis = api.getUDF( sDOM, "Analysis" )
		if ("Paired" in analysis or "Parad" in analysis ) :
			if ("/api/v2/configuration/protocols/852/steps/1057" in artifactGoingNextStep[a]) :
				print "Paired samples must be merged before Data analysis. Please change the 'NextStep' choice"
				sys.exit(255)
		else :
			if ("/api/v2/configuration/protocols/852/steps/1056" in artifactGoingNextStep[a]) :
				print "Only Paired samples must be merged before Data analysis. Please change the 'NextStep' choice"
				sys.exit(255)
				
		#Filter out samples for mail notification
		if ("Onkogenetik" in analysis) :
			limsID = sDOM.getElementsByTagName( "smp:sample" )[0].getAttribute( "limsid" )
			name = sDOM.getElementsByTagName( "name" )[0].firstChild.data
			eMailListONCO.append( {"limsID" : limsID, "name":name, "analysis":analysis} )

		if ("Ovarialcancer" in analysis) :
			limsID = sDOM.getElementsByTagName( "smp:sample" )[0].getAttribute( "limsid" )
                        name = sDOM.getElementsByTagName( "name" )[0].firstChild.data
                        eMailListOvarial.append( {"limsID" : limsID, "name":name, "analysis":analysis} )

	email_SUBJECT_line = 'ClarityLIMS notification'

	if len(eMailListONCO) >=1 :
		email_body = email_template(eMailListONCO)
		send_email( email_SUBJECT_line, email_body, 'Bella.Sinclair@skane.se' )
		send_email( email_SUBJECT_line, email_body, 'Maryem.Salim@skane.se' )
		send_email( email_SUBJECT_line, email_body, 'Sofia.Saal@skane.se' )
		send_email( email_SUBJECT_line, email_body, 'Sofie.Samuelsson@skane.se' )
		send_email( email_SUBJECT_line, email_body, 'Anna.Isinger-Ekstrand@skane.se' )
		send_email( email_SUBJECT_line, email_body, 'Maria.Strandh@skane.se' )
		send_email( email_SUBJECT_line, email_body, 'Caroline.Monten@skane.se' )	# Added 210601
		send_email( email_SUBJECT_line, email_body, 'Tord.Jonson@skane.se' )		# Added 210601
		send_email( email_SUBJECT_line, email_body, 'GenSG@skane.se' )

	if len(eMailListOvarial) >=1 :
		email_body = email_template(eMailListOvarial)
                send_email( email_SUBJECT_line, email_body, 'Bella.Sinclair@skane.se' )
		send_email( email_SUBJECT_line, email_body, 'Morten.Grauslund@skane.se' )
		send_email( email_SUBJECT_line, email_body, 'Sofia.GruvbergerSaal@skane.se' )
		send_email( email_SUBJECT_line, email_body, 'Sofie.Samuelsson@skane.se' )
		send_email( email_SUBJECT_line, email_body, 'Maria.Strandh@skane.se' )
		send_email( email_SUBJECT_line, email_body, 'Heike.Kotarsky@skane.se' )		# Added 210603
		send_email( email_SUBJECT_line, email_body, 'Per.Leveen@skane.se' )		# Added 210603
		send_email( email_SUBJECT_line, email_body, 'Caroline.Monten@skane.se' )	# Added 210603
		send_email( email_SUBJECT_line, email_body, 'Tord.Jonson@skane.se' )		# Added 210603
		send_email( email_SUBJECT_line, email_body, 'Anna.IsingerEkstrand@skane.se' ) 	# Added 210604


if __name__ == "__main__":
	main()

