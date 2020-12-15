class ApiError(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)
        self.status_code = 404


class ImapError(ApiError):
    def __init__(self, *args, **kwargs):
        ApiError.__init__(self, *args, **kwargs)
        self.args += ("IMAP error produced", )


class EncryptionError(ApiError):
    def __init__(self, *args, **kwargs):
        ApiError.__init__(self, *args, **kwargs)
        self.args += ("Error in decryption.", )
        self.status_code = 400

