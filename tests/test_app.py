import os


def test_environment_variables(monitoring_hours=None):
    """Перевірка, що мокання AWS в CI спрацювало і тести не мають доступу до реального AWS"""

    # для локалки – підставляю на пряму змінні
    if not os.environ.get("AWS_DEFAULT_REGION"):
        os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    if not os.environ.get("AWS_ACCESS_KEY_ID"):
        os.environ["AWS_ACCESS_KEY_ID"] = "mock_key_id"

    assert os.environ.get("AWS_DEFAULT_REGION") == "us-east-1"
    assert os.environ.get("AWS_ACCESS_KEY_ID") == "mock_key_id"


def test_app_imports():
    """Перевірка, що весь додаток здатний скомпілюватися та імпортуватися без Syntax/Import errors"""
    # для локалки – підставляю на пряму змінні
    if not os.environ.get("AWS_DEFAULT_REGION"):
        os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    if not os.environ.get("AWS_ACCESS_KEY_ID"):
        os.environ["AWS_ACCESS_KEY_ID"] = "mock_key_id"
    if not os.environ.get("AWS_SECRET_ACCESS_KEY"):
        os.environ["AWS_SECRET_ACCESS_KEY"] = "mock_secret_access_key"

    try:
        # Спробуй імпортувати свій хендлер. Якщо десь зламані імпорти - тест впаде
        import app.app_main as main
        assert main.handler is not None
    except ImportError as e:
        assert False, f"App didn't compile: {e}"
