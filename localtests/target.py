def target(value):
    """
    Function vulnerable to a timing attack.
    """
    teststring = "hello world hack the planetABCD1"
    for idx, value in enumerate(value):
        if teststring[idx] != value:
            return False

    return True
