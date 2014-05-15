import sys
import unittest

from StringIO import StringIO

import commands
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


class HelloWorldCommandTest(RealCommandTestBase):

    def test_command_output(self):
        arguments = self.parser.parse_args(['hello_world'])
        command = self.runner.command_list[arguments.which].Command()
        command.call(arguments)
        output = self.out.getvalue().strip()
        self.assertEqual(output, 'Hello world!')


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
