"""Connecting, subscribing, receiving and sending messages with MQTT client

This version uses the callback version of the API (connectAsync, publishAsync, etc.)

..but we turn & twist that version into asyncio (async/await) code that starts
to look pretty nice.

API reference for the original library:

https://s3.amazonaws.com/aws-iot-device-sdk-python-docs/html/index.html


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
# https://github.com/aws/aws-iot-device-sdk-python
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import time, json, sys
import asyncio

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

class Namespace:
    pass

globals = Namespace() # this hack allows us to access event loop in messageCallback

class AWSIoTMQTTClientAsync(AWSIoTMQTTClient):

    def saveEventLoop(self):
        global globals
        self.event_loop = asyncio.get_event_loop()
        globals.event_loop = self.event_loop

    async def connectAio(self, keepAliveIntervalSecond=3, timeout=None):

        def func(mid, data, event, loop, ns: Namespace):
            """AWSIoTMQTTClient seems to call this ....er from another thread
            so we must use loop.call_soon_threadsafe
            see: https://stackoverflow.com/questions/47673104/asyncio-event-wait-function-does-not-continue-after-event-has-been-stored
            parameters, namespace
            """
            print("connect_cb", mid, data)
            ns.result = "newval"
            # print("setting event")
            loop.call_soon_threadsafe(event.set)
            event.set()
            # print("event set")
        
        event = asyncio.Event()
        ns = Namespace()
        # loop = asyncio.get_event_loop()
        self.connectAsync(
            keepAliveIntervalSecond=keepAliveIntervalSecond,
            ackCallback = lambda mid, data: func(mid, data, event, self.event_loop, ns)
            )
        print("awaiting event")
        await asyncio.wait_for(event.wait(), timeout = timeout)
        print("event awaited")
        # now ns contains results.. could contain exceptions as well..?
        # return ns.result


    async def subscribeAio(self, topic, Qos, messageCallback: callable, timeout = None):

        def func(mid, data, event, loop, ns: Namespace):
            print("subs_cb", mid, data)
            ns.result = "newval"
            loop.call_soon_threadsafe(event.set)
            event.set()
            print("event set")

        event = asyncio.Event()
        ns = Namespace()
        # loop = asyncio.get_event_loop()
        self.subscribeAsync(
            topic,
            Qos,
            ackCallback = lambda mid, data: func(mid, data, event, self.event_loop, ns),
            messageCallback = messageCallback
            )
        await asyncio.wait_for(event.wait(), timeout = timeout)
        return ns.result


    async def publishAio(self, topic, payload, Qos, timeout = None):

        def func(mid, event, loop, ns: Namespace):
            print("pub_cb", mid)
            ns.result = "newval"
            loop.call_soon_threadsafe(event.set)
            event.set()
            print("event set")

        event = asyncio.Event()
        ns = Namespace()
        # loop = asyncio.get_event_loop()
        self.publishAsync(
            topic,
            payload,
            Qos,
            ackCallback = lambda mid: func(mid, event, self.event_loop, ns)
            )
        await asyncio.wait_for(event.wait(), timeout= timeout)
        return ns.result

async def main():

    def messageCallback(client, userdata, message):
        """WARNING: this is called from another thread
        """
        # print("client>", client) # deprecated!
        # print("userdata>", userdata) # deprecated!
        # event_loop = client.event_loop
        # global event_loop # only way to pass information into here!
        # event_loop = asyncio.get_event_loop() # nopes
        # global global_queue
        global globals
        print("messageCallback: event_loop", globals.event_loop)
        print("Received a new message: ")
        print(message.payload)
        print("from topic: ")
        print(message.topic)
        print("--------------\n\n")
        globals.event_loop.call_soon_threadsafe(
            globals.queue.put_nowait,
            message
        )

    port=8883
    clientId="myPubSub"
    topic = "kikkelis/kokkelis"

    # also send messages?
    # send = False
    send = True

    client = AWSIoTMQTTClientAsync(clientId)
    client.configureEndpoint(host, port)
    client.configureCredentials(ca_cert_file, cert_pk_file, cert_file)
    client.configureAutoReconnectBackoffTime(1, 32, 20)
    client.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
    client.configureDrainingFrequency(2)  # Draining: 2 Hz
    client.configureConnectDisconnectTimeout(10)  # 10 sec
    client.configureMQTTOperationTimeout(5)  # 5 sec

    print("main thread event loop:", asyncio.get_event_loop())

    client.saveEventLoop() # saves main thread's event loop to globals.event_loop

    global globals
    globals.queue = asyncio.Queue()

    print("connecting")
    res = await client.connectAio()
    print("connect got", res)
    res = await client.subscribeAio(topic, 1, messageCallback)
    print("subscribe got", res)
    print("waiting 60 secs")
    count = 0
    while True:
        print("still listening to topic", topic)
        await asyncio.sleep(3)
        if send:
            message = {}
            message['message'] = "message from IoT device"
            message['sequence'] = count
            messageJson = json.dumps(message)
            print('publishing topic %s: %s\n' % (topic, messageJson))
            res = await client.publishAio(topic, messageJson, 1)
            print("publish got result", res)

            item = await globals.queue.get()
            print("got from queue", item.payload)

            count += 1

asyncio.get_event_loop().run_until_complete(main())

