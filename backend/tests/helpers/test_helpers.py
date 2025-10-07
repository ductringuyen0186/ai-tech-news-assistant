def assert_equal(actual, expected):
    assert actual == expected, f'Expected {expected}, but got {actual}'

def assert_in(item, collection):
    assert item in collection, f'Expected {item} to be in {collection}'

def assert_not_in(item, collection):
    assert item not in collection, f'Expected {item} to not be in {collection}'