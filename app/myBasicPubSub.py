"""Connecting, subscribing, receiving and sending messages with MQTT client

- client id is "MyPubSub"
- topic is "kikkelis/kokkelis"

In order for this to work, you need to set correct permissions, so head to

``AWS IoT => Secure => Policies``

And append your thing's policies as follows:

::

    {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "iot:Publish",
                "iot:Receive",
                "iot:RetainPublish"
            ],
            "Resource": [
                ...
                "arn:aws:iot:us-west-2:263211xxxxxx:topic/kikkelis/kokkelis"
            ]
        },
        {
            "Effect": "Allow",
            "Action": "iot:Subscribe",
            "Resource": [
                ...
                "arn:aws:iot:us-west-2:263211xxxxxx:topicfilter/kikkelis/kokkelis"
            ]
        },
        {
            "Effect": "Allow",
            "Action": "iot:Connect",
            "Resource": [
                ...
                "arn:aws:iot:us-west-2:263211xxxxxx:client/myPubSub"
            ]
        }
    ]
    }


Send some messages from the ``test_publish_mqtt.py`` notebook and see if you can receive them here

"""
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import time, json

# certificates for this IoT "thing"
# created aw AWS IoT console
cert_file ="/app/cert/thing1.cert.pem"
ca_cert_file ="/app/cert/root-CA.crt"
cert_pk_file="/app/cert/thing1.private.key"

"""AWS IoT data endpoint for messaging

Can be obtained like this:

::

    iot_client = boto3.client('iot')
    response = iot_client.describe_endpoint(
        endpointType='iot:Data-ATS'
    )
    print(response["endpointAddress"])
    end_point_adr = response["endpointAddress"]

"""
host = "a20qyadf9v1i2e-ats.iot.us-west-2.amazonaws.com"

port=8883
clientId="myPubSub"
topic = "kikkelis/kokkelis"

def customCallback(client, userdata, message):
    print("Received a new message: ")
    print(message.payload)
    print("from topic: ")
    print(message.topic)
    print("--------------\n\n")

client = AWSIoTMQTTClient(clientId)
client.configureEndpoint(host, port)
client.configureCredentials(ca_cert_file, cert_pk_file, cert_file)

client.configureAutoReconnectBackoffTime(1, 32, 20)
client.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
client.configureDrainingFrequency(2)  # Draining: 2 Hz
client.configureConnectDisconnectTimeout(10)  # 10 sec
client.configureMQTTOperationTimeout(5)  # 5 sec

print("connect")
client.connect()
print("subscribe")
client.subscribe(topic, 1, customCallback)
print("starting")
count = 0

# also send messages from here
send = False
# send = True

while True:
    try:
        print("still listening to topic", topic)
        time.sleep(3)
        if send:
            message = {}
            message['message'] = "message from IoT device"
            message['sequence'] = count
            messageJson = json.dumps(message)
            client.publish(topic, messageJson, 1)
            print('Published topic %s: %s\n' % (topic, messageJson))
            count += 1
    except KeyboardInterrupt:
        print("you pressed CTRL-C: will exit")
        break
