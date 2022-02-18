import os
import boto3
import base64, json, requests

"""

Credentials_role_alias "my-role-alias" points to the role "my-role-credentials".

Credentials given by this role inherit it's rights, so in order to access the bucket, we need
to add to "my-role-credentials" this access rights policy:

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
            }
        ]
    }
"""

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

# generated using the boto3 python API
# this alias is a "pointer" to the actual role
credentials_role_alias = "my-role-alias"

# the bucket we're about to read
# the role where credentials_role_alias "points to" needs
# to have correct access rights (**)
bucket_name = "my-test-bucket"

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

s3_client = boto3.resource('s3',
    aws_access_key_id=creds["accessKeyId"],
    aws_secret_access_key=creds["secretAccessKey"],
    aws_session_token=creds['sessionToken'])

b = s3_client.Bucket(bucket_name)
print("listing bucket contents")
for obj in b.objects.all():
    print(obj)
print("bye!")

"""A note about Sagemaker

The "amazon-sagemaker-edge-manager-demo" uses this kind of data structure:

::

    sagemaker_edge_config = {
        "sagemaker_edge_core_device_name": "device_name",
        "sagemaker_edge_core_device_fleet_name": "device_fleet_name",
        "sagemaker_edge_core_capture_data_buffer_size": 30,
        "sagemaker_edge_core_capture_data_push_period_seconds": 4,
        "sagemaker_edge_core_folder_prefix": "demo_capture",
        "sagemaker_edge_core_region": "us-west-2",
        "sagemaker_edge_core_root_certs_path": "/agent_demo/certificates",
        "sagemaker_edge_provider_aws_ca_cert_file": "/agent_demo/iot-credentials/AmazonRootCA1.pem",
        "sagemaker_edge_provider_aws_cert_file": "/agent_demo/iot-credentials/device.pem.crt",
        "sagemaker_edge_provider_aws_cert_pk_file": "/agent_demo/iot-credentials/private.pem.key",
        "sagemaker_edge_provider_aws_iot_cred_endpoint": "endpoint",
        "sagemaker_edge_provider_provider": "Aws",
        "sagemaker_edge_provider_s3_bucket_name": bucket,
        "sagemaker_edge_core_capture_data_destination": "Cloud"
    }


Keep eyes on "sagemaker_edge_provider_aws_iot_cred_endpoint"

In our case, the endpoint is 

::

    https://[cred_end_point_server]/role-aliases/[alias]/credentials

I guess sagemaker automatizes the role/role alias/etc. crazy stuff & just
spits out the correct credentials endpoint?

"""
