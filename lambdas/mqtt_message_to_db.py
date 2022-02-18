"""deploy this with the name "mqttMessageFormatter2"

You need a dynamodb named ``my-test-db`` with

::

    primary key prim : str
    sort key sortie : str

PART 1 : Lambda db access rights
--------------------------------

::

    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "dynamodb:BatchGetItem",
                    "dynamodb:GetItem",
                    "dynamodb:Query",
                    "dynamodb:Scan",
                    "dynamodb:BatchWriteItem",
                    "dynamodb:PutItem",
                    "dynamodb:UpdateItem"
                ],
                "Resource": "arn:aws:dynamodb:us-west-2:263211xxxxxx:table/my-test-db"
            }
        ]
    }
"""

import boto3, json

def lambda_handler(event, context):
    db_name = "my-test-db"

    try:
        msg = event["message"]
        n = event["count"]    

        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(db_name)

        # write to the db        
        response = table.put_item(
        Item = { 
            'prim': str(n),
            'sortie': str(n),
            'msg' : msg
            }
        )
        print(response)

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

