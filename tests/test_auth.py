from app import auth


def test_signup_and_login(tmp_path, monkeypatch):
    monkeypatch.setattr(auth, "DB", str(tmp_path / "u.db"))
    assert auth.create_user("Jana_1", "secret1") == "ok"
    assert auth.create_user("jana_1", "other12") == "taken"
    assert auth.verify("JANA_1", "secret1")
    assert not auth.verify("jana_1", "wrong")
    assert not auth.verify("nobody", "secret1")


def test_validation(tmp_path, monkeypatch):
    monkeypatch.setattr(auth, "DB", str(tmp_path / "u.db"))
    assert auth.create_user("a", "secret1") == "bad_user"
    assert auth.create_user("valid_name", "123") == "short_pw"