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
