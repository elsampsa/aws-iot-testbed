"""Lambda function is something that you can call from wherever (backend, API gateway, IoT device) and it get's executed in the cloud
define lambda function in

::

    https://us-west-2.console.aws.amazon.com/lambda/home?region=us-west-2#/functions
    
give it the name "myFirstLambda"

You still remember the role ``my-role-credentials`` we created in the notebook ``token_generation_test.ipynb`` ?

That is the role we assume for this IoT device, so we have to grant it the rights to execute lambda functions.  Add this policy 
to ``my-role-credentials``:


::

    {
        "Version": "2012-10-17",
        "Id": "default",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": "lambda:InvokeFunction",
                "Resource": "arn:aws:lambda:us-west-2:263211xxxxxx:function:myFirstLambda"
            }
        ]
    }


"""
import json, requests
from pprint import pprint
import boto3 

# certificates for this IoT "thing"
# created aw AWS IoT console
cert_file ="/app/cert/thing1.cert.pem"
ca_cert_file ="/app/cert/root-CA.crt"
cert_pk_file="/app/cert/thing1.private.key"

# name of the thing (as in AWS IoT console)
# created at AWS IoT console:
your_thing_name="thing1" 

# doesn't change? let's hope so!
# queried using the boto3 python API:
cred_endpoint_server="c3dkxgjiybi9gp.credentials.iot.us-west-2.amazonaws.com" 
region = "us-west-2"

# generated using the boto3 python API
# this alias is a "pointer" to the actual role
credentials_role_alias = "my-role-alias"

cred_endpoint="https://"+cred_endpoint_server+"/role-aliases/"\
    +credentials_role_alias+"/credentials"
print(cred_endpoint)
resp = requests.get(
    cred_endpoint,
    cert=(cert_file, cert_pk_file, ca_cert_file),
    headers={
        "x-amzn-iot-thingname":your_thing_name
    }
)

creds = json.loads(resp.content)["credentials"]
pprint(creds)

lambda_client = boto3.client('lambda',
    region_name = region,
    aws_access_key_id=creds["accessKeyId"],
    aws_secret_access_key=creds["secretAccessKey"],
    aws_session_token=creds['sessionToken'])

response = lambda_client.invoke(
    FunctionName='myFirstLambda',
    InvocationType='RequestResponse'
)
print(response["Payload"].read())
