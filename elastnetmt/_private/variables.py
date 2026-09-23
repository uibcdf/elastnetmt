# ElastNetMT Private Variables and Utilities


def is_all(value):
    if isinstance(value, str):
        return value.lower() == "all"
    return False


def is_iterable(value):
    try:
        iter(value)
        return not isinstance(value, (str, bytes))
    except TypeError:
        return False
