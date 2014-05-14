from commands import BaseCommand


class Command(BaseCommand):

    description = "Prints Hello World!"
    arguments = {}

    def call(self, arguments):
        print("Hello world!")
