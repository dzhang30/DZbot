import collections
from unittest.mock import patch

from src.pager_duty.pd import send_incident, override_schedule, ensure_oncalls, search_entity, list_specific_entity, \
    list_all_entities, list_ep_by_level, list_contact_methods, get_all_entities_resp, get_user_contact_methods, \
    clean_contact_method, contact_methods_to_string
from src.value_objects.entities_resp import EntitiesResp
from src.value_objects.entity_resp import EntityResp
from src.value_objects.status import Status


@patch('src.pager_duty.pd.requests.post')
@patch('src.pager_duty.pd.search_entity')
@patch('src.pager_duty.pd.search_entity')
@patch('src.pager_duty.pd.get_user_login_email')
def test_send_user_incident(mock_get_user_login_email, mock_user_search_entity, mock_service_search_entity, mock_post):
    mock_get_user_login_email.return_value = EntityResp(Status(True, 'good'), 'testuser@iheart.com')
    mock_user_search_entity.return_value = EntityResp(Status(True, 'good'), entity={'id': 000})
    mock_service_search_entity.return_value = EntityResp(Status(True, 'good'), entity={'id': 000, 'type': 'test type'})
    mock_post.return_value.ok = True

    assert send_incident('users', 'test@iheartradio.com', 'test_user', 'test_service', 'test_title', 'message').success


@patch('src.pager_duty.pd.requests.post')
@patch('src.pager_duty.pd.search_entity')
@patch('src.pager_duty.pd.search_entity')
def test_override_schedule(mock_schedule_search, mock_user_search, mock_post):
    mock_schedule_search.return_value = EntityResp(Status(True, 'good'), entity={'id': '000'})
    mock_user_search.return_value = EntityResp(Status(True, 'good'), entity={'id': '001', 'name': 'test user'})
    mock_post.return_value.ok = True

    assert override_schedule('schedule', 'user', '2018-03-01T00:00:00-04:00', '2018-03-02T00:00:00-04:00').success


@patch('src.pager_duty.pd.list_oncalls_by_ep')
@patch('src.pager_duty.pd.list_all_entities')
def test_ensure_oncalls(mock_list_all_entities, mock_list_oncalls_by_ep):
    mock_list_all_entities.return_value = EntitiesResp(Status(True, 'good'), ['test_ep'])
    mock_list_oncalls_by_ep.return_value = EntitiesResp(Status(True, 'good'), {'oncalls': [{'escalation_level': 2}]})

    assert ensure_oncalls().entities == ['test_ep: oncall level 1 does not exist']


@patch('src.pager_duty.pd.get_all_entities_resp')
def test_search_entity(mock_get_all_users):
    mock_get_all_users.return_value = EntitiesResp(Status(True, 'good'),
                                                   {'users': [{'name': 'Test User'}, {'name': 'Test User 2'}]})

    assert search_entity('Test User', 'users').entity == {'name': 'Test User'}


@patch('src.pager_duty.pd.get_all_entities_resp')
def test_list_all_entities(mock_get_all_users):
    mock_get_all_users.return_value = EntitiesResp(Status(True, 'good'),
                                                   {'users': [{'name': 'Test User'}, {'name': 'Test User 2'}]})

    assert list_all_entities('users').entities == ['Test User', 'Test User 2']


@patch('src.pager_duty.pd.list_ep_by_level')
@patch('src.pager_duty.pd.list_contact_methods')
def test_list_specific_entity(mock_list_contact_methods, mock_list_ep_by_level):
    mock_list_contact_methods.return_value = EntitiesResp(Status(True, 'test success'), {'phone': ['1112223333']})
    assert list_specific_entity('oncalls', 'test_name').entity == {'phone': ['1112223333']}

    mock_list_ep_by_level.return_value = EntityResp(Status(True, 'test success'), {1: ['test, phone: 1112223333']})
    assert list_specific_entity('escalation_policies', 'test_ep').entity == "1: ['test, phone: 1112223333']"


@patch('src.pager_duty.pd.list_contact_methods')
@patch('src.pager_duty.pd._get_entities_resp_helper')
@patch('src.pager_duty.pd.requests.get')
@patch('src.pager_duty.pd.search_entity')
def test_list_ep_by_level(mock_search_entity, mock_get, mock_get_entities_resp_helper, mock_list_contact_methods):
    mock_search_entity.return_value = EntityResp(Status(True, 'good'), {'id': 1111})
    mock_get.return_value.ok = True
    oncalls = {'oncalls': [{'escalation_level': 1, 'user': {'summary': 'test user 1'}},
                           {'escalation_level': 2, 'user': {'summary': 'test user 2'}}]}
    mock_get_entities_resp_helper.return_value = EntitiesResp(Status(True, 'good'), oncalls)

    mock_list_contact_methods.return_value = EntitiesResp(Status(True, 'good'),
                                                          {'email': ['test@iheartmedia.com'], 'phone': ['1112223333']})

    result = list_ep_by_level('test ep')

    assert result.entity == collections. \
        OrderedDict({1: ['test user 1, email: test@iheartmedia.com, phone: 1112223333'],
                     2: ['test user 2, email: test@iheartmedia.com, phone: 1112223333']})


@patch('src.pager_duty.pd._get_entities_resp_helper')
@patch('src.pager_duty.pd.get_user_contact_methods')
@patch('src.pager_duty.pd.search_entity')
def test_list_contact_methods(mock_search_entity, mock_get_user_contact_methods, mock_get_entities_resp_helper):
    mock_search_entity.return_value = EntityResp(Status(True, 'good'), {'name': 'test user', 'id': '00000'})
    mock_get_user_contact_methods.return_value.ok = True
    mock_get_entities_resp_helper.status.success = False

    assert list_contact_methods('test user').entities is not None


@patch('src.pager_duty.pd.requests.get')
def test_get_all_entities_resp(mock_get):
    mock_get.return_value.ok = True
    mock_get.return_value.json.return_value = {'test entity': 'test value'}

    entities_resp = get_all_entities_resp('users')

    assert entities_resp.status.success
    assert entities_resp.entities == {'test entity': 'test value'}


@patch('src.pager_duty.pd.requests.get')
def test_get_user_contact_methods(mock_get):
    mock_get.return_value.ok = True

    assert get_user_contact_methods('00000') is not None


def test_clean_contact_methods():
    test_cm = [
        {
            'type': 'phone_contact_method',
            'address': '1112223333',
            'name': 'test user',
            'html_url': 'test html url',
            'self': 'test self',
            'label': 'test label',
            'id': '00000',
        },
        {
            'type': 'phone_contact_method',
            'address': '2223334444',
            'name': 'test user 2',
            'html_url': 'test html url 2',
            'self': 'test self 2',
            'label': 'test label 2',
            'id': '00001',
        },
        {
            'type': 'email_contact_method',
            'address': 'test@iheartradio.com',
            'name': 'test user 3',
            'html_url': 'test html url 3',
            'self': 'test self 3',
            'label': 'test label 3',
            'id': '00002',
        }
    ]

    assert clean_contact_method(test_cm) == {'phone': ['1112223333', '2223334444'], 'email': ['test@iheartradio.com']}


def test_contact_methods_to_string():
    test_cm = {'phone': ['1112223333', '2223334444'], 'email': ['test@iheartradio.com']}

    assert contact_methods_to_string(test_cm) == 'phone: 1112223333 & 2223334444, email: test@iheartradio.com'


def test_sort_ep():
    mock_unsorted_data = {3: 'test 3', 1: 'test 1', 4: 'test 4', 2: 'test 2'}
    assert mock_unsorted_data == collections.OrderedDict({1: 'test 1', 2: 'test 2', 3: 'test 3', 4: 'test 4'})
