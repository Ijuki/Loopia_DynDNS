#!/usr/bin/env python
from optparse import OptionParser
import sys
import httplib
import base64
import string
import ConfigParser

parser = OptionParser()
parser.add_option("-v", action="store_true", dest="verbose", default=False, help="Verbose output")
parser.add_option("-m", "--manual_ip", dest="manual_ip", default=False, help="Manually set IP, if unset dynamically fetch IP")
parser.add_option("-d", "--host", dest="hostname", default="unset", help="Hostname to configure")
parser.add_option("-u", "--user", dest="username", default="unset", help="Username for loopia.se")
parser.add_option("-p", "--password", dest="password", default="unset", help="Password for loopia.se") 
parser.add_option("-c", "--config", dest="config", default="unset", help="Configuration File")
parser.add_option("-s", "--save-config", dest="savefile", default="unset", help="Save configuration to file")
(options, args) = parser.parse_args()

if options.username == "unset" and options.config == "unset":
 print "No username supplied"
 sys.exit(1)

if options.password == "unset" and options.config == "unset":
 print "No password supplied"
 sys.exit(1)

if options.hostname == "unset" and options.config == "unset":
 print "No hostname supplied"
 sys.exit(1)

if options.config != "unset":
 if options.verbose == True:
  print "Reading config"
 config = ConfigParser.ConfigParser()
 config.read(options.config)

 if options.verbose == True:
  print "Hostname:", config.get("LoopiaDNS", "hostname")
  print "Username:", config.get("LoopiaDNS", "username")
  print "Password:", config.get("LoopiaDNS", "password")

 if options.hostname != "unset":
  if options.verbose == True:
   print "Passed hostname has precedence, setting hostname to:", options.hostname
 else:
  options.hostname = config.get("LoopiaDNS", "hostname")

 if options.username != "unset":
  if options.verbose == True:
   print "Passed username has precedence, setting username to:", options.username
 else:
  options.username = config.get("LoopiaDNS", "username")
  
 if options.password != "unset":
  if options.verbose == True:
   print "Passed password has precedence, setting password to:", options.password
 else:
  options.password = config.get("LoopiaDNS", "password")

 if options.manual_ip != False:
  if options.verbose == True:
   print "Passed manual ip has precedence, setting manual ip:", options.manual_ip
 else:
  try:
   config.get('LoopiaDNS', 'manual_ip')
  except ConfigParser.NoOptionError:
   pass
  else:
   if options.verbose == True:
    options.manual_ip = config.get('LoopiaDNS', 'manual_ip')

authstring = base64.encodestring('%s:%s' % (options.username, options.password)).replace('\n', '')

if options.savefile != "unset":
 print "Saving configuration to file:", options.savefile
 saveconfig = ConfigParser.ConfigParser()
 saveconfig.add_section('LoopiaDNS')
 saveconfig.set('LoopiaDNS', 'hostname', options.hostname)
 saveconfig.set('LoopiaDNS', 'username', options.username)
 saveconfig.set('LoopiaDNS', 'password', options.password)
 if options.manual_ip != "unset":
  saveconfig.set('LoopiaDNS', 'manual_ip', options.manual_ip)

 with open(options.savefile, 'wb') as configfile:
  saveconfig.write(configfile)
 sys.exit(1)

if options.manual_ip == False:
 pull = httplib.HTTP("dns.loopia.se")
 pull.putrequest("GET", "/checkip/checkip.php")
 pull.putheader("User-Agent", "gnuttNet IP-fetcher")
 pull.endheaders()
 pull.send('')

 statuscode, statusmessage, header = pull.getreply()
 data = pull.getfile().read()
 pull.close()

 findstring = "Current IP Address: "
 findstring2 = "</body>"
 position = data.rfind(findstring)
 position2 = data.rfind(findstring2)
 ipaddress = data[position+len(findstring):position2]
 if options.verbose == True:
  print "IP-adress: " + ipaddress
 ip=ipaddress
else:
 if options.verbose == True:
  print "User specified IP-adress: " + options.manual_ip
 ip=options.manual_ip

auth = base64.encodestring('%s:%s' % (options.username, options.password)).replace('\n', '')

if options.verbose == True:
 print ">Connecting to dns.loopia.se"
 print ">Username: " + options.username
 print ">Authstring: " + auth
 print ""

push = httplib.HTTP("dns.loopia.se")
push.putrequest("POST", "/XDynDNSServer/XDynDNS.php?system=custom&myip=" + ip + "&hostname=" + options.hostname)
push.putheader("User-Agent", "gnuttNet IP Updater")
push.putheader("Authorization", "Basic %s" % auth)
push.putheader("Content-length", 0)
push.endheaders()
push.send('')

statuscode, statusmessage, header = push.getreply()
res = push.getfile().read()

push.close()

if options.verbose == True:
 print "Status:", statuscode, statusmessage
 print "Header\n", header
 print res

if res == "badauth":
 print "Incorrent username/password"
 sys.exit(2)
elif res == "good":
 if options.verbose == True:
  print "IP-address updated"
 sys.exit(0)
elif res == "nochg":
 if options.verbose == True:
  print "No change"
 sys.exit(0)
elif res == "nofqdn":
 print "The hostname specified is not a fully-qualified domain name (not in the form hostname.dyndns.org or domain.com)."
 sys.exit(5)
elif res == "nohost":
 print "The hostname specified does not exist in this user account (or is not in the service specified in the system parameter)."
 sys.exit(5)
elif res == "numhost":
 print "Too many hosts (more than 20) specified in an update. Also returned if trying to update a round robin (which is not allowed)."
 sys.exit(5)
elif res == "abuse":
 print "The hostname specified is blocked for update abuse."
 sys.exit(5)
else:
 print "Unknown result code:", res
 sys.exit(1)
