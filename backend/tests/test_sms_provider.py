from app.config import Settings
from app.notifications.sms import _local10


def test_provider_auto_resolution():
    assert Settings().resolved_sms_provider == "console"
    assert Settings().sms_configured is False

    assert Settings(aakash_sms_token="tok").resolved_sms_provider == "aakash"
    assert Settings(aakash_sms_token="tok").sms_configured is True

    assert (
        Settings(sparrow_sms_token="tok", sparrow_sms_from="ORG").resolved_sms_provider
        == "sparrow"
    )
    # sparrow needs both token and sender id
    assert Settings(sparrow_sms_token="tok").resolved_sms_provider == "console"

    assert (
        Settings(
            twilio_account_sid="AC", twilio_auth_token="x", twilio_from="+1"
        ).resolved_sms_provider
        == "twilio"
    )


def test_explicit_provider_overrides_auto():
    assert Settings(sms_provider="sparrow").resolved_sms_provider == "sparrow"


def test_local10_normalises_nepal_numbers():
    assert _local10("+9779865365226") == "9865365226"
    assert _local10("9779865365226") == "9865365226"
    assert _local10("9865365226") == "9865365226"
    assert _local10("977-98-6536-5226") == "9865365226"
