from sqlalchemy import types
from sqlalchemy.types import Binary
from sqlalchemy.schema import Column
from functools import partial

import uuid

# Prevents setting Not Null on each NotNullColumn
NotNullColumn = partial(Column, nullable=False)


# http://stackoverflow.com/a/812363
class UUID(types.TypeDecorator):
    impl = Binary

    def __init__(self):
        self.impl.length = 32
        types.TypeDecorator.__init__(self, length=self.impl.length)

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(self.impl)

    def process_bind_param(self, value, dialect=None):
        if value and isinstance(value, uuid.UUID):
            return value.bytes
        elif value and not isinstance(value, uuid.UUID):
            raise ValueError, 'value %s is not a valid uuid.UUID' % value
        else:
            return None

    def process_result_value(self, value, dialect=None):
        if value:
            return uuid.UUID(bytes=value)
        else:
            return None

    def is_mutable(self):
        return False


def id_column():
    import uuid
    return NotNullColumn(UUID(), primary_key=True, default=uuid.uuid4)
