from unittest.mock import patch

from src.hipchat import hipchat


def test_get_capabilities_descriptor():
    result = hipchat.get_capabilities_descriptor('test webhook url')

    assert result.status.success


@patch('src.hipchat.hipchat.requests.get')
def test_get_all_rooms(mock_get):
    mock_get.return_value.ok = True
    response = hipchat._get_all_rooms()

    assert response.status.success


@patch('src.hipchat.hipchat.requests.post')
def test_create_web_hook(mock_post):
    mock_post.return_value.ok = True
    response = hipchat.create_web_hook(123456, 'test pattern', 'https://testsendurl.com', 'room_message')

    assert response.success


@patch('src.hipchat.hipchat.requests.post')
def test_send_room_notification(mock_post):
    mock_post.return_value.ok = True
    response = hipchat.send_room_notification(123456, 'test msg', 'blue')

    assert response.success


@patch('src.hipchat.hipchat.requests.delete')
def test_del_room_webhook(mock_post):
    mock_post.return_value.ok = True
    response = hipchat._del_room_webhook(123456, 654321)

    assert response.success
