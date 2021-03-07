"""
Copyright 2021 Venceslas Roullier, Daniel Santos Bustos, Guillem Sanyas, Julien Tagnani, Agustin Zorzano

This file is part of OpenEmailAntispam.

    OpenEmailAntispam is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    OpenEmailAntispam is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with OpenEmailAntispam.  If not, see https://www.gnu.org/licenses/.
"""

class ApiError(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)
        self.status_code = 404


class ImapError(ApiError):
    def __init__(self, *args, **kwargs):
        ApiError.__init__(self, *args, **kwargs)
        self.args += ("IMAP error produced",)


class SmtpError(ApiError):
    def __init__(self, *args, **kwargs):
        ApiError.__init__(self, *args, **kwargs)
        self.args += ("SMTP error produced",)


class EncryptionError(ApiError):
    def __init__(self, *args, **kwargs):
        ApiError.__init__(self, *args, **kwargs)
        self.args += ("Error in decryption.",)
        self.status_code = 400
