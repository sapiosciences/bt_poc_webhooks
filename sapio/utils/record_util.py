from __future__ import annotations

from typing import Tuple, List, Type, Any, Dict, Optional, Iterable

from sapiopycommons.general.aliases import RecordModel, SapioRecord
from sapiopycommons.general.exceptions import SapioException
from sapiopylib.rest.DataRecordManagerService import DataRecordManager
from sapiopylib.rest.pojo.DataRecord import DataRecord
from sapiopylib.rest.pojo.DataRecordPaging import DataRecordPojoPageCriteria
from sapiopylib.rest.pojo.webhook.WebhookContext import SapioWebhookContext
from sapiopylib.rest.utils.recordmodel.PyRecordModel import PyRecordModel
from sapiopylib.rest.utils.recordmodel.RecordModelManager import RecordModelManager, RecordModelInstanceManager, \
    RecordModelRelationshipManager
from sapiopylib.rest.utils.recordmodel.RecordModelWrapper import WrappedType
from sapiopylib.rest.utils.recordmodel.RelationshipPath import RelationshipPath, RelationshipPathDir


# FR-46064 - Initial port of PyWebhookUtils to sapiopycommons.
class RecordUtil:
    """
    A collection of shorthand methods for dealing with the various record managers.
    """
    __context: SapioWebhookContext
    dr_man: DataRecordManager
    rec_man: RecordModelManager
    inst_man: RecordModelInstanceManager
    rel_man: RecordModelRelationshipManager

    def __init__(self, context: SapioWebhookContext):
        """
        :param context: The current webhook context.
        """
        self.__context = context
        self.dr_man = context.data_record_manager
        self.rec_man = RecordModelManager(context.user)
        self.inst_man = self.rec_man.instance_manager
        self.rel_man = self.rec_man.relationship_manager

    def wrap_model(self, record: DataRecord, wrapper_type: Type[WrappedType]) -> WrappedType:
        """
        Shorthand for adding a single data record as a record model.
        :param record: The data record to wrap.
        :param wrapper_type: The record model wrapper to use.
        :return: The record model for the input.
        """
        return self.inst_man.add_existing_record_of_type(record, wrapper_type)

    def wrap_models(self, records: Iterable[DataRecord], wrapper_type: Type[WrappedType]) -> List[WrappedType]:
        """
        Shorthand for adding a list of data records as record models.
        :param records: The data records to wrap.
        :param wrapper_type: The record model wrapper to use.
        :return: The record models for the input.
        """
        return self.inst_man.add_existing_records_of_type(list(records), wrapper_type)

    def query_models(self, wrapper_type: Type[WrappedType], field: str, value_list: Iterable[Any],
                     page_limit: Optional[int] = None) -> List[WrappedType]:
        """
        Shorthand for using the data record manager to query for a list of data records by field value
        and then converting the results into a list of record models.
        :param wrapper_type: The record model wrapper to use.
        :param field: The field to query on.
        :param value_list: The values of the field to query on.
        :param page_limit: The maximum number of pages to query. If None, exhausts all possible pages.
        :return: The record models for the queried records.
        """
        return self.query_models_with_criteria(wrapper_type, field, value_list, None, page_limit)[0]

    def query_models_with_criteria(self, wrapper_type: Type[WrappedType], field: str, value_list: Iterable[Any],
                                   paging_criteria: Optional[DataRecordPojoPageCriteria] = None,
                                   page_limit: Optional[int] = None) \
            -> Tuple[List[WrappedType], DataRecordPojoPageCriteria]:
        """
        Shorthand for using the data record manager to query for a list of data records by field value
        and then converting the results into a list of record models.
        :param wrapper_type: The record model wrapper to use.
        :param field: The field to query on.
        :param value_list: The values of the field to query on.
        :param paging_criteria: The paging criteria to start the query with.
        :param page_limit: The maximum number of pages to query from the starting criteria. If None, exhausts all
            possible pages.
        :return: The record models for the queried records and the final paging criteria.
        """
        dt: str = wrapper_type.get_wrapper_data_type_name()
        records, paging_criteria = self.__exhaust_query_pages(dt, field, list(value_list), paging_criteria, page_limit)
        return self.wrap_models(records, wrapper_type), paging_criteria

    def query_models_by_id(self, wrapper_type: Type[WrappedType], ids: Iterable[int],
                           page_limit: Optional[int] = None) -> List[WrappedType]:
        """
        Shorthand for using the data record manager to query for a list of data records by record ID
        and then converting the results into a list of record models.
        :param wrapper_type: The record model wrapper to use.
        :param ids: The list of record IDs to query.
        :param page_limit: The maximum number of pages to query. If None, exhausts all possible pages.
        :return: The record models for the queried records.
        """
        return self.query_models_by_id_with_criteria(wrapper_type, ids, None, page_limit)[0]

    def query_models_by_id_with_criteria(self, wrapper_type: Type[WrappedType], ids: Iterable[int],
                                         paging_criteria: Optional[DataRecordPojoPageCriteria] = None,
                                         page_limit: Optional[int] = None) \
            -> Tuple[List[WrappedType], DataRecordPojoPageCriteria]:
        """
        Shorthand for using the data record manager to query for a list of data records by record ID
        and then converting the results into a list of record models.
        :param wrapper_type: The record model wrapper to use.
        :param ids: The list of record IDs to query.
        :param paging_criteria: The paging criteria to start the query with.
        :param page_limit: The maximum number of pages to query from the starting criteria. If None, exhausts all
            possible pages.
        :return: The record models for the queried records and the final paging criteria.
        """
        dt: str = wrapper_type.get_wrapper_data_type_name()
        records, paging_criteria = self.__exhaust_query_id_pages(dt, list(ids), paging_criteria, page_limit)
        return self.wrap_models(records, wrapper_type), paging_criteria

    def query_all_models(self, wrapper_type: Type[WrappedType], page_limit: Optional[int] = None) -> List[WrappedType]:
        """
        Shorthand for using the data record manager to query for all data records of a given type
        and then converting the results into a list of record models.
        :param wrapper_type: The record model wrapper to use.
        :param page_limit: The maximum number of pages to query. If None, exhausts all possible pages.
        :return: The record models for the queried records.
        """
        return self.query_all_models_with_criteria(wrapper_type, None, page_limit)[0]

    def query_all_models_with_criteria(self, wrapper_type: Type[WrappedType],
                                       paging_criteria: Optional[DataRecordPojoPageCriteria] = None,
                                       page_limit: Optional[int] = None) \
            -> Tuple[List[WrappedType], DataRecordPojoPageCriteria]:
        """
        Shorthand for using the data record manager to query for all data records of a given type
        and then converting the results into a list of record models.
        :param wrapper_type: The record model wrapper to use.
        :param paging_criteria: The paging criteria to start the query with.
        :param page_limit: The maximum number of pages to query from the starting criteria. If None, exhausts all
            possible pages.
        :return: The record models for the queried records and the final paging criteria.
        """
        dt: str = wrapper_type.get_wrapper_data_type_name()
        records, paging_criteria = self.__exhaust_query_all_pages(dt, paging_criteria, page_limit)
        return self.wrap_models(records, wrapper_type), paging_criteria

    def add_model(self, wrapper_type: Type[WrappedType]) -> WrappedType:
        """
        Shorthand for using the instance manager to add a new record model of the given type.
        :param wrapper_type: The record model wrapper to use.
        :return: The newly added record model.
        """
        return self.inst_man.add_new_record_of_type(wrapper_type)

    def add_models(self, wrapper_type: Type[WrappedType], num: int) -> List[WrappedType]:
        """
        Shorthand for using the instance manager to add new record models of the given type.
        :param wrapper_type: The record model wrapper to use.
        :param num: The number of models to create.
        :return: The newly added record models.
        """
        return self.inst_man.add_new_records_of_type(num, wrapper_type)

    def add_models_with_data(self, wrapper_type: Type[WrappedType], fields: List[Dict[str, Any]]) -> List[WrappedType]:
        """
        Shorthand for using the instance manager to add new models of the given type, and then initializing all those
        models with the given fields.
        :param wrapper_type: The record model wrapper to use.
        :param fields: A list of field maps to initialize the record models with.
        :return: The newly added record models with the provided fields set. The records will be in the same order as
            the fields in the fields list.
        """
        models: List[WrappedType] = self.add_models(wrapper_type, len(fields))
        for model, field in zip(models, fields):
            model.set_field_values(field)
        return models

    def create_models(self, wrapper_type: Type[WrappedType], num: int) -> List[WrappedType]:
        """
        Shorthand for creating new records via the data record manager and then returning them as wrapped
        record models. Useful in cases where your record model needs to have a valid record ID.

        Makes a webservice call to create the data records.
        :param wrapper_type: The record model wrapper to use.
        :param num: The number of new records to create.
        :return: The newly created record models.
        """
        dt: str = wrapper_type.get_wrapper_data_type_name()
        return self.wrap_models(self.dr_man.add_data_records(dt, num), wrapper_type)

    def create_models_with_data(self, wrapper_type: Type[WrappedType], fields: List[Dict[str, Any]]) \
            -> List[WrappedType]:
        """
        Shorthand for creating new records via the data record manager with field data to initialize the records with
        and then returning them as wrapped record models. Useful in cases where your record model needs to have a valid
        record ID.

        Makes a webservice call to create the data records.
        :param wrapper_type: The record model wrapper to use.
        :param fields: The field map list to initialize the new data records with.
        :return: The newly created record models.
        """
        dt: str = wrapper_type.get_wrapper_data_type_name()
        return self.wrap_models(self.dr_man.add_data_records_with_data(dt, fields), wrapper_type)

    def find_or_create_model(self, wrapper_type: Type[WrappedType], primary_identifier: str, id_value: Any,
                             secondary_identifiers: Optional[Dict[str, Any]] = None) -> WrappedType:
        """
        Find a unique record that has a field matching the given value. If no such records exist, create one with the
        identifying fields set to the desired value. If more than one record with the identifying values exists,
        throws an exception.

        Makes a webservice call to query for the existing record. Makes an additional webservice call if the record
        needs to be created.
        :param wrapper_type: The record model wrapper to use.
        :param primary_identifier: The data field name of the field to search on.
        :param id_value: The value of the identifying field to search for.
        :param secondary_identifiers: Optional fields used to filter the records that are returned after searching on
            the primary identifier.
        :return: The record model with the identifying field value, either pulled from the system or newly created.
        """
        # Query for all records that match the primary identifier.
        results: List[WrappedType] = self.query_models(wrapper_type, primary_identifier, [id_value])

        # If a map of secondary identifiers has been provided, filter the list to only those records that match these
        # identifiers. If no secondary identifiers were provided, the above results are the filtered list.
        filtered: List[WrappedType] = []
        if secondary_identifiers is not None:
            for result in results:
                matches_all: bool = True
                for field, value in secondary_identifiers:
                    if result.get_field_value(field) != value:
                        matches_all = False
                        break
                if matches_all:
                    filtered.append(result)
        else:
            filtered = results
        result_count = len(filtered)

        # If the filtered list contains more than one item, throw an exception.
        if result_count > 1:
            raise SapioException(f"More than one record of type {wrapper_type.get_wrapper_data_type_name()} "
                                 f"encountered in system that matches all provided identifiers.")

        # If the filtered list contains a single item, return it.
        if result_count == 1:
            return filtered[0]

        # If the filtered list contains no items, create a new data record with all identifiers set and wrap the result.
        secondary_identifiers.update({primary_identifier: id_value})
        return self.create_models_with_data(wrapper_type, [secondary_identifiers])[0]

    @staticmethod
    def get_model_managers(context: SapioWebhookContext) \
            -> Tuple[RecordModelManager, RecordModelInstanceManager, RecordModelRelationshipManager]:
        """
        Get all three record model managers at once.
        :param context: The current webhook context.
        :return: A tuple containing a record model manager, instance manager, and relationship manager.
        """
        rec_man = RecordModelManager(context.user)
        inst_man = rec_man.instance_manager
        rel_man = rec_man.relationship_manager
        return rec_man, inst_man, rel_man

    @staticmethod
    def map_to_parent(models: Iterable[RecordModel], parent_type: Type[WrappedType]) -> Dict:
        """
        Map a list of record models to a single parent of a given type. The parents must already be loaded.
        :param models: A list of record models.
        :param parent_type: The record model wrapper of the parent.
        :return: A Dict[ModelType, ParentType]. If an input model doesn't have a parent of the given parent type, then
            it will map to None.
        """
        return_dict: Dict[RecordModel, WrappedType] = {}
        for model in models:
            return_dict[model] = model.get_parent_of_type(parent_type)
        return return_dict

    @staticmethod
    def map_to_parents(models: Iterable[RecordModel], parent_type: Type[WrappedType]) -> Dict:
        """
        Map a list of record models to a list parents of a given type. The parents must already be loaded.
        :param models: A list of record models.
        :param parent_type: The record model wrapper of the parents.
        :return: A Dict[ModelType, List[ParentType]]. If an input model doesn't have a parent of the given parent type,
            then it will map to an empty list.
        """
        return_dict: Dict[RecordModel, List[WrappedType]] = {}
        for model in models:
            return_dict[model] = model.get_parents_of_type(parent_type)
        return return_dict

    @staticmethod
    def map_by_parents(models: Iterable[RecordModel], parent_type: Type[WrappedType]) -> Dict:
        """
        Take a list of record models and map them by their parents. Essentially an inversion of map_to_parents. Input
        models that share a parent will end up in the same list. The parents must already be loaded.
        :param models: A list of record models.
        :param parent_type: The record model wrapper of the parents.
        :return: A Dict[ParentType, List[ModelType]]. If an input model doesn't have a parent of the given parent type,
            then it will not be in the resulting dictionary.
        """
        to_parents: Dict[RecordModel, List[WrappedType]] = RecordUtil.map_to_parents(models, parent_type)
        by_parents: Dict[WrappedType, List[RecordModel]] = {}
        for record, parents in to_parents.items():
            for parent in parents:
                by_parents.setdefault(parent, []).append(record)
        return by_parents

    @staticmethod
    def map_to_child(models: Iterable[RecordModel], child_type: Type[WrappedType]) -> Dict:
        """
        Map a list of record models to a single child of a given type. The children must already be loaded.
        :param models: A list of record models.
        :param child_type: The record model wrapper of the child.
        :return: A Dict[ModelType, ChildType]. If an input model doesn't have a child of the given child type, then
            it will map to None.
        """
        return_dict: Dict[RecordModel, WrappedType] = {}
        for model in models:
            return_dict[model] = model.get_child_of_type(child_type)
        return return_dict

    @staticmethod
    def map_to_children(models: Iterable[RecordModel], child_type: Type[WrappedType]) -> Dict:
        """
        Map a list of record models to a list children of a given type. The children must already be loaded.
        :param models: A list of record models.
        :param child_type: The record model wrapper of the children.
        :return: A Dict[ModelType, List[ChildType]]. If an input model doesn't have children of the given child type,
            then it will map to an empty list.
        """
        return_dict: Dict[RecordModel, List[WrappedType]] = {}
        for model in models:
            return_dict[model] = model.get_children_of_type(child_type)
        return return_dict

    @staticmethod
    def map_by_children(models: Iterable[RecordModel], child_type: Type[WrappedType]) -> Dict:
        """
        Take a list of record models and map them by their children. Essentially an inversion of map_to_children. Input
        models that share a child will end up in the same list. The children must already be loaded.
        :param models: A list of record models.
        :param child_type: The record model wrapper of the children.
        :return: A Dict[ParentType, List[ModelType]]. If an input model doesn't have children of the given child type,
            then it will not be in the resulting dictionary.
        """
        to_children: Dict[RecordModel, List[WrappedType]] = RecordUtil.map_to_children(models, child_type)
        by_children: Dict[WrappedType, List[RecordModel]] = {}
        for record, children in to_children.items():
            for child in children:
                by_children.setdefault(child, []).append(record)
        return by_children

    @staticmethod
    def map_by_id(models: Iterable[SapioRecord]) -> Dict[int, SapioRecord]:
        """
        Map the given records their record IDs.
        :param models: The records to map.
        :return: A dict mapping the record ID to each record.
        """
        ret_dict: Dict[int, SapioRecord] = {}
        for model in models:
            ret_dict.update({model.record_id: model})
        return ret_dict

    @staticmethod
    def map_by_field(models: Iterable[SapioRecord], field_name: str) -> Dict[Any, List[SapioRecord]]:
        """
        Map the given records by one of their fields. If any two records share the same field value, they'll appear in
        the same value list.
        :param models: The records to map.
        :param field_name: The field name to map against.
        :return: A dict mapping field values to the records with that value.
        """
        ret_dict: Dict[Any, List[SapioRecord]] = {}
        for model in models:
            val: Any = model.get_field_value(field_name)
            ret_dict.setdefault(val, []).append(model)
        return ret_dict

    @staticmethod
    def map_by_unique_field(models: Iterable[SapioRecord], field_name: str) -> Dict[Any, SapioRecord]:
        """
        Uniquely map the given records by one of their fields. If any two records share the same field value, throws
        an exception.
        :param models: The records to map.
        :param field_name: The field name to map against.
        :return: A dict mapping field values to the record with that value.
        """
        ret_dict: Dict[Any, SapioRecord] = {}
        for model in models:
            val: Any = model.get_field_value(field_name)
            if val in ret_dict:
                raise SapioException(f"Value {val} encountered more than once in models list.")
            ret_dict.update({val: model})
        return ret_dict

    @staticmethod
    def sum_of_field(models: Iterable[SapioRecord], field_name: str) -> float:
        """
        Sum up the numeric value of a given field across all input models. Excepts that all given models have a value.
        If the field is an integer field, the value will be converted to a float.
        :param models: The models to calculate the sum of.
        :param field_name: The name of the numeric field to sum.
        :return: The sum of the field values for the collection of models.
        """
        field_sum: float = 0
        for model in models:
            field_sum += float(model.get_field_value(field_name))
        return field_sum

    @staticmethod
    def mean_of_field(models: Iterable[SapioRecord], field_name: str) -> float:
        """
        Calculate the mean of the numeric value of a given field across all input models. Excepts that all given models
        have a value. If the field is an integer field, the value will be converted to a float.
        :param models: The models to calculate the mean of.
        :param field_name: The name of the numeric field to mean.
        :return: The mean of the field values for the collection of models.
        """
        return RecordUtil.sum_of_field(models, field_name) / len(list(models))

    @staticmethod
    def get_newest_record(records: Iterable[SapioRecord]) -> SapioRecord:
        """
        Get the newest record from a list of records.
        :param records: The list of records.
        :return: The input record with the highest record ID. None if the input list is empty.
        """
        newest: Optional[SapioRecord] = None
        for record in records:
            if newest is None or record.record_id > newest.record_id:
                newest = record
        return newest

    @staticmethod
    def values_to_field_maps(field_name: str, values: Iterable[Any], existing_fields: Optional[List[Dict[str, Any]]] = None) \
            -> List[Dict[str, Any]]:
        """
        Add a list of values for a specific field to a list of dictionaries pairing each value to that field name.
        :param field_name: The name of the field that the values are from.
        :param values: A list of field values.
        :param existing_fields: An optional existing fields map list to add the new values to. Values are added in the
          list in the same order that they appear. If no existing fields are provided, returns a new fields map list.
        :return: A fields map list that contains the given values mapped by the given field name.
        """
        # Update the existing fields map list if one is given.
        if existing_fields:
            values = list(values)
            # The number of new values must match the length of the existing fields list.
            if len(values) != len(existing_fields):
                raise SapioException(f"Length of \"{field_name}\" values does not match the existing fields length.")
            for field, value in zip(existing_fields, values):
                field.update({field_name: value})
            return existing_fields
        # Otherwise, create a new fields map list.
        return [{field_name: value} for value in values]

    @staticmethod
    def get_linear_relationship(models: Iterable[RecordModel], path: RelationshipPath) \
            -> Dict[RecordModel, Optional[PyRecordModel]]:
        """
        Given a relationship path, travel the path starting from the input models. Returns the record at the end of the
        path, if any. The hierarchy must be linear and the relationship path must already be loaded.
        :param models: A list of record models.
        :param path: The relationship path to follow.
        :return: Each record model mapped to the record at the end of the path starting from itself. If the end of the
            path couldn't be reached, the record will map to None. The mapped record is an unwrapped PyRecordModel and
            must be wrapped by the caller.
        """
        ret_dict: Dict[RecordModel, Optional[PyRecordModel]] = {}
        path: List[Tuple[RelationshipPathDir, str]] = path.path
        for model in models:
            current: PyRecordModel = model if isinstance(model, PyRecordModel) else model.backing_model
            for direction, datatype in path:
                if current is None:
                    break
                if direction == RelationshipPathDir.CHILD:
                    current = current.get_child_of_type(datatype)
                elif direction == RelationshipPathDir.PARENT:
                    current = current.get_parent_of_type(datatype)
            ret_dict.update({model: current})
        return ret_dict

    @staticmethod
    def get_branching_relationship(models: Iterable[RecordModel], path: RelationshipPath) \
            -> Dict[RecordModel, List[PyRecordModel]]:
        """
        Given a relationship path, travel the path starting from the input models. Returns the records at the end of the
        path. The relationship path must already be loaded.
        :param models: A list of record models.
        :param path: The relationship path to follow.
        :return: Each record model mapped to the records at the end of the path starting from itself. If the end of the
            path couldn't be reached, the record will map to an empty list. The mapped records are unwrapped
            PyRecordModels and must be wrapped by the caller.
        """
        ret_dict: Dict[RecordModel, List[PyRecordModel]] = {}
        path: List[Tuple[RelationshipPathDir, str]] = path.path
        for model in models:
            current_search: List[PyRecordModel] = [model if isinstance(model, PyRecordModel) else model.backing_model]
            next_search: List[PyRecordModel] = []
            # Exhaust the records at each step in the path, then use those records for the next step.
            for direction, datatype in path:
                if len(current_search) == 0:
                    break
                for search in current_search:
                    if direction == RelationshipPathDir.CHILD:
                        next_search.extend(search.get_children_of_type(datatype))
                    elif direction == RelationshipPathDir.PARENT:
                        next_search.extend(search.get_parents_of_type(datatype))
                current_search = next_search
                next_search = []
            ret_dict.update({model: current_search})
        return ret_dict

    def __exhaust_query_pages(self, data_type_name: str, field: str, value_list: List[Any],
                              paging_criteria: Optional[DataRecordPojoPageCriteria],
                              page_limit: Optional[int]) \
            -> Tuple[List[DataRecord], Optional[DataRecordPojoPageCriteria]]:
        has_next_page: bool = True
        records: List[DataRecord] = []
        cur_page: int = 1
        while has_next_page and (not page_limit or cur_page < page_limit):
            page_result = self.dr_man.query_data_records(data_type_name, field, value_list, paging_criteria)
            paging_criteria = page_result.next_page_criteria
            has_next_page = page_result.is_next_page_available
            records.extend(page_result.result_list)
            cur_page += 1
        return records, paging_criteria

    def __exhaust_query_id_pages(self, data_type_name: str, id_list: List[int],
                                 paging_criteria: Optional[DataRecordPojoPageCriteria],
                                 page_limit: Optional[int]) \
            -> Tuple[List[DataRecord], Optional[DataRecordPojoPageCriteria]]:
        has_next_page: bool = True
        records: List[DataRecord] = []
        cur_page: int = 1
        while has_next_page and (not page_limit or cur_page < page_limit):
            page_result = self.dr_man.query_data_records_by_id(data_type_name, id_list, paging_criteria)
            paging_criteria = page_result.next_page_criteria
            has_next_page = page_result.is_next_page_available
            records.extend(page_result.result_list)
            cur_page += 1
        return records, paging_criteria

    def __exhaust_query_all_pages(self, data_type_name: str,
                                  paging_criteria: Optional[DataRecordPojoPageCriteria],
                                  page_limit: Optional[int]) \
            -> Tuple[List[DataRecord], Optional[DataRecordPojoPageCriteria]]:
        has_next_page: bool = True
        records: List[DataRecord] = []
        cur_page: int = 1
        while has_next_page and (not page_limit or cur_page < page_limit):
            page_result = self.dr_man.query_all_records_of_type(data_type_name, paging_criteria)
            paging_criteria = page_result.next_page_criteria
            has_next_page = page_result.is_next_page_available
            records.extend(page_result.result_list)
            cur_page += 1
        return records, paging_criteria
