from flask import Blueprint

# Reserved for the Mealie recipe-action trigger endpoint.
#
# The exact request shape Mealie sends (GET link opened in the browser vs.
# a server-to-server POST webhook) needs to be verified against a real
# Mealie instance when the first triggering feature is fed into the BDD
# workflow (see AGENTS.md). No routes are registered yet.
webhook_bp = Blueprint("webhook", __name__)
