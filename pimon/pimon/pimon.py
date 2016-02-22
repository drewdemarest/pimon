###############################################################################
# pimon is used as the main process by which a raspberry pi is put into       #
# combination monitor/sftp uploading mode. Two wireless cards are required.   #
# pimon is not smart enough to distinguish special adapter names.             #
# All it knows are wlan0 and wlan1. pimon is lazy and makes extenisve         #
# use of the subprocess call.                                                 #
# Plans for pimon                                                             #
# 1 - Smartly determine systemd service controllers                           #
# 2 - Smartly determine wireless cards with grep then python libs.            #
# 3 - Dyanmically create certificates, .conf files for stunnel and ovpn       #
#         by asking the server nicely.                                        #
# 4 - Integrate pysftp instead of subprocess.                                 #
# 5 - Replace most or all subprocess calls with actual, *for real*, libs.     #
###############################################################################

import os
import subprocess
import time

def pingInput():
    prompt = '> '
    
    print("Use default dns ping configuration? yes/no")
    selection = input(prompt)

    
    if selection == 'yes':
        address = '10.8.0.1'
        attempts = '3'

    elif selection == 'no':

        print("Please input the DNS IP Address")
        address = input(prompt)
    
        print("How many ping attempts?")
        attempts = input(prompt)
        
    return (attempts, address)

def ping(attempts, address):
	
    #Did the attempt string pass?
	print("Ping attempts set to: %s" % attempts)
	
    #Did the address string pass?
	print("IP Address set to: %s" % address)
	
    #Long command to run a ping
	pingTest = subprocess.Popen('ping -c %s %s' % (attempts, 
	address), shell=True)

    #Wait until pings
	time.sleep(5)
	
    #This will set pingTest as a boolean int (0 or 1)
    #I will now procede to clobber my variable
	pingTest = pingTest.wait()
	
    #This returns 1 or 0 to the main program.
	return pingTest

def escapeInput():
    prompt = '> '
    
    print("Please input the desired Wifi SSID")
    ssid = input(prompt)
    
    print("Starting or stopping the stack?")
    status = input(prompt)
    
    return (ssid, status)

def escape(ssid, status):

    #Kill the DHCP to windows
    subprocess.Popen('netctl stop ethernet-dhcp', shell=True)
    #bring up interface
    wlanUp = subprocess.Popen('netctl %s %s' % (status, ssid),
    shell=True)

    time.sleep(5)

    wlanUp = wlanUp.wait()

    #Start stunnel
    stunnel = subprocess.Popen('systemctl %s stunnel' % (status),
    shell=True)
    
    time.sleep(5)

    stunnel = stunnel.wait()

    #Start openvpn client configuration
    openvpn = subprocess.Popen('systemctl %s openvpn@client' % (status), 
    shell=True)
    
    time.sleep(5)
    
    openvpn = openvpn.wait()
    
    #Returns tuple of values
        
    return (wlanUp, stunnel, openvpn)
        

def monitorInput():
    subprocess.Popen('ip link', shell=True)
    time.sleep(1)
    prompt = '> '

    print("Specify which interface will go into monitor mode.")
    interface = input(prompt)
    print("Starting or stopping monitor mode?")
    state = input(prompt)
    
    return (state, interface)

def monitorMode(state, interface):
    #State is start or stop
    #interface is wlanX

    #Begin monitor mode for specified interface
    monitorMode = subprocess.Popen('airmon-ng %s %s' % (state, 
    interface), shell=True)
    
    #clobber
    monitorMode = monitorMode.wait()
    
    #return
    return monitorMode


def gatherDataInput():     
    prompt = '> '
    
    print("Please input the desired values for tcpdump")
    print("What is the name of the process screen?")
    screenName = input(prompt)
    
    print("How long in seconds will tcpdump capture?")
    capTime = input(prompt)
    
    print("Which interface will tcpdump use? Hint: wlan1mon")
    interface = input(prompt)
    
    print("How many pcap files will tcpdump make?")
    print("Note that file number*capturetime is total time.")
    fileQuantity = input(prompt)
    
    print("What will the pcap sequence be named?")
    fileName = input(prompt)
    
    print("Beginning capture...")
    
    return (screenName, capTime, interface, fileQuantity, fileName)   

def gatherData(screenName, capTime, interface, fileQuanity, fileName):

    gatherData = subprocess.Popen('screen -S %s tcpdump -G %s -s 0 -i %s -W %s -w %s.pcap' 
    % (screenName, capTime, interface, fileQuanity, fileName), shell=True)

    gatherData = gatherData.wait()

    return gatherData

def connect():
    
    #Creates a configureation tuple from escapeInput()
    escapeConf = escapeInput()

    #Asks the user for ping testing parameters.
    pingConf = pingInput()
    
    #Starts the network escape with the escapeConf tuple
    escape(*escapeConf)

    
    #If the user decided to start the connection process
    #rather than stop or reset it, then pimon will attempt
    #to maintain the connection
    if escapeConf[1] == 'start':
        
        #Determines if the pi is connected to the network.
        escapeState = ping(*pingConf)
        
        #If the pi has failed to connect on the first try it
        # will keep trying to reconnect to the network.
        while escapeState != 0:
        
            #This stops all network magic for a fresh start.
            escape(escapeConf[0], 'stop')
        
            #Helpful debuggin on the escape state.
            print("escape state: %s" % escapeState)
        
            #This keeps the stop/start process from stepping
            #on its own toes.
            time.sleep(2)
        
            #Starts all network magic.
            escape(escapeConf[0], 'start')
        
            #Tests to see if a connection is esablished with
            #ping
            escapeState = ping(*pingConf)
        
        #A Connection has been established with the VPN server.
        #Great!
        while escapeState == 0:
            
            #Ping out every minute to make sure the connection
            #is still up.
            time.sleep(30)
            
            #Ping test
            escapeState = ping(*pingConf)
            
            #Helpful debugging on the escape state.
            print("escape state: %s" % escapeState)
            
            #If the pi loses it's established connection it will
            #attempt to reconnect itself.
            while escapeState != 0:
                
                #This stops all network magic for a fresh start.                
                escape(escapeConf[0], 'stop')
                
                #Helpful debuggin information on the escape state.
                print("escape state: %s" % escapeState)
                
                #This keeps the stop/start process from stepping
                #on its own toes.
                time.sleep(2)
                
                #Starts all the network magic
                escape(escapeConf[0], 'start')
                
                #Tests to see if a connection is esablished with
                #ping
                escapeState = ping(*pingConf)
    else:
        print("Oh no something has broken!")     

print("What would you like to do?")
print("1: Configure a connection")
print("2: Start or stop monitor mode")
print("3: Start Packet Capture")
prompt = '> '
selection = input(prompt)

if selection == '1':
    connect()

elif selection == '2':
    monitorMode(*monitorInput())

elif selection == '3':
    gatherData(*gatherDataInput())
