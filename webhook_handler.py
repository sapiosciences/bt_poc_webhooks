import traceback
from abc import abstractmethod
from logging import Logger
from typing import List, Dict

import waitress.utilities
from sapiopylib.rest.DataRecordManagerService import DataRecordManager
from sapiopylib.rest.ELNService import ElnManager
from sapiopylib.rest.WebhookService import AbstractWebhookHandler
from sapiopylib.rest.pojo.DataRecord import DataRecord
from sapiopylib.rest.pojo.eln.ExperimentEntry import ExperimentEntry
from sapiopylib.rest.pojo.webhook.VeloxRules import ElnEntryRecordResult, VeloxRuleType
from sapiopylib.rest.pojo.webhook.WebhookContext import SapioWebhookContext
from sapiopylib.rest.pojo.webhook.WebhookResult import SapioWebhookResult
from sapiopylib.rest.utils.recordmodel.RecordModelManager import RecordModelManager, RecordModelInstanceManager


class PocWebhookHandler(AbstractWebhookHandler):
    """
    The class that all webhook endpoints should extend. Wraps the execute command in a try/except to capture
    any runtime errors and report them to the user.
    """
    logger: Logger = waitress.utilities.logger
    data_record_manager: DataRecordManager
    eln_manager: ElnManager
    exp_id: int
    rec_model_manager: RecordModelManager
    instance_manager: RecordModelInstanceManager

    def run(self, context: SapioWebhookContext) -> SapioWebhookResult:
        self.data_record_manager = context.data_record_manager
        self.eln_manager = context.eln_manager
        self.rec_model_manager = RecordModelManager(context.user)
        self.instance_manager = self.rec_model_manager.instance_manager

        if context.eln_experiment:
            self.exp_id = context.eln_experiment.notebook_experiment_id
        try:
            return self.execute(context)
        except SapioDisplayedException as e:
            self.log_error(context, e.args[0])
            return SapioWebhookResult(False, display_text=e.args[0])
        except Exception:
            self.logger.error("Error ({user:s}):\n{trc:s}"
                              .format(user=context.user.username, trc=traceback.format_exc()))
            return SapioWebhookResult(False, display_text="Error occurred during webhook execution.")

    def log_error(self, context: SapioWebhookContext, msg: str):
        self.logger.error("Error ({user}, {exp}):\n{trc}"
                          .format(user=context.user.username, exp=self.exp_id, trc=msg))

    @abstractmethod
    def execute(self, context: SapioWebhookContext) -> SapioWebhookResult:
        pass

    def get_data_records_for_entry(self, entry: ExperimentEntry) -> List[DataRecord]:
        """
        Shorthand for getting the data records from the given entry.
        """
        return self.eln_manager.get_data_records_for_entry(self.exp_id, entry.entry_id).result_list

    @staticmethod
    def parse_eln_rule_to_dict(context: SapioWebhookContext) -> Dict[str, List[DataRecord]]:
        """
        Parse the velox eln rule result down into a simple dict of data type to list of data records.
        """
        ret_dict: Dict[str, List[DataRecord]] = {}
        # Mapping entry name to results from the entry.
        rule_result_map: Dict[str, List[ElnEntryRecordResult]] = context.velox_eln_rule_result_map
        for entry in rule_result_map:
            # The results for this entry.
            record_results: List[ElnEntryRecordResult] = rule_result_map.get(entry)
            for record_result in record_results:
                # The list of records for this result, including the record of the ID above.
                result_list = record_result.rule_result_list
                for result in result_list:
                    rule_type: VeloxRuleType = result.velox_rule_type
                    data_type: str = rule_type.data_type_name

                    records: List[DataRecord] = ret_dict.get(data_type)
                    if records is None:
                        records = []

                    if data_type == "ELNExperimentDetail":
                        records.extend(result.data_records)
                    else:
                        for record in result.data_records:
                            if record.data_type_name == data_type and not records.__contains__(record):
                                records.append(record)
                    ret_dict.update({data_type: records})

        return ret_dict

    @staticmethod
    def parse_eln_rule_to_dict_by_entry(context: SapioWebhookContext) -> Dict[str, Dict[str, List[DataRecord]]]:
        """
        Parse the velox eln rule result down into a dict of entry names to a dict of data type to list of data records.
        """
        ret_dict: Dict[str, Dict[str, List[DataRecord]]] = {}
        # Mapping entry name to results from the entry.
        rule_result_map: Dict[str, List[ElnEntryRecordResult]] = context.velox_eln_rule_result_map
        for entry in rule_result_map:
            # The results for this entry.
            record_results: List[ElnEntryRecordResult] = rule_result_map.get(entry)
            entry_dict: Dict[str, List[DataRecord]] = {}
            for record_result in record_results:
                # The list of records for this result, including the record of the ID above.
                result_list = record_result.rule_result_list
                for result in result_list:
                    rule_type: VeloxRuleType = result.velox_rule_type
                    data_type: str = rule_type.data_type_name

                    records: List[DataRecord] = entry_dict.get(data_type)
                    if records is None:
                        records = []

                    if data_type == "ELNExperimentDetail":
                        records.extend(result.data_records)
                    else:
                        for record in result.data_records:
                            if record.data_type_name == data_type and not records.__contains__(record):
                                records.append(record)
                    entry_dict.update({data_type: records})
                ret_dict.update({entry: entry_dict})

        return ret_dict


class SapioDisplayedException(Exception):
    """
    An exception which returns its error text as display test in SapioWebhookResult.
    All other exceptions return a generic "Error occurred during webhook execution" message.
    """
    pass
