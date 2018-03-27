from pprint import pformat
from unittest.mock import patch

from src.dzbot import utils
from src.value_objects.entities_resp import EntitiesResp
from src.value_objects.status import Status


@patch('src.dzbot.utils.list_all_entities')
def test_create_outbound_msg(mock_list_all_entities):
    mock_list_all_entities.return_value = EntitiesResp(Status(True, 'success'), ['Test oncall 1', 'Test oncall 2'])
    mock_inbound_request = {
        'message': {
            'message': '/dzbot list --entity oncalls'
        }
    }
    assert utils.create_outbound_msg(mock_inbound_request) == pformat(['Test oncall 1', 'Test oncall 2'], width=100)


def test_strip_dzbot():
    assert utils._strip_dzbot('/dzbot list oncall: test user') == 'list oncall: test user'
    assert utils._strip_dzbot('/dzbot open the pod bay doors, hal') == 'open the pod bay doors, hal'
