from sapiopycommons.eln.experiment_handler import ExperimentHandler
from sapiopylib.rest.pojo.webhook.WebhookContext import SapioWebhookContext
from sapiopylib.rest.pojo.webhook.WebhookResult import SapioWebhookResult

from webhook_handler import PocWebhookHandler


class MultiTool(PocWebhookHandler):
    def execute(self, context: SapioWebhookContext) -> SapioWebhookResult:
        return SapioWebhookResult(True)
