import boto3
import json
import os
from boto3.dynamodb.conditions import And, Attr, Key
from uuid import uuid4
from datetime import datetime
from pytz import timezone


contact_list = boto3.resource('dynamodb').Table('contact_list')

def _get_username(event):
    return event['requestContext']['authorizer']['claims']['cognito:username']


def _find(username, **kwargs):
    query_params = {
        'IndexName': 'username-index',
        'KeyConditionExpression': Key('username').eq(username),
    }
    if kwargs:
        filter_condition_expressions = [ Attr(key).eq(value) for key, value in kwargs.items() ]
        if len(filter_condition_expressions) > 1:
            query_params['FilterExpression'] = And(*filter_condition_expressions)
        elif len(filter_condition_expressions) == 1:
            query_params['FilterExpression'] = filter_condition_expressions[0]
    
    data = contact_list.query(**query_params)

    return data['Items']


def _response(contact_lists):
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(contact_lists)
    }


def _get(request, username):
    contact_lists = _find(
        username=username
    )

    return _response(contact_lists)


def _create(request, username):
    contact_list.put_item(Item={
        'id': 'CL' + str(uuid4().int)[0:16],
        'list_name': request['list_name'],
        'username': username, 
        'created_at': datetime.now(tz=timezone('America/Denver')).isoformat(),
        'updated_at': datetime.now(tz=timezone('America/Denver')).isoformat(),
    })
        
    return _get(request, username) 


def handle(event, context):
    operation = event['requestContext']['httpMethod']
    operations = {
        'GET' : _get,
        'POST': _create
    }
    if operation in operations:
        return operations[operation](json.loads(event['body']), _get_username(event))
    else:
        raise ValueError(f'Unable to run operation for HTTP METHOD: {operation}')
    