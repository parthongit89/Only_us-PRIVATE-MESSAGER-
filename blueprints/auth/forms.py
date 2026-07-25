class LoginForm:
    def __init__(self, email="", password="", passcode=""):
        self.email = email
        self.password = password
        self.passcode = passcode

class RequestAccessForm:
    def __init__(self, email="", password="", passcode="", from_email="", for_email=""):
        self.email = email
        self.password = password
        self.passcode = passcode
        self.from_email = from_email
        self.for_email = for_email

class OTPVerifyForm:
    def __init__(self, otp=""):
        self.otp = otp
