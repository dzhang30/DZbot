import os
import json

import requests

from src.value_objects.entities_resp import EntitiesResp
from src.value_objects.entity_resp import EntityResp
from src.value_objects.status import Status

try:
    api_host = os.environ['hipchat_api_host']
    hipchat_api_token = os.environ['hipchat_api_token']
except KeyError:
    api_host = 'this api host value does not exist'
    hipchat_api_token = 'this api token value does not exist'

headers = {
    'Authorization': 'Bearer {0}'.format(hipchat_api_token),
    'content-type': 'application/json',
}


def get_capabilities_descriptor(webhook_url):
    """
    get the hipchat add-on capabilities descriptor. This descriptor is used to to allow admins to integrate DZbot
    with their chat rooms

    :return: the capabilities descriptor
    """
    with open('src/hipchat/capability_descriptor.json') as cd:
        capabilities_json = json.loads(cd.read())
        capabilities_json['capabilities']['webhook'][0]['url'] = webhook_url

    if capabilities_json:
        return EntityResp(Status(True, 'capability descriptor read successfully'), json.dumps(capabilities_json))

    return EntityResp(Status(False, 'could not read capability descriptor'))


def send_room_notification(room_id_or_name, message, color, message_format='text'):
    """
    sends room notification

    :param room_id_or_name: id or name of hipchat room
    :param message: message you want to send
    :param color: background color of the message
    :param message_format: can be 'html' or 'text', default is 'text' here
    :return: response from the http post request
    """
    send_notification_url = api_host + '/room/{}/notification'.format(room_id_or_name)
    body = {
        'message': message,
        "color": color,
        "message_format": message_format
    }

    response = requests.post(url=send_notification_url, headers=headers, json=body)

    return _response_helper(response)


def create_web_hook(room_id_or_name, regex_pattern, send_url, event):
    """
    create a webhook in hipchat room

    :param room_id_or_name: id or name of hipchat room
    :param regex_pattern: regex pattern that the webhook listens for
    :param send_url: the URL to send the webhook post to
    :param event: the type of event this webhook will listen for
        (i.e. room_message, room_notification, room_enter, etc)
    :return: response from the http post request
    """
    web_hook_url = api_host + '/room/{0}/webhook'.format(room_id_or_name)
    body = {'url': send_url, 'pattern': regex_pattern, 'event': event}

    response = requests.post(url=web_hook_url, headers=headers, json=body)

    return _response_helper(response)


def _get_all_rooms(max_results=1000):
    """
    get all hipchat rooms

    :param max_results: max number of rooms to return
    :return: response from the http get request
    """
    params = {'max-results': max_results}
    rooms_url = api_host + '/room'

    response = requests.get(url=rooms_url, headers=headers, params=params)

    return _get_entities_helper(response)


def _get_all_room_webhooks(rood_id_or_name, max_results=1000):
    """
    get all webhooks in specified hipchat room

    :param rood_id_or_name: id or name of hipchat room
    :param max_results: max number of webhooks to return
    :return: response from the http get request
    """
    params = {'max-results': max_results}
    get_all_webhooks_url = api_host + '/room/{0}/webhook'.format(rood_id_or_name)

    response = requests.get(url=get_all_webhooks_url, headers=headers, params=params)

    return _get_entities_helper(response)


def _del_room_webhook(room_id_or_name, webhook_id):
    """
    delete a webhook located in a specified hipchat room

    :param room_id_or_name: id or name of hipchat room
    :param webhook_id: id of webhook you want to remove
    :return: response from the http delete request
    """
    delete_url = api_host + '/room/{0}/webhook/{1}'.format(room_id_or_name, webhook_id)

    response = requests.delete(url=delete_url, headers=headers)

    return _response_helper(response)


def _response_helper(response):
    """
    helper method to return the status of a http request

    :param response: the response from an http request
    :return: a Status describing the response
    """
    if response.ok:
        return Status(True, 'request was successful')

    return Status(False, response.json())


def _get_entities_helper(response):
    """
    helper method to return a list of requested entities

    :param response: the response from an http request
    :return: an EntitiesResponse describing the response
    """
    if response.ok:
        status = Status(True, 'successfully retreived entities')
        try:
            return EntitiesResp(status, response.json())
        except json.JSONDecodeError:
            return EntitiesResp(status, response)

    return EntitiesResp(Status(False, response.json()))
