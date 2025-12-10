import io
from io import StringIO
from typing import List

from sapiopycommons.callbacks.callback_util import CallbackUtil
from sapiopycommons.files.file_bridge import FileBridge
from sapiopylib.rest.DataMgmtService import DataMgmtServer
from sapiopylib.rest.pojo.DataRecord import DataRecord
from sapiopylib.rest.pojo.webhook.WebhookContext import SapioWebhookContext
from sapiopylib.rest.pojo.webhook.WebhookResult import SapioWebhookResult
from sapiopylib.rest.utils.recordmodel.PyRecordModel import PyRecordModel
from sapiopylib.rest.utils.recordmodel.RecordModelManager import RecordModelManager

from sapio.utils.record_util import RecordUtil
from sapio.utils.waters_data_type_models import AttachmentModel, SBA_AssaySampleModel, SBA_MasterAssayRunModel, \
    InstrumentModel
from webhook_handler import PocWebhookHandler

# Constants
ATTACHMENT_TYPE = "Attachment"
RECORDS_PER_FILE = 96
FILE_NAME_PREFIX = "Waters_Demo_Input_file"


class WatersInputFileCreator(PocWebhookHandler):
    """Webhook handler for creating Waters input files from assay samples."""

    def execute(self, context: SapioWebhookContext) -> SapioWebhookResult:
        """Main entry point for the webhook."""
        # try:
        rec_man = RecordModelManager(context.user)
        inst_man = rec_man.instance_manager
        rel_man = rec_man.relationship_manager

        assay_run = inst_man.add_existing_record_of_type(context.data_record, SBA_MasterAssayRunModel)
        rel_man.load_children_of_type([assay_run], SBA_AssaySampleModel)

        sample_list = self.get_sorted_samples(assay_run)
        files = self.create_input_files(sample_list, assay_run, context)
        attachments = self.add_attachments_to_assay_run(inst_man, assay_run, files)

        rec_man.store_and_commit()

        file_datas = self.generate_file_dict(context, attachments)

        self.send_files_to_instrument(context, assay_run, file_datas)

        return SapioWebhookResult(True, display_text="Waters input files created successfully.")
        # except Exception as e:
        #     return SapioWebhookResult(False, display_text=f"Error creating Waters input files: {str(e)}")

    @staticmethod
    def get_sorted_samples(assay_run: SBA_MasterAssayRunModel) -> list[SBA_AssaySampleModel]:
        """Get sorted list of samples from the assay run."""
        return assay_run.get_children_of_type(SBA_AssaySampleModel)

    def create_input_files(self, samples: List[SBA_AssaySampleModel], assay_run: SBA_MasterAssayRunModel,
                           context: SapioWebhookContext) -> List[
        DataRecord]:
        """Create input files from the given samples."""
        newly_made_attachments = []
        run_id = assay_run.get_field_value("C_Waters_Run_Id")
        file_content = self.generate_file_content(samples, assay_run)
        file_name = f"{FILE_NAME_PREFIX}_{run_id}.csv"
        new_attachment = self.make_attachment(context.user, file_content.encode(), file_name)
        newly_made_attachments.append(new_attachment)

        return newly_made_attachments

    def generate_file_content(self, samples: List[SBA_AssaySampleModel], assay_run: SBA_MasterAssayRunModel) -> str:
        """Generate the content for a single input file."""
        output = StringIO()
        output.write(
            "worklistId,resultSetName,folder,processingMethod,ruleSet,instrumentSystem,sampleId,name,description,sampleType,injectionVolume,samplePosition,replicates,acqMethodId,runtime,level,quanReference,group,sampleFactor,comment\r\n")

        for index, sample in enumerate(samples, start=1):
            sample_fields = sample.fields
            run_id = assay_run.get_field_value("C_Waters_Run_Id")
            output.write(
                f"{run_id},LIMS Demo Result sets,,,,,{sample_fields['SBA_SampleId']},{sample_fields['SBA_OtherSampleId']},")
            if not sample_fields['SBA_IsControl']:
                output.write(f"Sample {index},Unknown,")
            else:
                output.write(
                    f"{sample_fields['SBA_ControlType']} - {sample_fields['SBA_OtherSampleId']},{sample_fields['SBA_ControlType']},")

            output.write(
                f"10,\"{sample_fields['SBA_PlateId']}:{sample_fields['SBA_RowPosition']},{sample_fields['SBA_ColPosition']}\",1,,,,FALSE,group1,")

            if 'SBA_DilutionFactor' in sample_fields:
                output.write(str(sample_fields['SBA_DilutionFactor']) if sample_fields['SBA_DilutionFactor'] else "")
            output.write("\r\n")

        return output.getvalue()

    @staticmethod
    def make_attachment(user, file_bytes: bytes, file_name: str) -> DataRecord:
        """Create an attachment record in the system."""
        attachment_fields = {
            "AttachmentId": file_name,
            "FilePath": file_name
        }
        data_record_manager = DataMgmtServer.get_data_record_manager(user)
        attachment = data_record_manager.add_data_record(ATTACHMENT_TYPE)
        attachment.set_fields(attachment_fields)
        data_record_manager.set_attachment_data(attachment, file_name, io.BytesIO(file_bytes))
        return attachment

    @staticmethod
    def add_attachments_to_assay_run(inst_man, assay_run: SBA_MasterAssayRunModel, files: List[DataRecord]) -> List[
        PyRecordModel]:
        """Add attachments to the assay run and mark it as complete."""
        attachments = inst_man.add_existing_records_of_type(files, AttachmentModel)
        assay_run.add_children(attachments)
        assay_run.set_SBA_IsPlatingComplete_field(True)
        return attachments

    def generate_file_dict(self, context, attachments):
        def consume_data(chunk: bytes):
            file_data.write(chunk)
        file_datas: dict[str, bytes] = {}
        for attachment in attachments:
            with io.BytesIO() as file_data:
                context.data_record_manager.get_attachment_data(attachment.get_data_record(), consume_data)
                file_data.flush()
                file_data.seek(0)
                file_bytes = file_data.read()
                file_datas[attachment.get_field_value("FilePath")] = file_bytes
        return file_datas

    def send_files_to_instrument(self, context, assay_run: SBA_MasterAssayRunModel, file_datas):
        # Get the instrument name.
        instrument_name: str = assay_run.get_SBA_Instrument_field()
        instruments = RecordUtil(context).query_models(InstrumentModel,
                                                       "InstrumentName",
                                                       [instrument_name])
        if not instruments:
            raise Exception(f"Instrument named {instrument_name} is NOT found in the system.")

        network_file_path = instruments[0].get_NetworkFilePath_field()
        if not network_file_path:
            raise Exception(f"Instrument named {instrument_name} doesn't have a network path.")

        for key in file_datas.keys():
            try:
                FileBridge.write_file(context, network_file_path, "Sapio/"+ key, file_datas[key])
            except Exception as e:
                CallbackUtil(context).write_file(key, file_datas[key])
                raise Exception(f"Unable to send files to the file bridge named {network_file_path}")
        return SapioWebhookResult(True, f"Files successfully sent to {instrument_name} FileBridge location.")
