import logging
import re
from pprint import pformat

from src.dzbot.cli import check_stdout_stderr, parse_args
from src.pager_duty.pd import send_incident, list_all_entities, list_specific_entity, ensure_oncalls, override_schedule

logging.getLogger('werkzeug').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def create_outbound_msg(inbound_request):
    """
    Create the correct outbound message by comparing the /dzbot command from hipchat with our command line program

    :param inbound_request: the inbound request sent from hipchat
    :return: the outbound message that is sent back to hipchat
    """
    message_list = _strip_dzbot(inbound_request['message']['message']).split()
    stdout, stderr = check_stdout_stderr(message_list)

    if not message_list:
        return 'can\'t leave message blank, please enter a command'
    elif stdout or stderr:
        return stdout.replace('cli.py', '/dzbot') if stdout else stderr.replace('cli.py', '/dzbot')

    action = message_list[0]
    args = parse_args(message_list)
    if action == 'override':
        return pd_override(args)
    elif action == 'list' and args.name:
        return pd_list_entity(args)
    elif action == 'list' and not args.name:
        return pd_list_all_entities(args)
    elif action == 'ensure-oncalls':
        return pd_ensure_oncalls()
    elif action == 'notify':
        sender_name = inbound_request['message']['from']['name']
        return pd_send_incident(sender_name, args)

    return 'incorrect action: {}'.format(action)


def pd_override(args):
    """
    Override a pager duty schedule

    :param args: arguments from /dzbot hipchat input
    :return: message on if schedule override was successful
    """
    schedule_name = ' '.join(args.schedule)
    user_name = ' '.join(args.user)
    return format_return(override_schedule(schedule_name, user_name, args.start, args.end).content)


def pd_list_all_entities(args):
    """
    List all entities by specified type

    :param args: arguments from /dzbot hipchat input
    :return: list containing each entity name
    """
    entity_type = 'escalation_policies' if args.entity == 'eps' else args.entity
    vo_resp = list_all_entities(entity_type)
    return format_return(vo_resp.entities) if vo_resp.status.success else format_return(vo_resp.status.content)


def pd_list_entity(args):
    """
    List a specific entity

    :param args: arguments from /dzbot hipchat input
    :return: info on specified entity
    """
    entity_type = 'escalation_policies' if args.entity == 'eps' else args.entity
    vo_resp = list_specific_entity(entity_type, ' '.join(args.name))
    return format_return(vo_resp.entity) if vo_resp.status.success else format_return(vo_resp.status.content)


def pd_ensure_oncalls():
    """
    Ensure there is a primary and secondary oncall for each escalation policy

    :return: list of escalation policies that don't meet the above requirement
    """
    vo_resp = ensure_oncalls()
    return format_return(vo_resp.entities) if vo_resp.status.success else format_return(vo_resp.status.content)


def pd_send_incident(sender_name, args):
    """
    Send a pager duty incident to a pd user or escalation policy

    :param sender_name: sender's name (your name)
    :param args: arguments from /dzbot hipchat input
    :return: message on if incident was successfully sent
    """
    entity_type = 'escalation_policies' if args.entity == 'eps' else args.entity
    entity_name = ' '.join(args.name)
    service_name = ' '.join(args.service)
    title = ' '.join(args.title)
    message = ' '.join(args.message)
    return format_return(send_incident(entity_type, sender_name, entity_name, service_name, title, message).content)


def _strip_dzbot(message):
    """
    strip '/dzbot' from inbound message

    :param message: the inbound message from hipchat
    :return: the inbound message without the '/dzbot' prefix
    """
    return re.split('^/dzbot ', message)[1]


def format_return(result):
    if isinstance(result, bytes):
        return result.decode('utf-8')
    if isinstance(result, dict):
        return str(result).replace('{', '').replace('}', '')
    if not isinstance(result, str):
        return pformat(result, width=120)

    return result
