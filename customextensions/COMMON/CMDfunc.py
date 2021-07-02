from xml.dom.minidom import parseString
import subprocess

def setupGlobalsFromURI( uri ):

        global HOSTNAME
        global VERSION
        global BASE_URI

        tokens = uri.split( "/" )
        HOSTNAME = "/".join(tokens[0:3])
        VERSION = tokens[4]
        BASE_URI = "/".join(tokens[0:5]) + "/"

	return HOSTNAME, VERSION, BASE_URI

def getStepConfiguration( stepURI, api ):

        response = ""

        if len( stepURI ) > 0:
                stepXML = api.getResourceByURI( stepURI )
                stepDOM = parseString( stepXML )
                nodes = stepDOM.getElementsByTagName( "configuration" )
                if nodes:
                        response = nodes[0].toxml()

        return response

def send_email( email_SUBJECT_line, email_body, receiver ):

	cmd = """echo "{b}" | mailx -s "{s}" "{to}" 2>/dev/null""".format(b=email_body, s=email_SUBJECT_line, to=receiver)
	p=subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
	output, errors = p.communicate()

	print( errors, output )

def send_fail_email(script):
	email_SUBJECT_line = 'ClarityLIMS notification - Automation Failed'
	email_body = "This is an automated message from ClarityLIMS. Automatic upload of samples have failed in script:\n\n%s\n\n" % script

	send_email( email_SUBJECT_line, email_body, 'Bella.Sinclair@skane.se' )

def send_success_email(projects, nrLines):
	email_SUBJECT_line = 'ClarityLIMS notification'

	if len(projects) > 1:
		email_body = "This is an automated message from ClarityLIMS. Samples have successfully been uploaded to the following projects:\n\n" 

		for project in projects:
			email_body = email_body + "\t%s\n" % projects

		email_body = email_body + '\n'

	else:
		email_body = "This is an automated message from ClarityLIMS. Samples have successfully been uploaded to project:\n\n\t%s\n\n" % projects[0]

	email_body = email_body + 'Number of samples: %d\n' % nrLines
	send_email( email_SUBJECT_line, email_body, 'Bella.Sinclair@skane.se' )

