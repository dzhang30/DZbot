from flask import Flask, request

from src.dzbot.utils import create_outbound_msg
from src.pager_duty.pd import monitor_primary_secondary

try:
    from src.hipchat import send_room_notification, get_capabilities_descriptor
except ImportError:
    from src.hipchat.hipchat import send_room_notification, get_capabilities_descriptor

app = Flask(__name__)


@app.route('/', methods=['POST'])
def app_dzbot():
    """
    the route/url that receives the http request from the webhook

    :return: a string representation of send_room_notification() if a POST request is received, else 'no request yet'
    """
    inbound_request = request.json['item']
    outbound_msg = create_outbound_msg(inbound_request)

    return str(send_room_notification(inbound_request['room']['name'], outbound_msg, 'purple'))


@app.route('/capability-descriptor', methods=['GET'])
def capability_descriptor():
    """
    the route/url that receives the http GET request from a hipchat room Admin requesting to integrate DZbot into their
    chat room

    :return: the capabilities descriptor containing details of how
    """
    last_slash_index = request.base_url.rfind('/')
    webhook_url = request.base_url[0:last_slash_index]

    cd = get_capabilities_descriptor(webhook_url)
    if cd.status.success:
        return cd.entity

    return cd.status.to_json()


@app.route('/monitor-pager-duty')
def monitor_pager_duty():
    """
    this is the route that the cron job calls for checking whether each team/escalation policy has a primary and
    secondary set in pager duty

    :return: Status object
    """
    return monitor_primary_secondary()
