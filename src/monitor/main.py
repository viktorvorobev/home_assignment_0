# pragma: nocover

import argparse
import logging
import signal
import sys

import dotenv
import yaml

from monitor.monitor import Monitor
from monitor.serializers import MonitorSettings, DbConnectionSettings
from monitor.utils import logger


def parse_args():
    parser = argparse.ArgumentParser(description='Util to monitor and log state of websites')
    parser.add_argument('--settings', required=True, help='Path to settings.yaml file')
    parser.add_argument('--verbose', required=False, action='store_true',
                        help='Set logging level to DEBUG')
    parser.add_argument('--envfile', required=False, help='Path to environment file with credentials of postgres',
                        default='.test.env')
    return parser.parse_args()


def setup_shutdown(monitor: Monitor):
    def sig_handler(_signum, _stack_frame):
        monitor.stop()

    signal.signal(signalnum=signal.SIGINT, handler=sig_handler)


def main():
    # I don't really want to pull here neither YAML, nor pydantic exceptions
    # pylint: disable = broad-exception-caught
    args = parse_args()

    logger_level = logging.DEBUG if args.verbose else logging.INFO
    logger.setLevel(logger_level)

    try:
        with open(args.settings, 'r', encoding='utf-8') as settings_file:
            yaml_settings = yaml.load(stream=settings_file, Loader=yaml.Loader)
    except Exception as error:
        logger.error('Failed to read settings file. %s: %s', error.__class__.__name__, error)
        sys.exit(1)

    logger.debug('Parsed settings: %s', yaml_settings)

    dotenv.load_dotenv(args.envfile)

    try:
        settings = MonitorSettings(**yaml_settings)
    except Exception as error:
        logger.error('Failed to parse settings file. %s: %s', error.__class__.__name__, error)
        sys.exit(1)

    try:
        db_connection_settings = DbConnectionSettings()
    except Exception as error:
        logger.error('Failed to get DB connection settings. %s: %s', error.__class__.__name__, error)
        sys.exit(1)

    monitor = Monitor(settings=settings, db_connection_settings=db_connection_settings)
    setup_shutdown(monitor)

    monitor.run()


if __name__ == '__main__':
    main()
