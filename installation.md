
# Installation
This manual describes clariot installation on a Raspberry Pi. 
but you can also do local emulation for developing and prototyping. 

For clariot use we need to install docker under an ARM based arquitecture (Raspberry OS architecture), that is common for embedded systems. 
we are going to describe a basic installation for the raspberry pi3 platform using the raspbian OS.

## Raspbian installation
### Download raspbian
```
wget https://downloads.raspberrypi.org/raspbian_lite_latest
```
### Execute raspbian installation on an SD
You have to plug an SD into a Linux, MAC or Windows based computer
```
dd bs=4M if=2017-11-29-raspbian-stretch.img of=/dev/sdX conv=fsync
```
### Configure network interfaces
```
 Entering the raspberry (with ifconfig or ipconfig know the IP of you board or conencting to a local router and accesed via it dynamic IP) default user password is pi /raspberry, after entering your raspberry issue:
 
 $ apt get update  
 
 to verify that you can install packages over internet. 

```

### Install docker with hypriot
```
$ curl -s https://packagecloud.io/install/repositories/Hypriot/Schatzkiste/script.deb.sh | sudo bash
$ sudo apt-get install docker-hypriot=1.10.3-1
$ sudo sh -c 'usermod -aG docker $SUDO_USER'
$ sudo systemctl enable docker.service
$ systemctl unmask docker.service
$ systemctl unmask docker.socket
$ systemctl start docker.service
```
### Check that docker is running
```
$ sudo docker --version
$ sudo docker run hello-world   
$ sudo docker info 
$ docker rmi hello-world 
```
### Install docker-compose 
```
$ sudo apt-get install -y apt-transport-https
$ echo "deb https://packagecloud.io/Hypriot/Schatzkiste/debian/ jessie main" | sudo tee /etc/apt/sources.list.d/hypriot.list
$ sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 37BBEE3F7AD95B3F
$ sudo apt-get install docker-compose
```

### Check that docker-compose is up and running
```
$ docker-compose --version
```
## Install clariot

Dockerfile.clariot has a description of all the necessary services to run a demo application on the [Things layer](ThingsLayer.md).
```
$ docker-compose up -f Appcontianr/Dockerfile.clariot.yaml 
```

## Dockeriot automatic installation
* [Installation](installation.sh) script. 

## Test that clariot is up and running well.
* Check that clariot is running ok: 
```
check_clariot.sh
```
## Updates 
* (for images with docker on RPI) available at: https://blog.hypriot.com/downloads/

## Local development, emulation and testing
* You can also test the dockerfiles locally, for that install docker in your preffered OS. 

