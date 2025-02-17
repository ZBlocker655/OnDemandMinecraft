# On Demand Minecraft Server
Using a Python Flask application and AWS, this repository launches an AWS EC2 Instance to host a Minecraft server upon request from users through the web application. The server will automatically shut down after the server has crashed or is empty for 15 minutes. This makes server hosting for small communities very inexpensive. For up to 20 players you can expect $0.02 per hour the server runs. The largest benefit of this system is that the server bill diminishes if your community decides to take a break from the game, and will be ready to pick back up when you want to play again. No subscriptions are required.

Note that this configuration will likely require familiarity with programming, SSH, and the command line.


# AWS Setup
This step will properly configure your AWS account and configuration.py file so that an instance can be created via the createInstance.py script.

 1. Create or access an **AWS Account**. Under the **User Dropdown** in the    **Toolbar**, select **Security Credentials**, then **Access Keys**, and finally **Create New Access Key**. Download this file, open it, and copy the values of **AWSAccessKeyId** and **AWSSecretKey** to **ACCESS_KEY** and **SECRET_KEY** in the **configuration.py** file in the root directory of the repository.
	
	<code>ACCESS_KEY = 'YourAWSAccessKeyIdHere'
	SECRET_KEY  =  'YourAWSSecretKeyHere'</code> 

 3. Navigate to the **EC2 Dashboard** under the **Services Dropdown** and select **Security Groups** in the sidebar. Select **Create Security Group**, input **minecraft** for the **Security group name**. Create **Inbound Rules** for the following:
	 - Type: **SSH** Protocol: **TCP** Port Range: **22** Source: **Anywhere**
	 - Type: **Custom TCP Rule** Protocol: **TCP** Port Range: **25565** Source: **Anywhere**
	 - Type: **Custom UDP Rule** Protocol: **UDP** Port Range: **25565** Source: **Anywhere**
	 
	 In **configuration.py** in the root directory, set **ec2_secgroups** to the name of the security group.
	 
	 <code>ec2_secgroups =  ['YourGroupNameHere']</code>

3. Under the **EC2 Dashboard** navigate to **Key Pairs** in the sidebar. Select **Create Key Pair**, provide a name and create. Move the file that is downloaded into the root directory of the project. In **configuration.py** in the root directory, set ** ec2_keypair** to the name entered, and **SSH_KEY_FILE_NAME** to the name.pem of the file downloaded.

	THIS MIGHT BE SUBJECT TO CHANGE
		<code>ec2_keypair =  'YourKeyPairName'
		SSH_KEY_FILE_PATH  =  './YourKeyFileName.pem'</code>

4. This step is concerned with creating the AWS instance. View [https://docs.aws.amazon.com/general/latest/gr/rande.html](https://docs.aws.amazon.com/general/latest/gr/rande.html) (Or google AWS Regions), and copy the  **Region** column for the **Region Name** of where you wish to host your server. In **configuration.py** of the root directory, set the **ec2_region** variable to the copied value.

	<code>ec2_region =  "Your-Region-Here"</code>

5. Navigate to [https://aws.amazon.com/ec2/instance-types/](https://aws.amazon.com/ec2/instance-types/) and select one of the T3 types (with the memory and CPU you desire, I recommend 10 players/GB). Copy the value in the **Model** column. I've configured mine to use **t3.small**. In **configuration.py** of the root directory, set the **ec2_instancetype** variable to the copied value.

	<code>ec2_instancetype =  't3.yourSizeHere'</code>

6. Then we must select an image for the instance to boot. Navigate to [https://cloud-images.ubuntu.com/locator/ec2/](https://cloud-images.ubuntu.com/locator/ec2/), in the filter at the bottom of the screen, select your region of choice under **Zone**, pick any LTS (Latest Stable) under **Version**, under **Arch** select **amd64**, and **hvm:ebs** under **Instance Type**. Select one of the images available and copy the **AMI-ID**. In **configuration.py** of the root directory, set the **ec2_amis** variable to the copied value.

	<code>ec2_amis =  ['ami-YourImageIdHere']</code>

7. At this point you should have the necessary configuration to create a new instance through the **createInstance.py** script in the **root** folder. Open a command line in the utilityScripts directory of the project, and execute:

	<code>pip install -r requirements.txt</code>
	
	After successful installation of dependencies execute:

	<code>python utilityScripts/createInstance.py</code>

	Copy the **Instance ID** that is output into the terminal. In **configuration.py** of the root directory, set the **INSTANCE_ID** variable to the copied value.

	<code>INSTANCE_ID  =  'i-yourInstanceIdHere'</code>


# Web Application Deployment
In this step the project will get deployed to Heroku's free hosting. This part of the application provides a rudimentary UI and Web URL for users to start the server.

Before deployment it will be important to set the password for the server to start. In **configuration.py** of the root directory, set the **SERVER_PASSWORD** variable to the password of your choosing.

   <code>SERVER_PASSWORD='YourPasswordHere'</code>
 1. Create or have access to a Heroku account.
 2. Install and setup the **Heroku CLI** onto your computer. [https://devcenter.heroku.com/articles/heroku-cli#download-and-install](https://devcenter.heroku.com/articles/heroku-cli#download-and-install)
 3. In the command line for the directory of this project, type:
	 <code>heroku create YourProjectNameHere</code>
4. Once this new project has been created, it is time to push the project to Heroku.
	<code>git push heroku master</code>
5. The URL to your hosted site should be: YourProjectNameHere.herokuapp.com
6. Access your site and launch/access your server!

# AWS Instance Configuration

This step will configure the AWS Linux server to run the minecraft server. It will include SSH connecting to the server, gaining admin privileges, installing java, directory setup, moving shell scripts onto the server, and making a CRON job for these shell scripts. Note that this step will include both an SSH client and a File Transfer client (such as FileZilla) on your PC.

## SSH in to the server

The first step will be to get SSH into the server instance. Using the key downloaded from AWS in the section above, add this key to PuTTY or simply access it through command line. The IP address can be obtained by entering the server password on the site, or through the EC2 Dashboard, selecting the iPV4 address from the corresponding instanceID in your configuration file. For MacOS and Linux systems

```
ssh -i pathToYourKeyFileHere ubuntu@IPAddress
```

## Update packages

Update the packages on the system by typing the command:

```
sudo apt update
```

## Make `ubuntu` user admin

Make the ubuntu user admin if it isn't already with:
 
```
adduser ubuntu sudo
```

## Install Java

The next step will be to install JavaJDK onto your system.

### For vanilla Minecraft

For newer versions you may enter:

```
sudo apt install openjdk-11-jdk-headless
```

If this doesn't work you can use <code>sudo apt list</code> and search through these packages for an alternative java version.

### For Forge server

Forge as of 1.17.1 runs on Java 16.

From [this guide](https://www.linuxuprising.com/2021/03/how-to-install-oracle-java-16-on-debian.html)...

- Add the Oracle Java 16 PPA repository (you'll need to follow some prompts here): ```sudo add-apt-repository ppa:linuxuprising/java```
- `sudo apt update`
- `sudo su` (to operate as `root` for a bit)
- `echo "deb http://ppa.launchpad.net/linuxuprising/java/ubuntu focal main" | tee /etc/apt/sources.list.d/linuxuprising-java.list`
- `apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 73C3DB2A`
- `apt-get update`
- `exit` (exit `root` access)
- `sudo apt install oracle-java16-installer --install-recommends`

## Copy over files

Open up an FTP client such as FileZilla and connect to the same address as the same user with the same IP address. Drag all files from the **instanceSetup** folder from this repository, into the root directory of the current user (probably **ubuntu**, for the purposes of these commands I will be using **ubuntu**, but feel free to replace with your own user if appropriate).

## Edit `server.properties`

If desired, make final edits to `server.properties`.

## Download Minecraft

### Vanilla Minecraft

Download the desired Minecraft server version from [https://www.minecraft.net/en-us/download/server/](https://www.minecraft.net/en-us/download/server/), rename it **server.jar** and drag it into the root directory of the user using FileZilla.

### Forge server

Download the desired Forge installer JAR, copy to the server.

Then run `java -jar forge-x.xx.x-installer.jar --installServer`

## Set up screens folder

1. Using the FTP client, create a new folder in the root directory of the current user called **screens**  
OR  
In the SSH client, create a folder in the current directory with the command:
	<code>sudo mkdir screens</code>
1. Then execute the following commands:
  - <code>sudo chown ubuntu /home/ubuntu/screens</code>
  - <code>sudo chmod 700 /home/ubuntu</code>
1. Then execute the next command:
  - <code>export SCREENDIR=/home/ubuntu/screens</code>
1. Then execute the command:
  - <code>sudo crontab /home/ubuntu/crontab -u ubuntu</code>

	Feel free to close the server through the AWS console or execute the command:
	<code>sudo /sbin/shutdown -P +1</code>

At this point you may restart the server from the Web Application using the password you configured. You should then be able to play!

# Additional Remarks
## Minecraft Memory Configuration
The server startup command does not specify memory constraints by default, but is available to be specified in Configuration.py. In the event that you configure this from an empty string, **the trailing space is required** as in the example below. Traditional minecraft server flags apply for this configuration.
<code>MEMORY_ALLOCATION='-Xmx1024M -Xms1024M '</code>
## UI Configuration
The title and header for the site can be changed in **/templates/index.html**. Feel free to add any more content or styling to the site, though be careful not to change any form, input, button, or script elements in the template.

## Server Maintenance
Maintaining the server is fairly straightforward and is done primarily through FileZilla. Updating the server file can be done by downloading the new server file, renaming it to **server.jar** and replacing the old file on the server. The world file can be backed up to your PC manually though there is no automated process at this time.

# Add new server

## Set up new EC2 instance

## Set up EventBridge alarms

## Follow instructions under "AWS Configuration"

### Exceptions

- No Forge
- No crontab (will use EventBridge instead)

### Further steps

- Run Minecraft locally - set up world
- FTP over any data packs
- Run Minecraft again - using screen command - make sure it works
- Try connect from Minecraft client

## Push update to Heroku page

- Update environment variables at Heroku
  - `NUM_INSTANCES` increment
  - `INSTANCE_ID_{N}` - set to EC2 instance ID
  - `SSH_KEY_{N}` - set to content of `minecraft2.pem` with newlines removed
- Update `index.html` with new step
- `git push heroku main`

## Verify

- Start server from web page - confirm connect

# Heroku commands

## List environment variables

`heroku config`

## Set environment variable

`heroku config:set VAR_NAME=value`

### Set SSH key

Do this through the Heroku GUI!!!

## View logs

`heroku logs`
