## Dockeriot things layer.
Dockeriot can be used for specific application on the "things layer" for an iot environment. 
The things layer depicts tjre principal containers:

* Appcontainer: Application specific container definitions. 
* Comcontainer: Comunication to other machines or iot devices, container definitions.
* SenActcontainer Sensor/actuators specific container definitions. 

For example, you are building an application that runs a webserver on an iot device (f.e raspberrypi).
locally, you could build your app (to test and prototype) and then run it: 
```
docker build -< Appcontainer/clariot.Dockerfile -t clariot
docker run -w /Appcontainer/ -t -i clariot 
```

Note: This example is using only an Appcontainer, but we could also define: Communication and Sensor-actuator containers, 
that are part of the "Things layer"

The same building/run procedure must be applied on all the iot devices you want to add
to the clariot environment. 


