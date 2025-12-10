import time
from datetime import datetime
from typing import Optional, List

from natsort import natsorted, ns
from sapiopylib.rest.pojo.DataRecord import DataRecord
from sapiopylib.rest.pojo.eln.ElnExperiment import ElnExperimentUpdateCriteria
from sapiopylib.rest.pojo.eln.ExperimentEntry import ExperimentEntry
from sapiopylib.rest.pojo.eln.ExperimentEntryCriteria import AbstractElnEntryUpdateCriteria, \
    ElnPluginEntryUpdateCriteria, ElnTableEntryUpdateCriteria
from sapiopylib.rest.pojo.eln.SapioELNEnums import ExperimentEntryStatus, ElnExperimentStatus
from sapiopylib.rest.pojo.webhook.WebhookContext import SapioWebhookContext

from sapio.tags.entry_tags import CommonTags
from sapio.utils.data_type_models import SampleModel


def get_entry_by_option(context: SapioWebhookContext, option: str,
                        entry_list: Optional[List[ExperimentEntry]] = None) -> Optional[ExperimentEntry]:
    """
    Get the first entry in the context with the given entry option key, or None if no entry hsa that name.
    Providing the entry list avoids additional calls if one needs multiple entries from an experiment.
    """
    eln_manager = context.eln_manager
    exp_id = context.eln_experiment.notebook_experiment_id
    if entry_list is None:
        entry_list = eln_manager.get_experiment_entry_list(exp_id, False)

    for entry in entry_list:
        if eln_manager.get_experiment_entry_options(exp_id, entry.entry_id).keys().__contains__(option):
            return entry
    return None


def get_entries_by_option(context: SapioWebhookContext, option: str,
                          entry_list: Optional[List[ExperimentEntry]] = None) -> list[ExperimentEntry]:
    eln_manager = context.eln_manager
    exp_id = context.eln_experiment.notebook_experiment_id
    if entry_list is None:
        entry_list = eln_manager.get_experiment_entry_list(exp_id, False)

    matching_entries = []
    for entry in entry_list:
        if eln_manager.get_experiment_entry_options(exp_id, entry.entry_id).keys().__contains__(option):
            matching_entries.append(entry)
    return matching_entries


def get_current_date_in_format(date_format: str) -> str:
    now = datetime.now()
    date: str = now.strftime(date_format)
    return date


def initialize_entry(entry: ExperimentEntry, context: SapioWebhookContext):
    exp_id = context.eln_experiment.notebook_experiment_id
    update_crit = AbstractElnEntryUpdateCriteria(entry.entry_type)
    update_crit.order = entry.order
    update_crit.template_item_fulfilled_timestamp = round(time.time() * 1000)
    context.eln_manager.update_experiment_entry(exp_id, entry.entry_id, update_crit)


def enableExperiment(context: SapioWebhookContext):
    update_crit = ElnExperimentUpdateCriteria()
    update_crit.new_experiment_status = ElnExperimentStatus.UnlockedChangesRequired
    context.eln_manager.update_notebook_experiment(context.eln_experiment.notebook_experiment_id, update_crit)


def enable_entry(context: SapioWebhookContext, entry: ExperimentEntry):
    update_crit = AbstractElnEntryUpdateCriteria(entry.entry_type)
    update_crit.entry_status = ExperimentEntryStatus.Enabled
    update_crit.template_item_fulfilled_timestamp = round(time.time() * 1000)
    context.eln_manager.update_experiment_entry(context.eln_experiment.notebook_experiment_id, entry.entry_id,
                                                update_crit)


def disable_entry(context: SapioWebhookContext, entry: ExperimentEntry):
    update_crit = AbstractElnEntryUpdateCriteria(entry.entry_type)
    update_crit.entry_status = ExperimentEntryStatus.Disabled
    update_crit.clear_template_item_fulfilled_timestamp = True
    context.eln_manager.update_experiment_entry(context.eln_experiment.notebook_experiment_id, entry.entry_id,
                                                update_crit)


def disable_plugin_entry(context: SapioWebhookContext, entry: ExperimentEntry):
    update_crit = ElnPluginEntryUpdateCriteria()
    update_crit.entry_status = ExperimentEntryStatus.Disabled
    update_crit.clear_template_item_fulfilled_timestamp = True
    context.eln_manager.update_experiment_entry(context.eln_experiment.notebook_experiment_id, entry.entry_id,
                                                update_crit)


def setPlatesFor3dPlatingStep(context: SapioWebhookContext, plates: List[DataRecord], plate_entry: ExperimentEntry,
                              plating_entry_options: dict[str, str]):
    values = (str(record.get_field_value("RecordId")) for record in plates if
              record.get_field_value("RecordId") is not None)
    values = sorted(values, reverse=True)
    plateIdString = ",".join(values)
    eln_manager = context.eln_manager
    update_crit = ElnPluginEntryUpdateCriteria()
    if plating_entry_options:
        update_crit.entry_options_map = plating_entry_options
    else:
        update_crit.entry_options_map = eln_manager.get_experiment_entry_options \
            (context.eln_experiment.notebook_experiment_id, plate_entry.entry_id)
    update_crit.entry_options_map.update({"MultiLayerPlating_Plate_RecordIdList": plateIdString})
    eln_manager.update_experiment_entry(context.eln_experiment.notebook_experiment_id, plate_entry.entry_id,
                                        update_crit)


def setPlateFor2dPlatingStep(context, plates: List[DataRecord], plate_entry: ExperimentEntry):
    plateIdString = ",".join(str(record.get_field_value("RecordId")) for record in plates
                             if record.get_field_value("RecordId") is not None)
    PLATE_IDS = ",".join(str(record.get_field_value("PlateId")) for record in plates
                         if record.get_field_value("PlateId") is not None)
    eln_manager = context.eln_manager
    update_crit = ElnPluginEntryUpdateCriteria()
    update_crit.entry_options_map = eln_manager.get_experiment_entry_options \
        (context.eln_experiment.notebook_experiment_id, plate_entry.entry_id)
    update_crit.entry_options_map.update({"USE EXISTING PLATE RECORD ID": plateIdString})
    update_crit.entry_options_map.update({"ACCESSION PLATE ID": PLATE_IDS})
    update_crit.entry_options_map.update({"ENTRY_SET_ACCESSIONED_PLATES": PLATE_IDS})
    eln_manager.update_experiment_entry(context.eln_experiment.notebook_experiment_id, plate_entry.entry_id,
                                        update_crit)


def update_table_entry_option(context, entry_options: dict[str, str], entry: ExperimentEntry):
    eln_manager = context.eln_manager
    update_crit = ElnTableEntryUpdateCriteria()
    update_crit.entry_options_map = eln_manager.get_experiment_entry_options \
        (context.eln_experiment.notebook_experiment_id, entry.entry_id)
    for key, value in entry_options.items():
        update_crit.entry_options_map.update({key: value})
    eln_manager.update_experiment_entry(context.eln_experiment.notebook_experiment_id, entry.entry_id,
                                        update_crit)


def remove_entry_option(context, entry, key):
    update_crit = ElnTableEntryUpdateCriteria()
    experiment_id = context.eln_experiment.notebook_experiment_id
    eln_manager = context.eln_manager
    update_crit.entry_options_map = eln_manager.get_experiment_entry_options(experiment_id, entry.entry_id)
    if key in update_crit.entry_options_map:
        del update_crit.entry_options_map[key]
        eln_manager.update_experiment_entry(experiment_id, entry.entry_id, update_crit)


def get_96plate_well_positions_column_wise():
    well_positions = []
    for column in range(1, 13):
        for row in range(ord('A'), ord('H') + 1):
            well_positions.append(f'{chr(row)}{column}')
    return well_positions


def get_sorted_records_by_field(records, field_name):
    if not records:
        return list()
    sorted_records = natsorted(records, key=lambda rec: (
        rec.get_field_value(field_name)), alg=ns.IGNORECASE)
    return sorted_records


def get_field_value_list(records, field_name: str):
    value_list = list()
    for rec in records:
        if rec.get_field_value(field_name):
            value_list.append(rec.get_field_value(field_name))
    return value_list


def get_source_sample_entry_records(self, context, rule_term_context_entry_list):
    samples_entry = get_entry_by_option(context, option=CommonTags.SAMPLES_STEP,
                                        entry_list=rule_term_context_entry_list)
    samples: List[SampleModel] = list()
    if samples_entry:
        records: list[DataRecord] = self.eln_manager. \
            get_data_records_for_entry(self.exp_id,
                                       samples_entry.entry_id).result_list
        if records:
            samples = self.instance_manager.add_existing_records_of_type(records, SampleModel)
    return samples


def get_root_sample(parent_sample, relationship_manager):
    root_sample = None
    while parent_sample:
        root_sample = parent_sample
        relationship_manager.load_parents_of_type([parent_sample], SampleModel)
        s = parent_sample.get_parent_of_type(SampleModel)
        if s:
            parent_sample = s
        else:
            break
    return root_sample


def is_number(value):
    try:
        float(value)
        return True
    except ValueError:
        return False
