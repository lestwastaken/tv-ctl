class PhilipsError(Exception):
    pass


class PhilipsConnectionError(PhilipsError):
    pass


class PhilipsAuthError(PhilipsError):
    pass
