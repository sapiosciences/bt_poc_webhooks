import json

import requests
from sapiopycommons.callbacks.callback_util import CallbackUtil
from sapiopycommons.general.popup_util import PopupUtil
from sapiopylib.rest.pojo.webhook.WebhookContext import SapioWebhookContext
from sapiopylib.rest.pojo.webhook.WebhookResult import SapioWebhookResult

from webhook_handler import PocWebhookHandler


class GetExperimentStatus(PocWebhookHandler):
    def execute(self, context: SapioWebhookContext) -> SapioWebhookResult:

        try:
            response = execute_call(context)
            print("Response : " + response.text)

        except Exception as e:
            return PopupUtil.display_ok_popup("Error", str(e))

        if response is None:
            return SapioWebhookResult(True, display_text="Webhook handling not found for testing this external system.")

        if response.status_code == 200:

            data = json.loads(response.text)
            protocol_status = data["protocol_status"]
            run_time = data["elapsed_run_time"]

            CallbackUtil(context).ok_dialog("Nanopore Response" ,f"EXPERIMENT STATUS - {protocol_status}\n\nELAPSED RUM TIME - {run_time}")
        else:
            CallbackUtil(context).ok_dialog("Error",
                                              "Failed to establish connection. "
                                              + "\n Response received :" + response.text)
        return SapioWebhookResult(True)


def execute_call(context):

    run_id = context.data_record.get_field_value("C_RunId")

    url = f"http://192.168.0.106:28500/ruo/experiment-status?experiment_run_id={run_id}&device_id=m1"

    payload = {}
    headers = {
        'accept': 'application/json',
        'access_token': 'gelEevNurs'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    return response
