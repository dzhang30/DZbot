import collections
import os

import requests

from src.value_objects.entities_resp import EntitiesResp
from src.value_objects.entity_resp import EntityResp
from src.value_objects.status import Status

try:
    api_host = os.environ['pd_api_host']
    api_key = os.environ['pd_api_key']
except KeyError:
    api_host = 'this api host value does not exist'
    api_key = 'this api key value does not exist'

headers = {
    'Authorization': 'Token token={}'.format(api_key),
    'Accept': 'application/vnd.pagerduty+json;version=2',
}


def send_incident(entity_type, sender_name, entity_name, service_name, title, message):
    """
    send a pager duty incident to either a user or escalation policy

    :param entity_type: the type (either 'users' or 'escalation_policies') of entity you want to send this incident to
    :param sender_name: name of sender (your name)
    :param entity_name: name of the entity (user or ep) you want to notify
    :param service_name: name of the impacted pager duty service
    :param title: title of incident
    :param message: body of message
    :return: a Status obj that contains whether the incident was sent successfully or not
    """
    email = get_user_login_email(sender_name)
    entity = search_entity(entity_name, entity_type)
    service = search_entity(service_name, 'services')
    search_results = send_and_override_helper(entity_type, entity, service)

    if not email.status.success:
        return Status(False, email.status.content)
    if not search_results.success:
        return Status(False, search_results.content)

    incident = get_incident_body(entity_type, entity, service, title, message)

    headers['FROM'] = email.entity
    send_incident_url = api_host + '/incidents'
    response = requests.post(url=send_incident_url, headers=headers, json=incident)

    if response.ok:
        return Status(True, 'successfully sent {0} incident to {1}'.format(entity_type, entity_name))
    return Status(False, response.content)


def get_user_login_email(name):
    """
    extract the user login email

    :param name: user name
    :return: email address of user
    """
    users = get_all_entities_resp('users', name)
    if not users.status.success:
        return EntityResp(Status(False, users.status.content))

    found_email = [user['email'] for user in users.entities['users'] if user['name'] == name]
    if not found_email:
        return EntityResp(Status(False, 'Could not find pagerduty login email for {}, please make sure your hipchat '
                                        'account name is the same as your pagerduty account name'.format(name)))

    return EntityResp(Status(True, 'found pagerduty login email for {}'.format(name)), found_email[0])


def get_incident_body(entity_type, entity, service, title, message):
    """
    get a dictionary representation of the incident format

    :param entity_type: the type (either 'users' or 'escalation_policies') of entity you want to send this incident to
    :param entity: the entity (user or ep) you want to notify
    :param service: the impacted pager duty service
    :param title: title of incident
    :param message: body of message
    :return: a dictionary representation of the incident format
    """
    if entity_type == 'users':
        return {
            'incident': {
                'type': 'incident',
                'title': title,
                'body': {
                    'type': 'incident_body',
                    'details': message
                },
                'service': {
                    'id': service.entity['id'],
                    'type': service.entity['type'],
                },
                'assignments': [{
                    'assignee': {
                        'id': entity.entity['id'],
                        'type': 'user'
                    }
                }]
            }
        }
    elif entity_type == 'escalation_policies':
        return {
            'incident': {
                'type': 'incident',
                'title': title,
                'body': {
                    'type': 'incident_body',
                    'details': message
                },
                'service': {
                    'id': service.entity['id'],
                    'type': service.entity['type'],
                },
                'escalation_policy': {
                    'id': entity.entity['id'],
                    'type': 'escalation_policy_reference'
                }
            }
        }
    return None


def override_schedule(schedule_name, user_name, start, end):
    """
    override the current schedule for the specified user with start and end times

    :param schedule_name: schedule name
    :param user_name: user name
    :param start: start time for override
    :param end: end time for override
    :return: a Status obj that contains whether the override was successful or not
    """
    user = search_entity(user_name, 'users')
    schedule = search_entity(schedule_name, 'schedules')

    search_results = send_and_override_helper('users', user, schedule)
    if not search_results.success:
        return Status(False, search_results.content)

    override = {
        'override': {
            'start': start,
            'end': end,
            'user': {
                'id': user.entity['id'],
                'type': 'user_reference'
            }
        }
    }

    override_schedule_url = api_host + '/schedules/{}/overrides'.format(schedule.entity['id'])
    response = requests.post(override_schedule_url, headers=headers, json=override)

    if response.ok:
        return Status(True, 'successfully created the override for {} between {} - {}'.
                      format(user.entity['name'], start, end))
    return Status(False, response.content)


def send_and_override_helper(entity_type, entity, service_or_schedule):
    if not entity.status.success:
        return Status(False, '{0} name error: {1}'.format(entity_type, entity.status.content))
    if not service_or_schedule.status.success:
        return Status(False, 'service/sched name error: {0}'.format(service_or_schedule.status.content))
    if not _check_id(entity.entity) or not _check_id(service_or_schedule.entity):
        return Status(False, 'the id field for {} or service/schedule is missing'.format(entity_type))

    return Status(True, 'both the entity and service/schedule have been found')


def monitor_primary_secondary():
    """
    monitor and notify each team/escalation policy whether it has a primary and secondary oncall set in pager duty

    :return: Status object
    """
    monitored_eps = {
        'Amp',
        'Data Engineering',
        'DataScience',
        'Ingestion',
        'Operations',
        'OpsDirect',
        'ops-delayed',
        'Radioedit',
        'Radioedit-delayed',
        'Web Escalation',
        'Test'
    }

    eps_without_primary_secondary = ensure_oncalls()

    if not eps_without_primary_secondary.status.success:
        return Status(False, eps_without_primary_secondary.status.content)

    for ep in eps_without_primary_secondary.entities:
        ep_name = ep.split(':')[0]
        if ep_name in monitored_eps:
            send_response = Status(True, 'No-Op')

            if not send_response.success:
                return Status(False, send_response.content)

    return Status(True, 'Monitored successfully')


def ensure_oncalls():
    """
    ensure that each escalation policy has an oncall level 1 and oncall level 2 user. It also checks if the oncall
    level 1 & 2 users are not the same

    :return: an EntitiesResp that contains a Status and a list of all of the escalation policies that are missing either
    an oncall level 1 or 2 user. It also lets you know if the same user is assigned to both level 1 & 2 of an
    escalation policy
    """
    all_eps_resp = list_all_entities('escalation_policies')

    if not all_eps_resp.status.success:
        return EntitiesResp(Status(False, all_eps_resp.status.content))

    result = []
    for ep_name in all_eps_resp.entities:
        ep_response = list_oncalls_by_ep(ep_name)
        if not ep_response.status.success:
            return EntitiesResp(Status(False, ep_response.status.content))

        ep_oncalls = ep_response.entities['oncalls']
        existing_escalation_levels = [ep['escalation_level'] for ep in ep_oncalls]
        if 1 not in existing_escalation_levels:
            result.append('{}: oncall level 1 does not exist'.format(ep_name))
        elif 2 not in existing_escalation_levels:
            result.append('{}: oncall level 2 does not exist'.format(ep_name))

    return EntitiesResp(Status(True, 'successfully ensured all primary & secondary'), result)


def search_entity(name, entity_type):
    """
    search for a specific entity in pager duty

    :param name: name of entity
    :param entity_type: type of entity ('users', 'escalation_policies', 'services', 'oncalls', 'schedules')
    :return: an EntityResp containing a Status and the searched entity if found, else None
    """
    entities_response = get_all_entities_resp(entity_type, name)

    if not entities_response.status.success:
        return EntityResp(Status(False, entities_response.status.content))

    entities = entities_response.entities[entity_type]
    for entity in entities:
        if entity['name'].lower() == name.lower():
            return EntityResp(Status(True, 'successfully found {}: {}'.format(entity_type, name)), entity)

    return EntityResp(Status(False, 'could not find entity name: \'{0}\' of type \'{1}\''.format(name, entity_type)))


def list_all_entities(entity_type):
    """
    list all entity names in pager duty by the specified type

    :param entity_type: type of entity you want to list ('users', 'escalation_policies', 'services',
     'oncalls', 'schedules')
    :return: EntitiesResp object containing a Status and a list of entity names
    """
    entities_response = get_all_entities_resp(entity_type)
    if not entities_response.status.success:
        return EntitiesResp(Status(False, entities_response.entities))

    entities = entities_response.entities[entity_type]
    if entity_type == 'oncalls':
        return EntitiesResp(entities_response.status, {entity['user']['summary'] for entity in entities})
    else:
        return EntitiesResp(entities_response.status, [entity['name'] for entity in entities])


def list_specific_entity(entity_type, name):
    """
    list info for a specific entity (i.e. an oncall user or an escalation policy

    :param entity_type: type of the entity you want to list
    :param name: name of the entity you want to list
    :return: an EntityResp containing a Status and the info for the specified entity
    """
    if entity_type == 'oncalls':
        vo_resp = list_contact_methods(name)
    elif entity_type == 'escalation_policies':
        vo_resp = list_ep_by_level(name)
        vo_resp.entity = ordered_dict_to_string(vo_resp.entity)
    else:
        return EntityResp(Status(False, '{} is an incorrect entity type'.format(entity_type)))

    if not vo_resp.status.success:
        return EntityResp(Status(False, vo_resp.status.content))

    result = vo_resp.entity if isinstance(vo_resp, EntityResp) else vo_resp.entities
    return EntityResp(Status(True, 'Successfully retrieved {} {}'.format(entity_type, name)), result)


def list_ep_by_level(ep_name):
    """
    list an escalation policy in order by its escalation levels and corresponding oncall users

    1: ['Test User 1, email: testuser1@iheartradio.com, phone: 1112223333']
    2: ['Test User 2, email: testuser2@iheartradio.com, phone: 2223334444']
    3: ['Test User 3, email: testuser3@iheartradio.com, phone: 3334445555']

    :param ep_name: name of escalation policy
    :return: an EntitiesResp containing a Status and a sorted/ordered dictionary of the ep's escalation level and its
    corresponding oncall users
    """
    oncalls_response = list_oncalls_by_ep(ep_name)
    if not oncalls_response.status:
        return EntityResp(Status(False, oncalls_response.status.content))

    ep = {}
    for oncall in oncalls_response.entities['oncalls']:
        esc_level = oncall['escalation_level']
        user_name = oncall['user']['summary']

        cm_response = list_contact_methods(user_name)
        if not cm_response.status:
            return EntityResp(Status(False, cm_response.status.content))

        user_info = user_name + ', ' + contact_methods_to_string(cm_response.entities)
        if esc_level not in ep:
            ep[esc_level] = [user_info]
        else:
            ep[esc_level].append(user_info)

    status = Status(True, 'got ep by level') if len(ep) > 0 else Status(False, '{} is not an ep'.format(ep_name))
    return EntityResp(status, sort_ep(ep))


def list_oncalls_by_ep(ep_name):
    """
    helper method that gets all of the oncall users by the specified escalation policy

    :param ep_name:
    :return: an EntitiesResp containing a Status and a list of oncall users by escalation policy
    """
    ep = search_entity(ep_name, 'escalation_policies')
    if not ep.status.success:
        return EntitiesResp(Status(False, '{} is not a valid escalation policy'.format(ep_name)))

    entity_url = api_host + get_entities_endpoints()['oncalls']
    response = requests.get(url=entity_url, headers=headers, params={'escalation_policy_ids[]': [ep.entity['id']]})
    return _get_entities_resp_helper('oncalls', response)


def list_contact_methods(name):
    """
    get the contact methods of a user

    :param name: name of user
    :return: an EntityResp containing a Status and a 'cleaned' list of dictionaries specifying all of the
    user's contact methods
    """
    user = search_entity(name, 'users')

    if not user.status.success:
        return EntitiesResp(Status(False, user.status.content))

    cm_response = get_user_contact_methods(user.entity['id'])
    if not cm_response.status.success:
        return EntitiesResp(Status(False, cm_response.status.content))

    cms = cm_response.entities['contact_methods']
    return EntitiesResp(Status(True, 'successfully got {}\'s contact methods'.format(name)), clean_contact_method(cms))


def get_user_contact_methods(user_id):
    """
    get all contact_methods of a pager duty user

    :param user_id: id of the user you want contact methods from
    :return: EntitiesResp object containing a list of all of the user's contact methods and a Status object
    """
    if not user_id:
        return EntitiesResp(Status(False, 'must specify a user_id in order to get user\'s contact methods'))

    contact_methods_url = api_host + '/users/{}/contact_methods'.format(user_id)
    response = requests.get(url=contact_methods_url, headers=headers, params={'limit': 100})

    return _get_entities_resp_helper('contact methods', response)


def get_all_entities_resp(entity_type, name=None):
    """
    retrieve a list of all entities by type

    :param entity_type: entity type (users, escalation_policies, services, schedules, oncalls, contact_methods)
    :param name: name of specific entity (this does not work for oncall entities)
    :return: EntitiesResp object containing a Status and a list of entities
    """
    entities_endpoints = get_entities_endpoints()

    if entity_type not in entities_endpoints:
        return EntitiesResp(Status(False, 'incorrect \'type\' parameter: {}'.format(entity_type)))

    entity_url = api_host + entities_endpoints[entity_type]
    response = requests.get(url=entity_url, headers=headers, params={'limit': 100, 'query': name})
    return _get_entities_resp_helper(entity_type, response)


def _get_entities_resp_helper(entity_type, entities_response):
    """
    helper method that helps convert http response into the correct EntitiesResp object

    :param entity_type: the type of entities (e.g. users/escalation_policies/oncalls/contact_methods etc.)
    :param entities_response: the response from request.get for users/escalation_policies/oncalls/services/
    contact_methods etc.
    :return: EntitiesResp object containing a Status and a list of entities
    """
    if entities_response.ok:
        try:
            return EntitiesResp(Status(True, 'successfully got all {}'.format(entity_type)), entities_response.json())
        except Exception as e:
            return EntitiesResp(Status(False, 'error: {0}\ncould not retrieve all {1}\nresponse: {2}'.
                                       format(e, entity_type, entities_response.ktext)))

    return EntitiesResp(Status(False, 'could not retrieve all {}'.format(entity_type)), entities_response.json())


def clean_contact_method(contact_methods):
    """
    helper method that cleans the returned contact methods in list_contact_methods(name)

    :param contact_methods: contact methods from list_contact_methods(name)
    """
    result_contact_methods = {}
    for contact_method in contact_methods:
        if contact_method['type'] == 'phone_contact_method':
            if 'phone' not in result_contact_methods:
                result_contact_methods['phone'] = [contact_method['address']]
            else:
                result_contact_methods['phone'].append(contact_method['address'])
        elif contact_method['type'] == 'email_contact_method':
            if 'email' not in result_contact_methods:
                result_contact_methods['email'] = [contact_method['address']]
            else:
                result_contact_methods['email'].append(contact_method['address'])

    return result_contact_methods


def contact_methods_to_string(contact_methods):
    """
    convert contact methods dictionary to a string

    :param contact_methods: dict of contact methods
    :return: string format of dict
    """
    result = ''
    for contact_type, address in contact_methods.items():
        address_string = ' & '.join(address)
        result = result + '{0}: {1}, '.format(contact_type, address_string)

    result = result[:-2]

    return result


def get_entities_endpoints():
    """
    get a dictionary of entity type to entity endpoint

    :return: dictionary containing a mapping of pd entity types to their associated endpoints
    """
    return {
        'users': '/users',
        'escalation_policies': '/escalation_policies',
        'oncalls': '/oncalls',
        'services': '/services',
        'schedules': '/schedules'
    }


def sort_ep(ep):
    """
    helper method that sorts the dictionary in list_ep_by_level(name)

    :param ep: the escalation policy dictionary with 'key: escalation level' and 'value: [user_info]'
    :return: an Ordered Dictionary of the escalation policy ordered by its escalation levels
    """
    return collections.OrderedDict(sorted(ep.items(), key=lambda x: x[0]))


def ordered_dict_to_string(ordered_dict):
    """
    helper method that converts an Ordered Dictionary to a string

    :param ordered_dict: the Ordered Dictionary
    :return: a string representation of the escalation policy ordered by its escalation levels
    """
    result = []
    for escalation_level, user_info in ordered_dict.items():
        result.append('{0}: {1}'.format(escalation_level, str(user_info)))

    return '\n'.join(result)


def _check_id(entity):
    return 'id' in entity
