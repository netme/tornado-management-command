import argparse
import logging
import pkgutil

from tornado.log import enable_pretty_logging

import commands


class CommandRunner(object):

    _command_list = None

    def __init__(self, package):
        self.package = package

    @property
    def command_list(self):
        if not self._command_list:
            self._command_list = {}
            prefix = self.package.__name__ + "."
            for loader, name, ispkg in pkgutil.iter_modules(
                    self.package.__path__):
                self._command_list[name] = __import__(
                    prefix + name, fromlist="dummy")
        return self._command_list

    @property
    def argument_parser(self):
        parser = argparse.ArgumentParser(
            description='Runs a management command')
        subparsers = parser.add_subparsers(help='Command')
        parsers = {}
        for command, module in self.command_list.iteritems():
            try:
                description = module.Command.description
                arguments = module.Command.arguments
            except AttributeError as e:
                logging.error(e.message)
                continue

            parsers[command] = subparsers.add_parser(command, help=description)
            parsers[command].set_defaults(which=command)
            for name, parameters in arguments.iteritems():
                parsers[command].add_argument(name, **parameters)
        return parser

    def run(self):
        args = self.argument_parser.parse_args()
        command = self.command_list[args.which].Command()
        command.call(args)


if __name__ == "__main__":
    enable_pretty_logging()
    command_runner = CommandRunner(commands)
    command_runner.run()
