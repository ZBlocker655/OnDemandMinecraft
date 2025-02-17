from flask import Flask, render_template, request, jsonify
from flask_cors import CORS, cross_origin
from multiprocessing import Process
import json
import boto3
import time
import paramiko
from io import StringIO
import os
import base64

app = Flask(__name__)
CORS(app)

#Paraminko ssh information
sshClient = paramiko.SSHClient()
sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())

#Waits for the server to reach a valid state so that commands can be executed on the server
def serverWaitOk(worldData):
    def dynamicServerWaitOk(instanceIp, client):

        checksPassed = False
        status = 'initializing'
        instanceIndex, _ = unpackWorldData(worldData)
        instanceIds = [os.environ[f'INSTANCE_ID_{instanceIndex}']]

        while (not checksPassed) and (status == 'initializing'):
            statusCheckResponse = client.describe_instance_status(InstanceIds = instanceIds)
            instanceStatuses = statusCheckResponse['InstanceStatuses']
            instanceStatus = instanceStatuses[0]
            instanceStatus = instanceStatus['InstanceStatus']
            status = instanceStatus['Status']
            checksPassed = status == 'ok'
            time.sleep(5)
        
        if checksPassed:
            initServerCommands(instanceIp, worldData)
        else:
            print('An error has occurred booting the server')

    return dynamicServerWaitOk
    
#SSH connects to server and executes command to boot minecraft server
def initServerCommands(instanceIp, worldData):
    instanceIndex, worldName = unpackWorldData(worldData)
    raw_key = os.environ[f"SSH_KEY_{instanceIndex}"]
    # When setting private key config in Heroku with: heroku config:set SSH_KEY=$(cat minecraft.pem)
    # Heroku seems to convert newlines to spaces. We need to convert those back to newlines.
    raw_key = unpackKeyFromEnvVar(raw_key)
    key = paramiko.RSAKey.from_private_key(StringIO(raw_key))

    # Connect/ssh to an instance
    try:
        # Here 'ubuntu' is user name and 'instance_ip' is public IP of EC2
        sshClient.connect(hostname=instanceIp, username="ubuntu", pkey=key)

        # Execute a command(cmd) after connecting/ssh to an instance
        stdin, stdout, stderr = sshClient.exec_command(f"screen -dmS minecraft bash -c 'sudo java -jar server.jar --world {worldName} --nogui'")
        for line in stdout:
            print(line)
        for line in stderr:
            print(line)
        print("COMMAND EXECUTED")
        # close the client connection once the job is done
        sshClient.close()

    except:
        print('Error running server commands')

#Main endpoint for loading the webpage
@app.route('/')
def loadIndex():
    return render_template('index.html')

@app.route('/tryKey')
def tryLoadKey():
    worldData = request.args.get('world')
    instanceIndex, _ = unpackWorldData(worldData)
    raw_key = os.environ[f"SSH_KEY_{instanceIndex}"]
    raw_key = unpackKeyFromEnvVar(raw_key)
    testPrivateKey(StringIO(raw_key))

@app.route('/initServerMC', methods = ['POST'])
def initServerMC():
    inputPass = request.form['pass']
    worldData = request.form['world']
    returnData = {}

    message = "Password Incorrect!"

    if inputPass == os.environ['SERVER_PASSWORD']:
        print(f"Attempting to start the server with access key {os.environ['ACCESS_KEY'][:9]}...")

        #Instantiate server here or return ip address if already running
        client = boto3.client(
            'ec2',
            aws_access_key_id=os.environ['ACCESS_KEY'],
            aws_secret_access_key=os.environ['SECRET_KEY'],
            region_name=os.environ['EC2_REGION']
        )
        message = manageServer(client, worldData)
    
    print(message)
    return render_template('index.html', ipMessage=message)


#Gets IP Address for return to webpage otherwise boots server
def manageServer(client, worldData):
    returnString = 'ERROR'

    instanceIndex, _ = unpackWorldData(worldData)
    instanceIds = [os.environ[f'INSTANCE_ID_{instanceIndex}']]
    response = client.describe_instances(InstanceIds = instanceIds)
    reservations = response['Reservations']
    reservation = reservations[0]

    instances = reservation['Instances']
    
    print("\nSERVER INSTANCES\n")
    print(instances)
    print("\n")
    if len(instances) > 0:
        instance = instances[0]
        state = instance['State']
        stateName = state['Name']
        print(f"Server instance found with state [{stateName}]")

        if (stateName == 'stopped') or (stateName == 'shutting-down'):
            #SETUP MULTIPROCESSING HERE INSTEAD OF REDIS
            print("Attempting start...")
            returnString = startServer(client, worldData)
        elif stateName == 'running':
            returnString = 'Already running at IP: ' + instance['PublicIpAddress']
        else:
            returnString = 'ERROR'
    return returnString

#Starts the specified AWS Instance from the configuration
def startServer(client, worldData):
    #Gets proper variables to attempt to instantiate EC2 instance and start minecraft server
    returnString = 'ERROR'
    instanceIndex, _ = unpackWorldData(worldData)
    instanceIds = [os.environ[f'INSTANCE_ID_{instanceIndex}']]
    response = client.start_instances(InstanceIds = instanceIds)

    stateCode = 0

    while not (stateCode == 16):
        time.sleep(3)

        print('\nAWS EC2 START RESPONSE\n')
        print(str(response))
        print('\n')

        response = client.describe_instances(InstanceIds = instanceIds)
        reservations = response['Reservations']
        reservation = reservations[0]

        instances = reservation['Instances']
        instance = instances[0]

        state = instance['State']
        stateCode = state['Code']
        
        print("\nSERVER INSTANCES\n")
        print(instances)
        print("\n")
        
    ipAddress = instance['PublicIpAddress']
    returnString = 'Server is starting, this may take a few minutes.\nIP: ' + ipAddress
    #SETUP MULTIPROCESSING HERE INSTEAD OF REDIS
    p = Process(target=serverWaitOk(worldData), args=(ipAddress, client))
    p.start()
    return returnString


# Unpacks world data string received from form.
#   Example: "i0;world" yields (0, "world")
def unpackWorldData(worldData):
    fields = worldData.split(";")
    instanceIndex = int(fields[0][1:])
    worldName = fields[1]
    return (instanceIndex, worldName)


def unpackKeyFromEnvVar(rawKey):
    keyHead = rawKey[:rawKey.find("KEY-----") + 8]
    keyTail = rawKey[rawKey.find("-----END"):]
    keyBody = rawKey[len(keyHead):-len(keyTail)]
    return keyHead + keyBody.replace(' ', '\n') + keyTail


def testPrivateKey(f):
    tag = "RSA"
    lines = f.readlines()
    print(f"Number of lines in key: {len(lines)}")
    start = 0
    beginning_of_key = "-----BEGIN " + tag + " PRIVATE KEY-----"
    while start < len(lines) and lines[start].strip() != beginning_of_key:
        print(f"Line {start} has {len(lines[start])} characters")
        start += 1
    if start >= len(lines):
        print(f"start = {start}, so not a valid {tag} private key file")
    # parse any headers first
    headers = {}
    start += 1
    while start < len(lines):
        l = lines[start].split(": ")
        if len(l) == 1:
            print("Parsed a line with no header.")
            break
        print(f"Parsed a line with header {l[0].lower()}")
        headers[l[0].lower()] = l[1].strip()
        start += 1
    # find end
    end = start
    ending_of_key = "-----END " + tag + " PRIVATE KEY-----"
    while end < len(lines) and lines[end].strip() != ending_of_key:
        end += 1
    # if we trudged to the end of the file, just try to cope.
    try:
        data = base64.decodebytes(b("".join(lines[start:end])))
    except base64.binascii.Error as e:
        print(f"base64 decoding error: {str(e)}")
    if "proc-type" not in headers:
        # unencryped: done
        print(f"We have data - {len(data)} bytes")
    # encrypted keyfile: will need a password
    proc_type = headers["proc-type"]
    if proc_type != "4,ENCRYPTED":
        print('Unknown private key structure "{}"'.format(proc_type))
    try:
        encryption_type, saltstr = headers["dek-info"].split(",")
    except:
        print("Can't parse DEK-info in private key file")
    print('Stop here')


def b(s, encoding="utf8"):
    """cast unicode or bytes to bytes"""
    if isinstance(s, bytes):
        return s
    elif isinstance(s, str):
        return s.encode(encoding)
    else:
        raise TypeError("Expected unicode or bytes, got {!r}".format(s))


if __name__ == "__main__":
    app.run()
