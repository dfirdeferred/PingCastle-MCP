from pingcastle_mcp import cli


class FakeStore:
    def __init__(self): self.key = None
    def set_api_key(self, k): self.key = k
    def get_api_key(self): return self.key


def test_configure_persists_url_and_key(monkeypatch, tmp_path):
    saved = {}
    monkeypatch.setattr(cli, "save_url", lambda u: saved.__setitem__("url", u))
    store = FakeStore()
    answers = iter(["https://pc.test/"])
    rc = cli.configure(
        input_fn=lambda _: next(answers),
        getpass_fn=lambda _: "secretkey",
        store=store,
        validate=False,
    )
    assert rc == 0
    assert saved["url"] == "https://pc.test"
    assert store.key == "secretkey"
