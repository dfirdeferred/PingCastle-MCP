from pingcastle_mcp.credentials import CredentialStore


class FakeKeyring:
    def __init__(self):
        self.store = {}

    def get_password(self, service, user):
        return self.store.get((service, user))

    def set_password(self, service, user, value):
        self.store[(service, user)] = value

    def delete_password(self, service, user):
        self.store.pop((service, user), None)


def test_set_get_delete_roundtrip():
    cs = CredentialStore(keyring_backend=FakeKeyring())
    assert cs.get_api_key() is None
    cs.set_api_key("secret123")
    assert cs.get_api_key() == "secret123"
    cs.delete_api_key()
    assert cs.get_api_key() is None
