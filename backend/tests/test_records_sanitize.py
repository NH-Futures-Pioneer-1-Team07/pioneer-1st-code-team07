from app.records.sanitize import is_secret_key, sanitize


def test_비밀정보_키를_알아본다():
    secret = ["appkey", "AppKey", "app_key", "APP_SECRET", "appsecret", "access_token", "Authorization", "password"]
    secret += ["account_no", "accountNumber", "acnt_no", "계좌번호", "bearer_token"]
    for name in secret:
        assert is_secret_key(name), name


def test_일반_필드는_비밀정보가_아니다():
    for name in ["price", "quantity", "reason", "entry_id", "reference_high", "net_pnl", "strategy_id", "key_level"]:
        assert not is_secret_key(name), name


def test_중첩된_딕셔너리와_리스트_안의_비밀정보도_제거한다():
    data = {
        "price": 70000,
        "request": {"header": {"authorization": "Bearer x", "appkey": "k"}, "body": {"qty": 1}},
        "orders": [{"id": 1, "계좌번호": "123"}, {"id": 2, "token": "t"}],
    }

    assert sanitize(data) == {
        "price": 70000,
        "request": {"header": {}, "body": {"qty": 1}},
        "orders": [{"id": 1}, {"id": 2}],
    }


def test_원본은_바꾸지_않는다():
    data = {"token": "t", "price": 1}

    sanitize(data)

    assert data == {"token": "t", "price": 1}
