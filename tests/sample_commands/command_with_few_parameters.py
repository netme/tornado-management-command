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
