from django.core.management.base import BaseCommand
from tenabot.bot import main  # import your bot main() function

class Command(BaseCommand):
    help = "Run the Tenabot Telegram bot"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Starting Tenabot..."))
        main()