from dataclasses import dataclass


@dataclass
class SmsMessage:
    phone: str
    code: str


class LocalStubSmsSender:
    def __init__(self):
        self.sent_messages = []

    def send_code(self, phone, code):
        self.sent_messages.append(SmsMessage(phone=phone, code=code))

    def reset(self):
        self.sent_messages.clear()


_sms_sender = LocalStubSmsSender()


def get_sms_sender():
    return _sms_sender


def reset_sms_sender():
    global _sms_sender
    _sms_sender = LocalStubSmsSender()
    return _sms_sender
