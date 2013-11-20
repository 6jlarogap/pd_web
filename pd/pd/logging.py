# -*- coding: utf-8 -*-

from django.http import UnreadablePostError

def skip_unreadable_post(record):
    """
     Filter out UnreadablePostError (raised when a user cancels an upload) from the admin emails
    """
    if record.exc_info:
        exc_type, exc_value = record.exc_info[:2]
        if isinstance(exc_value, UnreadablePostError):
            return False
    return True
