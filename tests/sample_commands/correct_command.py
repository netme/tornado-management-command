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
