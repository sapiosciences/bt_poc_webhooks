import io
from typing import Optional, Tuple, Dict

from sapiopylib.rest.pojo.webhook.ClientCallbackRequest import MultiFilePromptRequest, MultiFileRequest
from sapiopylib.rest.pojo.webhook.ClientCallbackResult import AbstractClientCallbackResult, MultiFilePromptResult
from sapiopylib.rest.pojo.webhook.WebhookResult import SapioWebhookResult

from sapio.utils.data_type_models import AttachmentModel


def request_csv_files(client_callback: AbstractClientCallbackResult, title: str, error: str) \
        -> Tuple[Optional[SapioWebhookResult], Optional[Dict[str, bytes]]]:
    if client_callback and client_callback.user_cancelled:
        return SapioWebhookResult(True), None

    if not isinstance(client_callback, MultiFilePromptResult):
        prompt = MultiFilePromptRequest(dialog_title=title, file_extension="")
        return SapioWebhookResult(True, client_callback_request=prompt, display_text=error), None

    result: MultiFilePromptResult = client_callback
    for file_path in result.files.keys():
        file_bytes = result.files.get(file_path)
        if file_path is None or len(file_path) == 0 or file_bytes is None or len(file_bytes) == 0:
            return SapioWebhookResult(False, display_text="Empty files provided or files unable to be read."), None
    return None, result.files


def create_attachments(self, files_data_dict: Dict[str, bytes]):
    """
    Function to create attachment records using passed file name to data dict
    """
    new_attachments = []
    for filename, file_bytes in files_data_dict.items():
        attachment_record = self.data_record_manager.add_data_record(AttachmentModel.DATA_TYPE_NAME.__str__())
        attachment_record.set_field_value(AttachmentModel.ATTACHMENTID__FIELD_NAME.__str__(), filename)
        attachment_record.set_field_value(AttachmentModel.FILEPATH__FIELD_NAME.__str__(), filename)
        self.data_record_manager.set_attachment_data(attachment_record, filename, io.BytesIO(file_bytes))
        new_attachments.append(attachment_record)
    self.data_record_manager.commit_data_records(new_attachments)
    return new_attachments


def create_attachment(self, file_name, file_bytes):
    """
      Function to create attachment record using passed file name and data dict
      """
    attachments = create_attachments(self, {file_name: file_bytes})
    return attachments[0]
