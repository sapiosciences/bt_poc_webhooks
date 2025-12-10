import json

import requests
from sapiopycommons.callbacks.callback_util import CallbackUtil
from sapiopycommons.eln.experiment_handler import ExperimentHandler
from sapiopylib.rest.pojo.webhook.WebhookContext import SapioWebhookContext
from sapiopylib.rest.pojo.webhook.WebhookResult import SapioWebhookResult

from sapio.utils.data_type_models import SampleModel, C_NanoporeSequencingRunDetailsModel
from webhook_handler import PocWebhookHandler


class CreateNanoporeExperiment(PocWebhookHandler):
    def execute(self, context: SapioWebhookContext) -> SapioWebhookResult:

        callback = CallbackUtil(context)
        response = None
        nanopore_rec = None
        try:
            samples = ExperimentHandler(context).get_step_models("Samples", SampleModel)
            if not samples:
                callback.ok_dialog("Error", "No samples found in the experiment.")
                return SapioWebhookResult(True)

            nanopore = ExperimentHandler(context).get_step_models("Nanopore Sequencing Run Details",
                                                                  C_NanoporeSequencingRunDetailsModel)
            nanopore_rec = nanopore[0] if nanopore else None
            if not nanopore_rec:
                callback.ok_dialog("Error", "No Nanopore Sequencing Run Details found in the experiment.")
                return SapioWebhookResult(True)
            if not nanopore_rec.get_C_DeviceId_field():
                callback.ok_dialog("Error", "No Device Id Nanopore Sequencing Run Details.")
                return SapioWebhookResult(True)
            if not nanopore_rec.get_C_FlowCellId_field():
                callback.ok_dialog("Error", "No Flow Cell Product Code Nanopore Sequencing Run Details.")
                return SapioWebhookResult(True)

            nanopore_rec.set_C_SampleId_field(samples[0].get_SampleId_field())

            response = test_api_call_using_api_key(context, nanopore_rec, samples[0])
            print("Response : " + response.text)

        except Exception as e:
            if str(e).__contains__("failed to start") or str(e).__contains__(
                    "Cannot change output directories while acquiring data"):
                callback.ok_dialog("Error",
                                   "Experiment might be already running for this sample (library) in Nanopore.\n\n" + str(
                                       e))
            else:
                callback.ok_dialog("Error", str(e))
                return SapioWebhookResult(True)

        if response is None:
            return SapioWebhookResult(True, display_text="Webhook handling not found for testing this external system.")

        if response.status_code == 200:

            data = json.loads(response.text)
            run_id = data["run_id"]

            nanopore_rec.set_C_RunId_field(run_id)

            self.rec_model_manager.store_and_commit()

            callback.ok_dialog("SUCCESS", "Successfully created experiment in MinKnow")
        else:
            callback.ok_dialog("Error",
                               "Failed to establish connection. "
                               + "\n Response received :" + response.text)
        return SapioWebhookResult(True)


def test_api_call_using_api_key(context, rec, s):
    device_id = rec.get_C_DeviceId_field()
    url = f"http://192.168.0.106:28500/ruo/start-experiment?device_id={device_id}"

    payload = json.dumps({
        "add_experiment_group_hash": True,
        "barcodes": [
            {
                "alias": "alias01",
                "barcode": "barcode01",
                "passenger_info": {}
            }
        ],
        "barcoding_kit": "SQK-RBK004",
        "experiment_duration": "0.05",
        "experiment_group_id": str(context.eln_experiment.notebook_experiment_id),
        "experiment_group_prefix": "POC_",
        "experiment_group_suffix": "_SAPIO",
        "library_id": s.get_SampleId_field(),
        "output_arguments": {
            "fastq": "on",
            "fastq_reads_per_file": 2000
        },
        "position": {
            "position_id": "MS00000",
            "position_key_type": "position_id"
        },
        "protocol": {
            "experiment_type": 0,
            "flow_cell_product_code": rec.get_C_FlowCellId_field(),
            "sequencing_kit": "SQK-RBK004",
            "identifier_starts_with": "USER:"
        },
        "protocol_configurations": [
            "--guppy_filename=dna_r9.4.1_450bps_fast.cfg"
        ]
    })

    headers = {
        'accept': 'application/json',
        'access_token': 'gelEevNurs',
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    return response
