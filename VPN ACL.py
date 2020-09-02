__author__ = "Ben Kelly"

from sys import argv
import paramiko
import re
import time
import os
from datetime import date
from pathlib import Path
import shutil
import getpass

#Sets up Paramiko SSH and sets it to automatically trust unknown keys
ssh_client = paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

def open_ssh(device,user,password):
    # Connect to the firewall and change to System Context
    ssh_client.connect(hostname=device,username=user,password=password)
    remote_connection = ssh_client.invoke_shell()
    remote_connection.send("terminal length 0\n")
    time.sleep(1)

    return remote_connection

def get_tunnels(connection):
    #Regular Expression to match Tunnel Interfaces
    expression = re.compile("Tu\d+")
    #Sends the show the command to list destination and receives the output back
    connection.send("show int des | in ^Tu.*_up.*_up\n")
    time.sleep(5)
    output = connection.recv(99999).decode(encoding='utf-8')
    #Filters the output and puts the tunnel names into a list
    tunnel_list = expression.findall(output)

    return tunnel_list

def get_destination(connection,tunnel):
    #Regular Expression to match Ip address
    expression = re.compile("\d{1,3}\.\d{1,3}\.\d{1,3}.\d{1,3}")
    #Sends the show the command to list destination and receives the output back
    connection.send("show run int {} | in tunnel destination\n".format(tunnel))
    time.sleep(5)
    output = connection.recv(99).decode(encoding='utf-8')
    time.sleep(2)
    #Filters the output and returns the IP
    tunnel_dest = expression.findall(output)

    return tunnel_dest


#Get user and router details
print('\n')
router_ip = input('Enter the IP address of the Router: ')
user = input('Enter Username: ')
password = getpass.getpass(prompt='Enter password: ')

print('\n \nRunning Script\n')

#Invoke the module to connect to the device.
router_ssh = open_ssh (router_ip,user,password)
#Invoke the module to get the list of Up Tunnels
tunnels = get_tunnels(router_ssh)

#Open the output Filters
access_list = open("access-list.txt", "w")

#loop through the list of tunnels and get ip's
for tun in tunnels:
    dest = get_destination(router_ssh,tun)
    print("Tunnel - {} - IP Address: {}\n".format(tun,dest[0]))
    access_list.write ("ip access-list extended ACL-WAN_IN permit ip host {} any\n".format(dest[0]))

#close the file
access_list.close()

#close the connection
router_ssh.close()

print('\nComplete!')
