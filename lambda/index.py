import json
import boto3
import requests

def handler(event, context):
    response = {
        'Status': 'SUCCESS',
        "Reason": "See the details in CloudWatch Log Stream: " + context.log_stream_name,
        'PhysicalResourceId': context.log_stream_name,
        'StackId': event['StackId'],
        'RequestId': event['RequestId'],
        'LogicalResourceId': event['LogicalResourceId'],
        'Data': {"Message": "Resource creation successful!"},
    }

    client = boto3.client('iam')
    try:
        if event['RequestType'] == 'Create':
            kubectl_role_name = event['ResourceProperties']['KubectlRoleName']
            build_role_arn = event['ResourceProperties']['CodeBuildServiceRoleArn']

            assume = client.get_role(RoleName = kubectl_role_name)
            assume_doc = assume['Role']['AssumeRolePolicyDocument']
            roles = [ { 'Effect': 'Allow', 'Principal': { 'AWS': build_role_arn }, 'Action': 'sts:AssumeRole' } ]

            for statement in assume_doc['Statement']:
                if 'AWS' in statement['Principal']:
                    if statement['Principal']['AWS'].startswith('arn:aws:iam:'):
                        roles.append(statement)

            assume_doc['Statement'] = roles
            update_response = client.update_assume_role_policy(RoleName = kubectl_role_name, PolicyDocument = json.dumps(assume_doc))
    except Exception as e:
        print(e)
        response['Status'] = 'FAILED'
        response["Reason"] = e
        response['Data'] = {"Message": "Resource creation failed"}

    response_body = json.dumps(response)
    headers = {'content-type': '', "content-length": str(len(response_body)) }
    put_response = requests.put(event['ResponseURL'], headers=headers, data=response_body)
    return response