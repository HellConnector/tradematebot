import argparse
import logging

from alembic.config import CommandLine, Config


def run():
    logging.basicConfig(level=logging.DEBUG)

    alembic = CommandLine()
    alembic.parser.formatter_class = argparse.ArgumentDefaultsHelpFormatter
    options = alembic.parser.parse_args()

    config = Config(file_=options.config, ini_section=options.name, cmd_opts=options)
    alembic.run_cmd(config, options)
    exit()


if __name__ == "__main__":
    run()
