import requests
from sapiopycommons.general.popup_util import PopupUtil
from sapiopylib.rest.pojo.webhook.ClientCallbackResult import OptionDialogResult
from sapiopylib.rest.pojo.webhook.WebhookContext import SapioWebhookContext
from sapiopylib.rest.pojo.webhook.WebhookResult import SapioWebhookResult

from sapio.utils.data_type_models import C_OutboundCommunicationConfigModel
from sapio.webhook.integrations.config_ids import ConfigIds
from webhook_handler import PocWebhookHandler


class TestConnectionButton(PocWebhookHandler):
    def execute(self, context: SapioWebhookContext) -> SapioWebhookResult:

        client_callback = context.client_callback_result
        if isinstance(client_callback, OptionDialogResult):
            if client_callback.button_text is None or client_callback.button_text == 'OK':
                return SapioWebhookResult(True)
        if not context.data_record:
            return SapioWebhookResult(False, display_text="No config found")

        config = self.instance_manager.add_existing_record_of_type(context.data_record,
                                                                   C_OutboundCommunicationConfigModel)
        config_id = config.get_C_ConfigId_field()
        try:
            # SGIMED
            if config_id == ConfigIds.HUMMINGBIRD.value:
                response = test_api_call_using_api_key(config)

            # add handling for other integrations in future as required
            else:
                response = test_api_call_using_api_key(config)  # placeholder test call for new integrations
        except Exception as e:
            return PopupUtil.display_ok_popup("Error", str(e))

        if response is None:
            return SapioWebhookResult(True, display_text="Webhook handling not found for testing this external system.")

        if response.status_code == 200:
            self.logger.info("Test Connection: Successfully established connection with " + config_id)
            return PopupUtil.display_ok_popup("SUCCESS",
                                              "Successfully established connection with " + config_id)
        else:
            self.logger.info("Test Connection: Failed to establish connection with "
                             + config_id + ".\n Response received :" + response.text)
            return PopupUtil.display_ok_popup("Error",
                                              "Failed to establish connection with "
                                              + config_id + ".\n Response received :" + response.text)


def test_api_call_using_api_key(config):
    api_key = config.get_C_WebServiceApiKey_field()
    if not api_key:
        raise Exception("API Key value is blank. Please enter it using 'Change API Key' button as Admin")
    headers = {
        'accept': 'application/json',
        'Authorization': 'Bearer ' + api_key,
    }
    webservice_url = config.get_C_WebServiceUrl_field()
    endpoint = config.get_C_TestingEndpoint_field()
    if endpoint:
        webservice_url = (webservice_url if webservice_url else "") + endpoint
    return requests.get(url=webservice_url, headers=headers)
