"""deploy lambda function this with the name "mqttMessageFormatter"

PART 1: Lambda bucket rights
----------------------------

Since this lamda writes to a bucket, it needs the correct rights.  Go to your lambda function => permissions => role name
=> add a policy:

::

    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:ListBucket"
                ],
                "Resource": "arn:aws:s3:::my-test-bucket"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject"
                ],
                "Resource": "arn:aws:s3:::my-test-bucket/*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "s3:PutObject"
                ],
                "Resource": "arn:aws:s3:::my-test-bucket/*"
            }
        ]
    }


PART 2 : MQTT Message to bucket
-------------------------------

MQTT message comes with topic "kikkelis/kokkelis" and with payload  {"message" : str, "count" : int}

Attach the following trigger to this lambda function (in your lambda function => triggers menu)

::

    SELECT * FROM 'kikkelis/kokkelis' 

It just forwards the payload as-is to this lambda function

ref: https://docs.aws.amazon.com/iot/latest/developerguide/iot-sql-reference.html?icmpid=docs_iot_console

"""

import boto3, json

def lambda_handler(event, context):
    bucket_name = "my-test-bucket"

    try:
        msg = event["message"]
        n = event["count"]    

        s3_client = boto3.resource('s3')
        b = s3_client.Bucket(bucket_name)

        # create a file into the bucket
        b.put_object(
            Body=msg.encode("utf-8"),
            # Bucket=bucket_name,
            Key="messagefile_"+str(n)+".txt"
        )
    except Exception as e:
        return {
        'statusCode': 405,
        'body': json.dumps({
            "event" : event,
            "exception" : str(e)})
        }
    else:
        return {
            'statusCode': 200,
            'body': json.dumps('All good!')
        }


def main():
    from pprint import pprint
    event = {}
    event["message"] = "a test"
    event["count"] = 9999
    ret=lambda_handler(event, None)
    pprint(ret)

if __name__ == "__main__":
    main()
