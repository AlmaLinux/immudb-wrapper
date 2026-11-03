import logging
from unittest.mock import Mock, patch

import pytest
from grpc import RpcError, StatusCode

from immudb_wrapper import ImmudbWrapper


class FakeRpcError(RpcError):
    def __init__(self, code):
        self._code = code

    def code(self):
        return self._code


@pytest.fixture
def wrapper():
    # a client that never talks to a server
    instance = ImmudbWrapper.__new__(ImmudbWrapper)
    instance.logger = logging.getLogger()
    instance.max_retries = 1
    instance.retry_timeout = 0
    with patch.multiple(
        instance,
        login=Mock(),
        verifiedGet=Mock(),
        verifiedSet=Mock(),
        to_dict=Mock(side_effect=lambda response: response),
    ):
        yield instance


class TestImmudbWrapper:
    def test_calls_do_not_login(self, wrapper):
        wrapper.verifiedGet.return_value = {'value': {'Hash': 'abc'}}
        wrapper.verifiedSet.return_value = Mock()

        assert wrapper.authenticate('abc') == {'value': {'Hash': 'abc'}}
        with patch('immudb_wrapper.asdict', return_value={}):
            wrapper.notarize('abc', {'Hash': 'abc'})
        wrapper.login.assert_not_called()

    @pytest.mark.parametrize(
        'code', [StatusCode.UNAUTHENTICATED, StatusCode.PERMISSION_DENIED]
    )
    def test_relogin_on_rejected_token(self, wrapper, code):
        wrapper.verifiedGet.side_effect = [
            FakeRpcError(code),
            {'value': {'Hash': 'abc'}},
        ]

        assert wrapper.authenticate('abc') == {'value': {'Hash': 'abc'}}
        wrapper.login.assert_called_once()
        assert wrapper.verifiedGet.call_count == 2

    def test_other_errors_are_reported(self, wrapper):
        wrapper.verifiedGet.side_effect = FakeRpcError(StatusCode.NOT_FOUND)

        assert 'error' in wrapper.authenticate('abc')
        wrapper.login.assert_not_called()
