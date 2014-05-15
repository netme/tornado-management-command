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
