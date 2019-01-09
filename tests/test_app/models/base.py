from datetime import datetime

import sqlalchemy as _sa
from sqlalchemy.ext.declarative import declarative_base


class _Base:
    @classmethod
    def PK(cls) -> _sa.Column:
        """
        Generates a column as general Primary Key
        """
        return _sa.Column(_sa.Integer, primary_key=True, autoincrement=True)

    @classmethod
    def Bool(cls) -> _sa.Column:
        """
        Generates a column as a Boolean with default-within-project params
        """

        return _sa.Column(
            _sa.Boolean,
            default=False,
            index=False,
            nullable=False,
            server_default=_sa.text("false"),
        )

    @classmethod
    def FK(cls, column: str) -> _sa.Column:
        """
        Generates a column as a Foreign Key with:
        * index=True
        * nullable=False
        * onupdate: CASCADE
        * ondelete: CASCADE
        """

        return _sa.Column(
            _sa.Integer,
            _sa.ForeignKey(column, onupdate="CASCADE", ondelete="CASCADE"),
            index=True,
            nullable=False,
        )

    @classmethod
    def Numeric(cls, **kwargs) -> _sa.Column:
        """
        Generates a column of Numeric type with predefined accuracy
        """
        return _sa.Column(_sa.Numeric(precision=28, scale=4), **kwargs)

    record_created = _sa.Column(
        _sa.DateTime,
        nullable=False,
        default=datetime.now,
        server_default=_sa.text("statement_timestamp()"),
    )

    record_modified = _sa.Column(
        _sa.DateTime,
        nullable=False,
        default=datetime.now,
        server_default=_sa.text("statement_timestamp()"),
        onupdate=datetime.now,
        index=True,
    )


Model = declarative_base(cls=_Base)
