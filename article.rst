Advanced management commands in Tornado
=======================================

.. contents:: 
   :depth: 2

Introduction
^^^^^^^^^^^^

Tornado is a Python web framework and asynchronous networking library, 
originally developed at FriendFeed. It is lean, flexibe and perfectly fits
for small projects. By using non-blocking network I/O, Tornado can perfectly
serve a large amount of requests. 

Sometimes, then the project starts to grow, it becomes necessary to provide 
utilities which are utilizing the existing project's libraries, but for some
reasons should be started from the terminal or like a cron job. Tornado 
provides a library called `tornado.options` which helps to provide additional 
configuration parameters for the projects via settings file or via command line
arguments. 

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
the user should either create a separate script for every command, or should 
deal with the long list of parameters used by different commands. 
Unfortunately, it was not optimal for us. 

First, we have looked on existing solutions. A quick recap:

* Using Django libraries for management commands by David Koblas
  (http://geekscrap.com/2010/02/integrate-tornado-in-django/). The solution
  itself is not bad, but we decided not to add one more web framework to our 
  requirement list. 

* Stuart Marsh provided a bit cleaner solution in his library `tornado-cli` 
  (https://github.com/beardygeek/tornado-cli/). But we have found few issues
  why we should not use it. First of all this library is not supported since
  2011. Second, it uses deprecated Python libraries like `optparse`. Third, all
  commands should be declared in advance, which makes adding new commands
  more complex. Third, we didn't like the way to declare command arguments. 


Our solution
^^^^^^^^^^^^

Finally, we have decided to create our own management command runner. The
original idea of code structure was taken from the Django framework, their
management commands are implemented nice way. We have agreed on the following
module structure:

::
    
    commands
    |-__init__.py
    |-command1.py
    |-command2.py
    |...
    scripts.py


Each command is stored inside the `commands` module. The `commands` module also
contains the base class for each command - `BaseCommand`:

::
    
    # commands/__init__.py

    class BaseCommand(object):

        description = ""
        arguments = {}

        def call(self, arguments):
            pass


Each command should be inherited from the class `BaseCommand` and override at
least the `call` method. The `description` attribute should store the in-line 
help. Let's look on the code of a simple `hello_world` command:

::
    
    # commands/hello_world.py

    from commands import BaseCommand


    class Command(BaseCommand):

        description = "Prints Hello World!"

        def call(self, arguments):
            print("Hello world!")


We have decided to use `argparse` from the standard library for argument
management. All possible command arguments are stored inside a dict
`arguments`:

::

    arguments = {
        '--name': {
            'help': 'The user name',
            'metavar': 'John',
            'type': str,
            'required': True
        }
    }

When the command runs all argument values are passed to the `call` method. This
is the source code of the `hello_user` command which prints "Hello" to the user
specified via the parameter `--name`:

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

To run the commands, we created script called `manage.py`. This scipts is using
Python's `pkgutil` standard module to get a list of all possible commands from
the `commands` module:

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

As a next step, we have to form the list of possible script arguments. The
`argparse` module provides nice mechanism called `subparsers`. We decided to
create a subparser for every command to keep it's arguments in a separate
scope:

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
                    if not issubclass(module.Command, commands.BaseCommand):
                        continue
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


Here is the `scripts.py` source code:

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
                    if not issubclass(module.Command, commands.BaseCommand):
                        continue
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


Testing
^^^^^^^

Management command testing is quite tricky topic. First of all, command runner
itself should be tested. The main challenge here in testing is that we cannot
stick to the existing command list. In the beginning project can have zero 
commands, but we have to be sure that command runner is working. We decided to
use special command set. One command should have incorrect class  name, another
one should be correct and the third one should introduce some additional 
parameters. All commands for testing should be isolated in their own module
called `tests.sample_commands` . 

::

    # tests/sample_commands/command_with_wrong_classname.py
    from commands import BaseCommand


    class WrongCommand(BaseCommand):

        description = 'Help message for Wrong Command'
        arguments = {
            '--user_id': {
                'type': int,
                'help': 'User ID'
            }
        }

        def call(self, args):
            pass


    # tests/sample_commands/correct_command.py
    from commands import BaseCommand


    class Command(BaseCommand):

        description = 'Help message for Correct Command'
        arguments = {
            '--user_id': {
                'type': int,
                'help': 'User ID'
            }
        }

        def call(self, args):
            pass

    # tests/sample_commands/command_with_few_parameters.py
    from commands import BaseCommand


    class Command(BaseCommand):

        description = 'Help message for Command with Few Parameters'
        arguments = {
            '--user_id': {
                'type': int,
                'help': 'User ID'
            },
            '--password': {
                'type': str,
                'help': 'Password'
            }
        }

        def call(self, args):
            pass


The main test strategy for the command runner is:

* Test that all commands are appearing in the `command_list`
* Test that only correct commands are displayed in command help message
* Test that each correct command has its own parameter context

Here is the source code of the command runner test class:

::

    # tests/test_commands.py
    import unittest
    ...
    from manage import CommandRunner
    from tests import sample_commands


    class CommandRunnerTest(unittest.TestCase):

        def setUp(self):
            self.runner = CommandRunner(sample_commands)

        def test_command_list(self):
            generated_list = self.runner.command_list
            original_list = {
                'command_with_few_parameters': (
                    sample_commands.command_with_few_parameters),
                'correct_command': sample_commands.correct_command,
                'command_with_wrong_classname': (
                    sample_commands.command_with_wrong_classname)
            }

            for name in original_list.keys():
                self.assertEqual(original_list[name], generated_list[name])

        def test_command_list_in_help_message(self):
            parser = self.runner.argument_parser
            message = parser.format_help()
            self.assertIn('command_with_few_parameters', message)
            self.assertIn('correct_command', message)
            self.assertNotIn('command_with_wrong_classname', message)
            self.assertIn('Help message for Command with Few Parameters', message)
            self.assertIn('Help message for Correct Command', message)
            self.assertNotIn('Help message for Wrong Command', message)

        def test_awesome_command_parameters(self):
            parser = self.runner.argument_parser
            arguments = parser.parse_args(['command_with_few_parameters'])
            self.assertEqual(arguments.which, 'command_with_few_parameters')
            parameters = dir(arguments)
            self.assertIn('user_id', parameters)
            self.assertIn('password', parameters)

        def test_correct_command_parameters(self):
            parser = self.runner.argument_parser
            arguments = parser.parse_args(['correct_command'])
            self.assertEqual(arguments.which, 'correct_command')
            parameters = dir(arguments)
            self.assertIn('user_id', parameters)
            self.assertNotIn('password', parameters)
        ...


To test real commands, we need to capture `stdout` and `stderr`. Let's create a 
base class for real command tests:

::

    # tests/test_commands.py
    import sys
    import unittest

    from StringIO import StringIO

    import commands
    from manage import CommandRunner
    ...

    class RealCommandTestBase(unittest.TestCase):

        def setUp(self):
            self.saved_stdout = sys.stdout
            self.saved_stderr = sys.stderr
            self.out = StringIO()
            self.errors = StringIO()
            sys.stdout = self.out
            sys.stderr = self.errors

            self.runner = CommandRunner(commands)
            self.parser = self.runner.argument_parser

        def tearDown(self):
            sys.stdout = self.saved_stdout
            sys.stderr = self.saved_stderr
    ...


All output from `stdout` and `stderr` will be captured into `out` and `errors`
attributes of the test class. To test `hello_world` command we need to run the 
command and check 'Hello world!' in the `stdout`:

::

    # tests/test_commands.py
    ...

    class HelloWorldCommandTest(RealCommandTestBase):

        def test_command_output(self):
            arguments = self.parser.parse_args(['hello_world'])
            command = self.runner.command_list[arguments.which].Command()
            command.call(arguments)
            output = self.out.getvalue().strip()
            self.assertEqual(output, 'Hello world!')
    ...


Testing `hello_user` is a bit more tricky. We need to check the correct 
command behaviour when the `--name` parameter is set, and we also need to check
proper error handling if this parameter is missing:


::

    # tests/test_commands.py
    ...
    class HelloUserCommandTest(RealCommandTestBase):

        def test_command_output(self):
            arguments = self.parser.parse_args(['hello_user', '--name=John'])
            command = self.runner.command_list[arguments.which].Command()
            command.call(arguments)
            output = self.out.getvalue().strip()
            self.assertEqual(output, 'Hello John!')

        def test_name_parameter_required(self):
            with self.assertRaises(SystemExit):
                self.parser.parse_args(['hello_user'])
            output = self.errors.getvalue().strip()
            self.assertIn('--name is required', output)


Sometimes commands can generate db records, files and other data, but we will
not cover these topics in scope of this article.

Conclusion
^^^^^^^^^^

This approach helped us to organize our growing collection of management 
commands for our Tornado-based project. As long as we tried to use system
modules, we've got a framework independent solution which can be used in any
Python 2.7+ project. 

Have fun with management commands! 


Links
^^^^^
* http://tornado.readthedocs.org/en/latest/options.html
* http://geekscrap.com/2010/02/integrate-tornado-in-django/
* https://github.com/beardygeek/tornado-cli
