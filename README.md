# Amazon IoT testbed

## A. Synopsis

You'll be running a "fleet" of AWS IoT "things" from docker containers.

You are the "puppet master" from your local linux box, where you can interact with the things from the comfort of python notebooks.

Some topics covered:

- Publishing and subscribing to MQTT messages
- Sending those messages from a local notebook
- Triggers to write messages to buckets / databases in AWS
- Sending and receiving messages to/from and IoT device (and writing them to buckets / databases)
- Lambda functions

Check out section ``E. Demos`` for more information.

The complicated part is (surprise!) setting all those rights IAMs in AWS.

But do not worry - I will provide complete, step-by-step examples and documentation.

## B. First things first

## 1. Install credentials & boto3

*basics: skip if you need to*

After this, you are able to manage the IoT fleet from the comfort of our linux box.

Go to [identity and access management](https://console.aws.amazon.com/iamv2/home?#/home)

Create ```$HOME/.aws/credentials``` with:
```
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
```

Create ``$HOME/.aws/config`` with:
```
[default]
region=us-east-1
```

Install AWS SDK with:
```
pip3 install --user boto3
```

## 2. Build the docker image

Like this:
```
docker-compose --f docker-compose-dev.yml build thing1
```

## 3. Create an IoT "thing"

Head to [AWS IoT]([here](https://us-west-2.console.aws.amazon.com/iot/home?region=us-west-2#/connectdevice/)) and create your first "thing".  Please name it ``thing1``.

Place the certificates under the directory ``thing1/cert/```

Now your directory structure should look like this:
```
├── docker-compose-dev.yml      # thing1 entry point: /app/dev/run.bash (**)
├── Dockerfile.dev
├── notes.md
├── README.md
├─  notebook/                   # notebooks to command the IoT "fleet"
|   └──
|
├── app                         # docker bind mounted to /app/common
│   └──                         # place your python scripts here
|                               # common to all "things"
|
├── dev                         # docker bind mounted to /app/dev
|   └── run.bash                # example entry point: hot-reloads /app/common/basicPubSub.py (**)
|                               # place entry_point scripts here. Common to all things
|
└── thing1                      # one directory for each of your "things"
    │   
    ├── cert                    # docker bind mounted to /app/cert
    |    ├── root-CA.crt        # place your IoT device credentials here (see below)
    |    ├── thing1.cert.pem
    |    ├── thing1.private.key
    |    └── thing1.public.key
    └─ app                      # place your python scripts here
                                # scripts only for a particular "thing"
```

## 4. Authorize the thing

If your IoT thing wants to use AWS resources (buckets, etc.), you need to
go through a rather complicated authorization procedure.  This is explained 
in the [notebook/](notebook/) ``token_generation_test.ipynb``.

I recommend to go through the step-by-step demos in ``E. Demos``.

## C. Start a thing

*these won't work until you set the rights in part (E)*

Like this:
```
docker-compose --f docker-compose-dev.yml run thing1 python3 /app/common/testBucket.py
```
It will run, inside the docker container, the local file [app/testBucket.py](app/testBucket.py)

This command starts receiving MQTT message:
```
docker-compose --f docker-compose-dev.yml run thing1 python3 /app/common/myBasicPubSub.py
```
before launching it, read and edit [app/myBasicPubSub.py](myBasicPubSub.py)

If you want hot-reloading, do this:
```
docker-compose --f docker-compose-dev.yml run thing1 watchmedo auto-restart -d /app --patterns="*.py;*.crt;*.key;*.pem" --recursive -- python3 /app/common/myBasicPubSub.py
```

There is even a short-hand script for that:
```
./runcommon.bash thing1 myBasicPubSub.py
```

## D. Add more things

- Create more things in the AWS IoT console
- Create new directories (say ``thing2``, ``thing3``, etc.)
- Place the certificates under the corresponding ``cert/`` directories
- Finally, add more entries into your ``docker-compose-dev.yml`` file

## E. Demos

Notebooks at [notebook/](notebook/) will be used.

For code that you run from the notebooks, we assume that you have god-like priviledges in AWS
(pubsub messages, buckets, role admin, etc.).

Before starting, please create an S3 bucket named ``my-test-bucket``.

You need to go there examples in the ascending order.

### 1. Grant AWS access to IoT device

- Notebook: ``token_generation_test``, part 1
- Role ``my-role-credentials`` and it's alias ``my-role-alias`` are created
- Credentials corresponding to ``my-role-alias`` now allow access to AWS services
- However, their rights are quite limited, so several rights have to be manually enabled (++)

### 2. Test bucket operations with IoT device credentials

- Notebook ``token_generation_test``, part 2
- As explained in the notebook, role ``my-role-credentials`` needs access rights to the bucket ``my-test-bucket`` (++)

### 3. Access AWS bucket from an IoT device

- Run ``./runcommon.bash thing1 testBucket.py``
- It executes [app/testBucket.py](app/testBucket.py)

### 4. Notebook MQTT message => AWS => IoT device

- Read the documentation in [app/myBasicPubSub.py](app/myBasicPubSub.py)
- You need to grant rights to ``my-role-credentials`` to pub & sub to messages (++)
- Disable sending messages in [app/myBasicPubSub.py](app/myBasicPubSub.py)
- Run ``./runcommon.bash thing1 myBasicPubSub.py``
- Use notebook ``test_publish_mqtt`` to send messages to AWS => IoT device
- Messages received by the IoT device should appear in the running terminal

### 5. Lambda call => write to bucket

- Read part 1 of the documentation in [lambdas/mqtt_message_to_bucket.py](lambdas/mqtt_message_to_bucket.py)
- Copy-paste the import statement and ``lambda_handler`` to AWS as a new lambda function with the name  ``mqttMessageFormatter``
- Give the lambda function rights to write to our bucket ``my-test-bucket`` (as explained in ``mqtt_message_to_bucket.py``)
- Use notebook ``lambda_test`` part 2 to call the lambda function
- Check that a new file was written to the bucket ``my-test-bucket``

### 6. Notebook MQTT message => AWS => Lambda => write bucket

- Read part 2 of the documentation in [lambdas/mqtt_message_to_bucket.py](lambdas/mqtt_message_to_bucket.py)
- As explained in the documentation, create a trigger that launches the lambda function at a certain MQTT message
- Use notebook ``test_publish_mqtt`` to send messages to AWS
- Check that a new file was written to the bucket ``my-test-bucket``

### 7. IoT device MQTT message => AWS => Lambda => write bucket

- Enable sending messages in [app/myBasicPubSub.py](app/myBasicPubSub.py)
- Run ``./runcommon.bash thing1 myBasicPubSub.py``
- Check that new files appear to the bucket ``my-test-bucket``

### 8. Lambda call => write to database

- Create a DynamoDB with the name ``my-test-db``
- Read part 1 of the documentation in [lambdas/mqtt_message_to_db.py](lambdas/mqtt_message_to_db.py)
- Copy-paste the import statement and ``lambda_handler`` to AWS as a new lambda function with the name ``mqttMessageFormatter2``
- Give the lambda function rights to write to our database ``my-test-db`` (as explained in ``mqtt_message_to_db.py``)
- Use notebook ``lambda_test`` part 3 to call the lambda function
- Check that a new entry was written to the db ``my-test-db``


## References

- [Authorizing IoT devices](https://docs.aws.amazon.com/iot/latest/developerguide/authorizing-direct-aws.html)
- [Assuming roles](https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRole.html)
- [MQTT => rule => lambda](https://docs.aws.amazon.com/iot/latest/developerguide/iot-lambda-rule.html)

## Copyright

(c) Sampsa Riikonen 2022

## License

DO WHAT THE F*** YOU WANT TO PUBLIC LICENSE
