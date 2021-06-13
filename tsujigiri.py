import os
import discord
from dotenv import load_dotenv
from datetime import datetime, timedelta


class Tsujigiri(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}.')
        for guild in self.guilds:
            pruner = Pruner(guild)
            await pruner.make_list()
            await pruner.kick()
            del pruner


class Pruner:
    def __init__(self, guild):
        self.guild = guild
        self.period = int(os.getenv('PRUNING_PERIOD', 365))
        self.list = []

    async def make_list(self):
        for member in self.guild.members:
            if member.bot:
                continue
            if datetime.now() - member.joined_at < timedelta(days=self.period):
                continue

            prune = True
            for channel in self.guild.text_channels:
                entry = await channel.history().get(author__id=member.id)
                if not entry:
                    continue
                if datetime.now() - entry.created_at < timedelta(days=self.period):
                    prune = False
                    break
            if prune:
                self.list.append(member)

    async def kick(self):
        for member in self.list:
            try:
                await member.kick()
                print(f'Kicked {member} from {member.guild}')
            except (discord.errors.Forbidden, AttributeError) as error_content:
                print(f'Failed to kick {member}: {error_content}')


def main():
    load_dotenv()
    token = os.getenv('BOT_TOKEN')

    intents = discord.Intents.default()
    intents.members = True

    client = Tsujigiri(intents=intents)
    client.run(token)


if __name__ == '__main__':
    main()
