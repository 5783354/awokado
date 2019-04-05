from sqlalchemy.sql import Selectable

from awokado.exceptions import (
    CreateResourceForbidden,
    ReadResourceForbidden,
    UpdateResourceForbidden,
    DeleteResourceForbidden,
)


class BaseAuth:
    CREATE = {
        # 'ROLE NAME HERE': Boolean value,
        #  Example:
        # 'ADMIN': True,
        # 'GUEST': False,
    }
    READ = {}
    UPDATE = {}
    DELETE = {}

    @classmethod
    def can_create(cls, session, payload, user_id: int, skip_exc=False):
        if skip_exc:
            return False
        raise CreateResourceForbidden()

    @classmethod
    def can_read(cls, ctx, query: Selectable, skip_exc=False):
        if skip_exc:
            return False

        raise ReadResourceForbidden()

    @classmethod
    def can_update(cls, session, user_id: int, obj_ids: list, skip_exc=False):
        if skip_exc:
            return False

        raise UpdateResourceForbidden()

    @classmethod
    def can_delete(cls, session, user_id: int, obj_ids: list, skip_exc=False):
        if skip_exc:
            return False

        raise DeleteResourceForbidden()

    @classmethod
    def _get_read_query(cls, ctx, query: Selectable):
        return query
