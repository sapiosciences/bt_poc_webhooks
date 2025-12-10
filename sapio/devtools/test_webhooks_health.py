from sapiopylib.rest.DataMgmtService import DataMgmtServer
from sapiopylib.rest.pojo.webhook.WebhookContext import SapioWebhookContext
from sapiopylib.rest.pojo.webhook.WebhookResult import SapioWebhookResult
from sapiopylib.rest.pojo.DataRecord import DataRecord

from sapio.utils.data_type_models import ExemplarConfigModel
from webhook_handler import PocWebhookHandler


class TestWebhookServerConnection(PocWebhookHandler):
    def execute(self, context: SapioWebhookContext) -> SapioWebhookResult:
        exemplar_configs = context.data_record_manager.query_all_records_of_type(ExemplarConfigModel.DATA_TYPE_NAME.__str__()).result_list

        exemplar_config: DataRecord = None
        if exemplar_configs:
            exemplar_config = exemplar_configs[0]

        if exemplar_config is None:
            return SapioWebhookResult(True, display_text="Your Exemplar Config was not available !")

        record_id = exemplar_config.get_field_value("RecordId")
        data_type_name = exemplar_config.get_data_type_name()
        display_name = DataMgmtServer.get_data_type_manager(context.user).get_data_type_definition(
            data_type_name).__str__()

        return SapioWebhookResult(True, display_text="Test Button! Your Config has a Display Name: "
                                                     + display_name + ", and a Record ID: " + str(record_id))
