import glob
from time import sleep
import subprocess

def main():
	files = glob.glob('/opt/gls/clarity/customextensions/PreAnalys/tmp_sendConc/*')

	for file in files:
		command1 = "cp %s /mnt/limsrs-clarity/InstrRcv/" % file
		command2 = "mv %s /opt/gls/clarity/customextensions/PreAnalys/sent/" % file
		print(command1 + '; ' + command2)

		subprocess.run(["bash", "-c", command1])
		subprocess.run(["bash", "-c", command2])

if __name__ == '__main__':
	main()

