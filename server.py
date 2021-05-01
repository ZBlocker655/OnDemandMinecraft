from flask import Flask, render_template, request, jsonify
from flask_cors import CORS, cross_origin
from multiprocessing import Process
import json
import boto3
import time
import paramiko
import os

app = Flask(__name__)
CORS(app)

#Paraminko ssh information
dirname = os.path.dirname(__file__)
filename = os.path.join(dirname, "./minecraft.pem")
key = paramiko.RSAKey.from_private_key_file(filename)
sshClient = paramiko.SSHClient()
sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())

#Waits for the server to reach a valid state so that commands can be executed on the server
def serverWaitOk(world):
    def dynamicServerWaitOk(instanceIp, client):

        checksPassed = False
        status = 'initializing'
        instanceIds=[os.environ['INSTANCE_ID']]

        while (not checksPassed) and (status == 'initializing'):
            statusCheckResponse = client.describe_instance_status(InstanceIds = instanceIds)
            instanceStatuses = statusCheckResponse['InstanceStatuses']
            instanceStatus = instanceStatuses[0]
            instanceStatus = instanceStatus['InstanceStatus']
            status = instanceStatus['Status']
            checksPassed = status == 'ok'
            time.sleep(5)
        
        if checksPassed:
            initServerCommands(instanceIp, world)
        else:
            print('An error has occurred booting the server')

    return dynamicServerWaitOk
    
#SSH connects to server and executes command to boot minecraft server
def initServerCommands(instanceIp, world):
    # Connect/ssh to an instance
    try:
        # Here 'ubuntu' is user name and 'instance_ip' is public IP of EC2
        sshClient.connect(hostname=instanceIp, username="ubuntu", pkey=key)

        # Execute a command(cmd) after connecting/ssh to an instance
        stdin, stdout, stderr = sshClient.exec_command(f"sudo cp server.properties.{world} server.properties")
        for line in stdout:
            print line
        for line in stderr:
            print line
        stdin, stdout, stderr = sshClient.exec_command("screen -dmS minecraft bash -c 'sudo java -jar server.jar nogui'")
        for line in stdout:
            print line
        for line in stderr:
            print line
        print("COMMAND EXECUTED")
        # close the client connection once the job is done
        sshClient.close()

    except:
        print('Error running server commands')

#Main endpoint for loading the webpage
@app.route('/')
def loadIndex():
    return render_template('index.html')

@app.route('/initServerMC', methods = ['POST'])
def initServerMC():
    inputPass = request.form['pass']
    world = request.form['world']
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
        message = manageServer(client, world)
    
    print(message)
    return render_template('index.html', ipMessage=message)


#Gets IP Address for return to webpage otherwise boots server
def manageServer(client, world):
    returnString = 'ERROR'

    instanceIds = [os.environ['INSTANCE_ID']]
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
            returnString = startServer(client, world)
        elif stateName == 'running':
            returnString = 'IP: ' + instance['PublicIpAddress']
        else:
            returnString = 'ERROR'
    return returnString

#Starts the specified AWS Instance from the configuration
def startServer(client, world):
    #Gets proper variables to attempt to instantiate EC2 instance and start minecraft server
    returnString = 'ERROR'
    instanceIds = [os.environ['INSTANCE_ID']]
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
    p = Process(target=serverWaitOk(world), args=(ipAddress, client))
    p.start()
    return returnString


if __name__ == "__main__":
    app.run()
