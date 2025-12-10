#! /usr/bin/env python
# SPDT-1: Create secure default Python webhook server.

import os

from sapiopylib.rest.WebhookService import WebhookConfiguration, WebhookServerFactory, AbstractWebhookHandler
from sapiopylib.rest.pojo.webhook.WebhookContext import SapioWebhookContext
from sapiopylib.rest.pojo.webhook.WebhookResult import SapioWebhookResult
from waitress import serve

from sapio.devtools.multitoool import MultiTool
from sapio.devtools.test_webhooks_health import TestWebhookServerConnection
from sapio.webhook.waters.generate_waters_input_file import WatersInputFileCreator

# SPDT-1: verify_sapio_cert should be true by default.
config: WebhookConfiguration = WebhookConfiguration(verify_sapio_cert=True, debug=False)

# SPDT-1: If the insecure environment variable is true, set verify_sapio_cert to false.
if os.environ.get('SapioWebhooksInsecure') == "True":
    config.verify_sapio_cert = False


class Ping(AbstractWebhookHandler):
    def run(self, context: SapioWebhookContext) -> SapioWebhookResult:
        return SapioWebhookResult(True, "Success!")


# Ping to see if the webhook server is running.
config.register('/ping', Ping)

# Check webhooks server connection
config.register('/test_webhooks_health', TestWebhookServerConnection)

config.register('/generate_waters_input_file', WatersInputFileCreator)


# Dev tools
config.register('/multitool', MultiTool)

app = WebhookServerFactory.configure_flask_app(app=None, config=config)


# Health check route. This is required for deployments to an apprunner.
@app.route("/ping")
def health_check():
    return "Alive!"


# Run this to run a local server.
if __name__ == '__main__':
    host = "0.0.0.0"
    # This port must match the EXPOSE value in the Dockerfile when deploying.
    port = 8090
    if os.environ.get('SapioWebhooksDebug') == "True":
        app.run(host=host, port=port, debug=True)
    else:
        serve(app, host=host, port=port)
