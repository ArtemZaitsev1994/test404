from views import Handler, Info


routes = [
    ('*', '/api/contacts', Handler),
    ('GET', '/api/get_failed_mess', Info),
]
