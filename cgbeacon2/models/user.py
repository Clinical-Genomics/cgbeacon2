# -*- coding: utf-8 -*-
from uuid import uuid4


class User:
    """Class defining a service user"""

    def __init__(self, user_dict):
        """Instantiate a new user"""
        self._id = user_dict["_id"]
        self.name = user_dict["name"]
        self.description = user_dict["description"]
        self.url = user_dict.get("url")
        self.created = user_dict["created"]
        self.token = self._create_token()

    def _create_token(self):
        """Creates an authentication token for a new user"""
        return str(uuid4())
