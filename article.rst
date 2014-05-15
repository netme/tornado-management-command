Advanced management commands in Tornado
=======================================

Tornado is a Python web framework and asynchronous networking library, 
originally developed at FriendFeed. It is lean, flexibe and perfectly fits
for small projects. By using non-blocking network I/O, Tornado can perfectly
serve a large amount of requests. 

Sometimes, then the project starts to grow, it becomes necessary to provide 
utilities which are utilizing the existing project's libraries, but for some
reasons should be started from the terminal or like a cron job. For this case
Tornado provides a library called `tornado.options`. This library helps to
provide additional configuration parameters for the projects via configuration
file or via command line arguments. 

::

    from tornado.options import define, options

    define("mysql_host", default="127.0.0.1:3306", help="Main user DB")
    define("memcache_hosts", default="127.0.0.1:11011", multiple=True,
           help="Main user memcache servers")

    def connect():
        options.parse_command_line()
        db = database.Connection(options.mysql_host)
        ...

This approach is nice, but when the number of command-line utilities grows,
the user should either create a separate script runner for every command, or 
should deal with the long list of parameters used by different commands. 

To overcome this issues we have decided to create our own management command 
runner. The original idea of code structure was taken from Django framework, 
there management commands are implemented nice way. We have decided to stick to 
the following module structure:

::
    
    commands
    |-__init__.py
    |-command1.py
    |-command2.py
    |...
    manage.py


Each command is stored inside `commands` module. `commands` module also 
contains the base class for each command - `BaseCommand`:

::
    
    # commands/__init__.py

    class BaseCommand(object):

        description = ""
        arguments = {}

        def call(self, arguments):
            pass


Each command should be inherited from `BaseCommand` class and override at least
`call` method. To help the user understand what command is doing, it should be
a good practice to fill the `description` attribute with some general 
information. Let's look on the code of `hello_world` command:

::
    
    # commands/hello_world.py

    from commands import BaseCommand


    class Command(BaseCommand):

        description = "Prints Hello World!"

        def call(self, arguments):
            print("Hello world!")


As long, as Python 2.7+ has a library called `argparse`, we have decided
to use it for argument management. All possible command arguments are stored
inside `arguments` dict:

::

    arguments = {
        '--name': {
            'help': 'The user name',
            'metavar': 'John',
            'type': str,
            'required': True
        }
    }

When command runs all values are passed to the `call` method inside `arguments`
variable. This is the source code of `hello_user` command which prints "Hello"
to the user specified via `--name` parameter:

::

    # commands/hello_user.py

    from commands import BaseCommand


    class Command(BaseCommand):

        description = "Prints Hello World!"
        arguments = {
            '--name': {
                'help': 'The name of the user',
                'metavar': 'John',
                'type': str,
                'required': True
            }
        }

        def call(self, arguments):
            print("Hello %s!" % arguments.name)


Command runner
^^^^^^^^^^^^^^

To run the commands, we have a script called `manage.py`. This scipts is using
Python's `pkgutil` module to get a list of all possible commands from 
`commands` module:

::

    class CommandRunner:
        ...
        _command_list = None
        ...
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
        ...

As a next step, we have to form the list of possible script arguments. 
`argparse` module provides nice mechanism called `subparsers`. We are creating 
a subparser for every command to keep it's arguments in a separate scope:

::

    class CommandRunner:
        ...
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
        ...

`which` parameter of subparser helps us to understand which command was called.
To run the command, we need to parse all arguments, create an instance of the
proper `Command` class and call it, sending the list of the arguments:


::

    class CommandRunner:
        ...
        def run(self):
            args = self.argument_parser.parse_args()
            command = self.command_list[args.which].Command()
            command.call(args)


Here is the `manage.py` source code:

::

    # commands/hello_user.py

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


Conclusion
^^^^^^^^^^

This approach helped us to organize our growing collection of management 
commands for our Tornado project. As long as we tried to use system modules, 
we've got a framework independent solution which can be used in any Python 
2.7+ project. Have fun with management commands! 
