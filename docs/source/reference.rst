Reference book
**************

In class Meta we declare different resource's options:

.. contents::
    :local:
    :backlinks: none

name
----
    used for two resources connection by relation

model
-----
    represents sqlalchemy model

methods
-------
    tuple of methods you want to use

disable_totals
--------------
    set false, if you don't need to know returning objects amount in read-requests

auth
----
    awokado BaseAuth object for embedding authentication logic

select_from
-----------
    provide data source here if your resource use another's model fields (for example sa.outerjoin(FirstModel, SecondModel, FirstModel.id == SecondModel.first_model_id))

skip_doc
--------
    set true if you don't need to add resource to documentation


Override methods
----------------

There are possibility for certain methods to write your own behavior.
For example:

.. code-block:: python
   :linenos:

    def create(self, session, payload: dict, user_id: int) -> dict:
        # prepare data to insert
        data = payload[self.Meta.name]

        if isinstance(data, list):
            result = self.bulk_create(session, user_id, data)
            return result

        result = self.load(data)

        data_to_insert = self._to_create(result)

        # insert to DB
        resource_id = session.execute(
            sa.insert(self.Meta.model)
            .values(data_to_insert)
            .returning(self.Meta.model.id)
        ).scalar()

        data["id"] = resource_id
        self._save_m2m(session, data)

        result = self.read_handler(
            session=session, user_id=user_id, resource_id=resource_id
        )

        return result
