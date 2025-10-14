import importlib.util
import sys
from pathlib import Path
import pytest

# Load the api module directly from file to avoid importing Home Assistant packages
ROOT = Path(__file__).resolve().parents[1]
api_path = ROOT / "custom_components" / "risegarden" / "api.py"
spec = importlib.util.spec_from_file_location("risegarden.api", str(api_path))
api = importlib.util.module_from_spec(spec)
sys.modules["risegarden.api"] = api
spec.loader.exec_module(api)

RiseGardenClient = api.RiseGardenClient


class DummyResponse:
    def __init__(self, status, data):
        self.status = status
        self._data = data

    async def json(self):
        return self._data

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeSession:
    def __init__(self, post_responses=None, request_responses=None):
        self._post = post_responses or []
        self._request = request_responses or []

    def post(self, url, json=None, headers=None, timeout=None):
        status, data = self._post.pop(0)
        return DummyResponse(status, data)

    def request(self, method, url, headers=None, params=None, json=None, timeout=None):
        status, data = self._request.pop(0)
        return DummyResponse(status, data)


@pytest.mark.asyncio
async def test_login_success():
    session = FakeSession(post_responses=[(200, {"token": "t", "refresh_token": "r", "expires_in": 1000, "user": {"id": "u"}})])
    client = RiseGardenClient(session, "e", "p")
    ok = await client.login()
    assert ok
    assert client._access_token == "t"
    assert client._refresh_token == "r"
    assert client._user_id == "u"


@pytest.mark.asyncio
async def test_refresh_success():
    session = FakeSession(post_responses=[(200, {"token": "newt", "expires_in": 2000})])
    client = RiseGardenClient(session, "e", "p")
    client._refresh_token = "r"
    client._access_token = "old"
    ok = await client.refresh()
    assert ok
    assert client._access_token == "newt"


@pytest.mark.asyncio
async def test_get_gardens_uses_request():
    session = FakeSession(request_responses=[(200, {"gardens": [{"id": 1}]})])
    client = RiseGardenClient(session, "e", "p")
    client._access_token = "token"
    data = await client.get_gardens()
    assert data == {"gardens": [{"id": 1}]}
