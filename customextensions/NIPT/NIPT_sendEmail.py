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


def email_template1(eMailInfo ):
	body = []
	
	body.append( "This is an automated message from ClarityLIMS. Reports have been created for the following NIPT samples:\n\n")
	body.append( "Lims ID\tSubmittedID\n")


	for dict in eMailInfo:
		body.append( dict["limsID"] + "\t")
		body.append( dict["name"] + "\t\n")
		
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

	Inputs = []
	eMailNIPT = []

	#Get sample information
	stepURI = args[ "stepURI" ] + "/details"
	stepDOM = parseString(api.GET(stepURI))
	IOMaps = stepDOM.getElementsByTagName( "input-output-map" )
	for IOMap in IOMaps:
		if IOMap.getElementsByTagName( "output" )[0].getAttribute( "output-generation-type" ) == "PerInput":
			Inputs.append(IOMap.getElementsByTagName( "output" )[0].getAttribute( "uri" ))
		
	Inputs = set(Inputs)

	for i in Inputs :
		aDOM = parseString( api.GET(i))
		
		limsID = aDOM.getElementsByTagName( "sample" )[0].getAttribute( "limsid" )
		subSampleURI = aDOM.getElementsByTagName( "sample" )[0].getAttribute( "uri" )
		sDOM = parseString(api.GET(subSampleURI))

		analysis = api.getUDF( sDOM, "Analysis" )
		department = api.getUDF( sDOM, "Department" )
		classification = api.getUDF( sDOM, "Classification" )

		name = sDOM.getElementsByTagName( "name" )[0].firstChild.data
		
		if (( "NIPT" in analysis ) and ( department == "Klinisk Genetik" ) and ( classification == "Rutinprov" ) ) :

			eMailNIPT.append({"name" : name, "limsID" : limsID , "department" : department}) 

	email_SUBJECT_line = 'ClarityLIMS notification'

	if len(eMailNIPT) >=1 :
		email_body = email_template1(eMailNIPT)
		send_email( email_SUBJECT_line, email_body, 'Maryem.Salim@skane.se' )
		send_email( email_SUBJECT_line, email_body, 'Elin.Lundblad-Andersson@skane.se' )
		send_email( email_SUBJECT_line, email_body, 'Asa.Hagstrom@skane.se' )
		send_email( email_SUBJECT_line, email_body, 'Caroline.Monten@skane.se' ) 
		send_email( email_SUBJECT_line, email_body, 'Kajsa.H.Nilsson@skane.se' ) 
		send_email( email_SUBJECT_line, email_body, 'Viktor.Henmyr@skane.se' ) 
		send_email( email_SUBJECT_line, email_body, 'Christel.Bjork@skane.se' )
		
		

if __name__ == "__main__":
	main()
