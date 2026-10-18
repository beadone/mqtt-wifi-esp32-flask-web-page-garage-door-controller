#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <Pinger.h>
#include <PubSubClient.h>
//#include <WiFiUdp.h>
#include <stdio.h>
#include <string.h>
extern "C"
{
  #include <lwip/icmp.h> // needed for icmp packet definitions
}

// Set global to avoid object removing after setup() routine
Pinger pinger;

#define MSG_BUFFER_SIZE (50)
#define LED1 D0
#define LED2 D1
#define RELAY D2
const int trigPinfront = 12;
const int echoPinfront = 14;
const int trigPinback = 15;
const int echoPinback = 13;
#define SOUND_VELOCITY 0.034

int loopcounter = 0;
long durationfront; 
float distanceCmfront;

long durationback; 
float distanceCmback;

//--------------------------------------
// config (edit here before compiling) add the usernames and passwords
//--------------------------------------

const char* ssid = "xxxxxxxxxxx";
const char* password = "xxxxxxxxxx";
const char* mqtt_server = "192.168.1.18"; // eg. your-demo.cedalo.cloud or 192.168.1.11
const uint16_t mqtt_server_port = 1883; // or 8883 most common for tls transport
const char* mqttUser = "xxxxxxxxx";
const char* mqttPassword = "xxxxxxxxxxxx";
const char* mqttTopicIn = "esp-8266-in";
const char* topicdoor = "garage/door";
//--------------------------------------
// globals
//--------------------------------------

WiFiClient wifiClient;

PubSubClient mqttClient(wifiClient);

//--------------------------------------
// function setup_wifi called once
//--------------------------------------
void setup_wifi() {

  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("WiFi connected");
}

void IsDoorOpen()  {
      const float OpenDistance = 5;
      digitalWrite(trigPinfront, LOW);
      delayMicroseconds(2);
     // Sets the trigPin on HIGH state for 10 micro seconds
     digitalWrite(trigPinfront, HIGH);
     delayMicroseconds(10);
     digitalWrite(trigPinfront, LOW);  
     // Reads the echoPin, returns the sound wave travel time in microseconds
     durationfront = pulseIn(echoPinfront, HIGH);
     // Calculate the distance
     distanceCmfront = durationfront * SOUND_VELOCITY/2;
 
     Serial.print("Distance front (cm): ");
     Serial.print(distanceCmfront);

     if (distanceCmfront < OpenDistance){     
      Serial.println(", front is closed, back should be closed");   
     } else {
      Serial.println(", front is open, back can be open or closed");
     }

     digitalWrite(trigPinback, LOW);
     delayMicroseconds(2);
     digitalWrite(trigPinback, HIGH);
     delayMicroseconds(10); 
     digitalWrite(trigPinback, LOW);
     durationback = pulseIn(echoPinback, HIGH);
     distanceCmback = durationback * SOUND_VELOCITY/2;
     Serial.print("Distance back (cm): ");
     Serial.print(distanceCmback);

     if (distanceCmback < OpenDistance){
      // door is open
      Serial.println(", back is open, front should be open");   
     } else {
      Serial.println(", back is closed, front can be open or closed");
     }

    if ((distanceCmfront < OpenDistance) && (distanceCmback > OpenDistance)){
     mqttClient.publish(topicdoor,"CLOSED");
    }
    if ((distanceCmfront > OpenDistance) && (distanceCmback < OpenDistance)){
     mqttClient.publish(topicdoor,"OPEN");
    }
    if ((distanceCmfront > OpenDistance) && (distanceCmback > OpenDistance)){
     mqttClient.publish(topicdoor,"PARTIAL");
    }
    if ((distanceCmfront < OpenDistance) && (distanceCmback < OpenDistance)){
     mqttClient.publish(topicdoor,"ERROR");
    }

}



//--------------------------------------
// function callback called everytime 
// if a mqtt message arrives from the broker
//--------------------------------------
void callback(char* topic, byte* payload, unsigned int length) {
  char messageBuffer[30];
  int LEDState = 0;
   

    Serial.print("Message arrived on topic: '");
    Serial.print(topic);
    Serial.print("' with payload: ");
    for (unsigned int i = 0; i < length; i++) {
      Serial.print((char)payload[i]);
    }
    Serial.println();
    memcpy(messageBuffer, payload, length);  //copy the payload to a buffer
    messageBuffer[length] = '\0';  //terminate with a zero to convert to a C style string
  //program needs updating to check the topic first

    if (strcmp(messageBuffer, "press") == 0)
    {
      digitalWrite(LED1, !(digitalRead(LED1)));
      Serial.println("led1 should toggle");
      digitalWrite(RELAY, LOW);
      delay(500);
      digitalWrite(RELAY, HIGH);
      IsDoorOpen();
    }

    if (strcmp(messageBuffer, "status") == 0)
    {
      IsDoorOpen();
    }
}

//--------------------------------------
// function connect called to (re)connect
// to the broker
//--------------------------------------
void connect() {
  while (!mqttClient.connected()) {
    Serial.print("Attempting MQTT connection...");
    String mqttClientId = "esp8266";
    if (mqttClient.connect(mqttClientId.c_str(), mqttUser, mqttPassword)) {
      Serial.println("connected");
      mqttClient.subscribe(mqttTopicIn);
    } else {
      Serial.print("failed, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" will try again in 5 seconds");
      delay(5000);
    }
  }
}

//--------------------------------------
// main arduino setup fuction called once
//--------------------------------------
void setup() {
  Serial.begin(115200);

  setup_wifi();
  mqttClient.setServer(mqtt_server, mqtt_server_port);
  mqttClient.setCallback(callback);
  connect();
  pinMode(LED1, OUTPUT);
  pinMode(LED2, OUTPUT);
  pinMode(trigPinfront, OUTPUT); // Sets the trigPin as an Output
  pinMode(echoPinfront, INPUT); // Sets the echoPin as an Input
  pinMode(trigPinback, OUTPUT); // Sets the trigPin as an Output
  pinMode(echoPinback, INPUT); // Sets the echoPin as an Input
  pinMode(RELAY,OUTPUT);
  digitalWrite(RELAY, HIGH);
}

//--------------------------------------
// main arduino loop fuction called periodically
//--------------------------------------
void loop() {

  
  mqttClient.loop();
  // periodically check the wifi connection and mqtt
  loopcounter = loopcounter + 1;
  if (loopcounter > 1000000 )
  {
    //Serial.println(loopcounter);
    loopcounter = 0;
    
    
    if(pinger.Ping(IPAddress(192,168,1,1)) == true)
    {
      //Serial.println("ping ok");
      if (!mqttClient.connected()) {
          connect();
      }
      IsDoorOpen();
    }else{
    
      Serial.println("ping not ok"); 
      //wait and try again
      delay(10000);
      if(pinger.Ping(IPAddress(192,168,1,1)) == true)
      {
        Serial.println("ping ok second go");
        if (!mqttClient.connected()) {
          connect();
        }
        IsDoorOpen();

      }else{   
        Serial.println("ping not ok reset"); 
        //reset because we have lost wifi connection
        ESP.reset();
      }      
    }  
  }
}
