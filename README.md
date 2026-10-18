# mqtt-wifi-esp32-flask-web-page-garage-door-controller
code that controls an esp32 which uses a relay to open and close a garage door

An esp32 soc has a relay and a couple of HC-sr04 sonic sensors attached which can switch a garage door motor. The sensors test if the door is open or closed.
The esp32 runs an mqtt loop that is subscribe to a topic. If it receives a payload "press" it will activate the relay (on  then off) which switches the door opener motor on.
If it receives the payload "status" it will check the output of the ultrasonic senors to determine if the door is open or closed.

A NUC (small computer)running Ubuntu has a flask web page is used to send the mqtt payloads, update the web page with the door status and control access.



