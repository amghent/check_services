import logging.config
import os
import socket
import smtplib

import psutil
import yaml

from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path


APP_NAME: str = ""
APP_VERSION: str = ""

CURRENT_DIR: Path = Path(__file__).parent
MACHINE_NAME: str = ""

LOGGER = logging.getLogger(APP_NAME)


def configure_logger():
    with open(os.path.join(CURRENT_DIR, "logging.yaml"), "r") as config_file:
        config_data = yaml.safe_load(config_file.read())

        logging.config.dictConfig(config_data)
        logging.basicConfig(level=logging.NOTSET)


def read_config():
    global APP_NAME, APP_VERSION

    with open(os.path.join(CURRENT_DIR, "config.yaml"), "r") as config_file:
        config_data = yaml.safe_load(config_file)

    APP_NAME = config_data["name"]
    APP_VERSION = config_data["version"]

    title = f"{APP_NAME.upper()} v.{APP_VERSION}"

    LOGGER.info(len(title) * "_")
    LOGGER.info(title)
    LOGGER.info(len(title) * "_")

    return config_data


def log_dirs():
    LOGGER.info(f"Current directory: {CURRENT_DIR} ")


def get_machine_name():
    global MACHINE_NAME

    MACHINE_NAME = socket.gethostname()

    LOGGER.info(f"This machine's name: {MACHINE_NAME}")

    return True


def check_services(config_data):
    services = []

    for service in config_data["services"]:
        LOGGER.info(f"Checking service '{service}'")

        service_info = psutil.win_service_get(service)

        if service_info.status().lower() != "running":
            LOGGER.warning(f"Service '{service}' is NOT RUNNING")

            services.append(service)
        else:
            LOGGER.info(f"Service '{service}' OK")

    return len(services) == 0, services


def notify(config_data, services):
    assert config_data is not None
    assert type(services) is not str

    try:
        with smtplib.SMTP(host=config_data["mail"]["server"], port=int(config_data["mail"]["port"])) as server:
            msg = MIMEMultipart()

            msg["subject"] = Header(config_data["mail"]["subject"])
            msg["from"] = Header(config_data["mail"]["from"])
            msg["to"] = Header(config_data["mail"]["to"])

            body = f"{config_data['mail']['text']}: {MACHINE_NAME}\n\n"
            body += f"{config_data['mail']['list_text']}:\n"

            for service in services:
                body += f"- {service}\n"

            msg.attach(MIMEText(body, "plain"))

            server.send_message(msg=msg)

            LOGGER.info(f"Notifying {msg['to']} that one or more services are down")

    except Exception as err:
        LOGGER.error(f"Could not notify people because of a mail server error: {err}")


def run(config_data):
    get_machine_name()

    check_ok, services = check_services(config_data=config_data)

    if not check_ok:
        notify(config_data=config_data, services=services)


def main():
    configure_logger()
    config_data = read_config()
    log_dirs()

    run(config_data=config_data)


if __name__ == "__main__":
    main()
