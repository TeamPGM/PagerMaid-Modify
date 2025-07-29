class QRCodeWebError(Exception):
    """
    Occurs when the QR code is not scanned.
    """

    def __init__(self, msg: str):
        self.msg = msg
        super().__init__("QR code not scanned")


class QRCodeWebCodeError(QRCodeWebError):
    """
    Occurs when the QR code is not scanned.
    """

    def __init__(self, code: str):
        self.code = code
        super().__init__("QR code not scanned")


class QRCodeWebNeedPWDError(QRCodeWebError):
    """
    Occurs when the account needs to be verified.
    """

    def __init__(self, hint: str):
        self.hint = hint
        super().__init__("Account needs to be verified")
