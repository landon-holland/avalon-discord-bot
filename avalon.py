import random
import json
from discord import Embed, Member, player
from discord.ext.commands import Bot, Cog
from discord_slash import cog_ext, SlashContext, ComponentContext
from discord_slash.utils.manage_components import create_button, create_select, create_select_option, create_actionrow, wait_for_component
from discord_slash.model import ButtonStyle
guild_id = [340219167909085185]


class Avalon(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.players = []
        self.ready_players = []
        self.min_players = 5
        self.max_players = 10
        self.player_roles = {}
        self.passed_quests = ["Not done"] * 5
        self.quest_num = 0    # count from 0
        self.game_status = 0  # 0: No Game. 1: Intermission. 2: In game
        self.checkTime = 300  # TODO add game timeout
        with open("config.json") as f:
            self.config = json.load(f)
        self.roles = self.config["roles"]
        self.role_thumbnails = self.config["role_thumbnails"]
        self.team_counts = self.config["team_counts"]
        self.good = self.config["good"]
        self.evil = self.config["evil"]

    def displayname(self, member: Member):
        # A helper function to return the member's display name
        nick = name = None
        try:
            nick = member.nick
        except AttributeError:
            pass
        try:
            name = member.name
        except AttributeError:
            pass
        if nick:
            return nick
        if name:
            return name
        return None

    def make_embed(self, title, color, name, value):
        embed = Embed(title=title, color=color)
        embed.add_field(name=name,
                        value=value,
                        inline=False)

        return embed

    def clear_variables(self):
        self.players = []
        self.ready_players = []
        self.player_roles = {}
        self.quest_num = 1
        self.game_status = 0

    @cog_ext.cog_slash(name="guide", guild_ids=guild_id)  # TODO add desc
    async def _guide(self, ctx: SlashContext):
        await ctx.send("Sending to PMs...")
        with open("guides/general1.txt") as f:
            await ctx.author.send(f.read())
        with open("guides/general2.txt") as f:
            await ctx.author.send(f.read())

    @cog_ext.cog_slash(name="start", guild_ids=guild_id)  # TODO add desc
    async def _start(self, ctx: SlashContext):
        if self.game_status == 2:
            await ctx.send("The game has already been started.")
            return

        buttons = [
            create_button(style=ButtonStyle.green, label="Join"),
            create_button(style=ButtonStyle.red, label="Leave"),
            create_button(style=ButtonStyle.blue, label="Ready"),
            create_button(style=ButtonStyle.blue, label="Unready")
        ]
        action_row = create_actionrow(*buttons)
        await ctx.send("Starting Avalon game...", components=[action_row])
        self.game_status = 1

        while self.game_status == 1:
            button_ctx: ComponentContext = await wait_for_component(self.bot, components=action_row)
            if button_ctx.component["label"] == "Join":
                if button_ctx.author in self.players:
                    await button_ctx.send(f"{button_ctx.author.mention}, you are already in the game.")
                else:
                    if len(self.players) < self.max_players:
                        self.players.append(button_ctx.author)
                        await button_ctx.send(f"{button_ctx.author.mention} joined the game.")
                    else:
                        await button_ctx.send(f"{button_ctx.author.mention} Game is full.")
            elif button_ctx.component["label"] == "Leave":
                if button_ctx.author in self.players:
                    self.players.remove(button_ctx.author)
                    await button_ctx.send(f"{button_ctx.author.mention} has left the game.")
                else:
                    await button_ctx.send(f"{button_ctx.author.mention}, you aren't in the game.")
            elif button_ctx.component["label"] == "Ready":
                if button_ctx.author not in self.players:
                    await button_ctx.send(f"{button_ctx.author.mention}, you haven't joined the game.")
                    return
                if button_ctx.author in self.ready_players:
                    await button_ctx.send(f"{button_ctx.author.mention}, you are already ready.")
                    return

                self.ready_players.append(button_ctx.author)
                await button_ctx.send(f"{button_ctx.author.mention} is now ready! {len(self.ready_players)}/{len(self.players)}")

                if len(self.ready_players) == len(self.players):
                    if len(self.players) < self.min_players:
                        await button_ctx.send(f"Need {self.min_players} to start game.")
                    else:
                        self.game_status = 2
                        # TODO countdown
                        await self.assign_roles()
                        await self.main_game_loop(ctx=ctx)

            elif button_ctx.component["label"] == "Unready":
                if button_ctx.author not in self.players:
                    await button_ctx.send(f"{button_ctx.author.mention} you aren't even in the game, dude.")
                    return
                if button_ctx.author not in self.ready_players:
                    await button_ctx.send(f"{button_ctx.author.mention} you're already not ready.")
                    return

                self.ready_players.remove(button_ctx.author)
                await button_ctx.send(f"{button_ctx.author.mention} is now unready! ({len(self.ready_players)}/{len(self.players)})")

    async def assign_roles(self):
        roles_for_this_game = []
        for role, number in self.roles[str(len(self.players))].items():
            roles_for_this_game += [role] * number

        random.shuffle(self.players)
        random.shuffle(roles_for_this_game)

        for player in self.players:
            self.player_roles[player] = roles_for_this_game.pop()

        for player, role in self.player_roles.items():
            if role in self.evil:
                embed_role = "Minion of Mordred"
                embed_color = 0xff4055
                embed_desc = "You are a Minion of Mordred"

            if role in self.good:
                embed_role = "Loyal Servant of Arthur"
                embed_color = 0x77dd77
                embed_desc = "You are a Loyal Servant of Arthur"

            embed_desc = f"You are {role}!\nUse `/guide` to find a guide about your role."
            embed_thumbnail = self.role_thumbnails[role]
            embed = self.make_embed(
                "Avalon", embed_color, embed_desc, embed_role)
            embed.set_thumbnail(url=embed_thumbnail)
            await player.send(embed=embed)

        for player in [p for p in self.players if self.player_roles[p] in self.evil]:
            evil_players = [p for p in self.players if (
                self.player_roles[p] in self.evil)]
            await player.send(f"The members of the Minion of Mordred are:\n{await self.enumerate_players(evil_players)}")

        for player in [p for p in self.players if self.player_roles[p] == "Merlin"]:
            merlin_players = [p for p in self.players if (
                self.player_roles[p] in self.evil and self.player_roles[p] != "Mordred")]
            await player.send(f"The Minions of Mordred (excluding Mordred) are:\n{await self.enumerate_players(merlin_players)}")

        for player in [p for p in self.players if self.player_roles[p] == "Percival"]:
            percival_players = [p for p in self.players if (
                self.player_roles[p] == "Merlin" or self.player_roles[p] == "Morgana")]
            await player.send(f"Merlin and Morgana are (you don't know who is who): {await self.enumerate_players(percival_players)}")

    async def main_game_loop(self, ctx: SlashContext):
        channel_ctx = self.bot.get_channel(ctx.channel_id)
        # Five quests
        for i in range(5):
            skips = 0
            while skips < 5:
                # Quest information
                await channel_ctx.send(f"Welcome to Quest {self.quest_num + 1}!")
                await channel_ctx.send(f"There will be {self.team_counts[str(len(self.players))][self.quest_num]} team members on this Quest.")
                if self.quest_num == 3 and len(self.players) > 6:
                    await channel_ctx.send("For this Quest **TWO** fail votes are required for the Quest to fail!")
                # Send team order
                await self.send_player_order(ctx.channel_id)
                # Make dropdown for team leader to make team
                picked_players = (await self.make_dropdown(ctx.channel_id, f"{self.players[0].mention} is the current team leader!", {self.players[0]}, self.players, self.team_counts[str(len(self.players))][self.quest_num]))[self.players[0]]
                # List team
                await channel_ctx.send(f"{self.players[0].mention} has proposed the following team:\n{''.join([f'{i + 1}. {player.mention}🍔' for i, player in enumerate(picked_players)])}".replace("🍔", "\n")) # lmao
                # Whole group votes on team
                team_responses = await self.call_vote(channel_id=ctx.channel_id, message="Should this proposed team go on the Quest?", players=self.players, private=False)
                # Check votes
                if sum([1 if "Pass" == value else 0 for key, value in team_responses.items()]) > len(self.players) / 2:
                    break
                skips += 1
                await channel_ctx.send(f"The vote has failed! Time to vote for another team. ({skips}/5 skips)")
                await channel_ctx.send("If 5 skips is reached, the Quest is failed!")
                self.players.append(self.players.pop(0))
            if skips == 5:
                await channel_ctx.send("The proposed teams have been skipped 5 times now! Evil has won the Quest")
                self.passed_quests[self.quest_num] = "Failed"
                self.quest_num += 1
                # TODO monkey coding is happening here, make this a function
                await channel_ctx.send(f"Quest {self.quest_num + 1} is over. Moving on to Quest {self.quest_num + 2}...")
                await channel_ctx.send("".join([f"Quest {i + 1}: {result}\n" for i, result in enumerate(self.passed_quests)]))
                continue
            # Team does quest now
            await channel_ctx.send("The vote has passed! The proposed team will be going on the Quest.")
            quest_responses = await self.call_vote(channel_id=ctx.channel_id, message=f"{', '.join([f'{player.mention}' for player in picked_players])}: Do you want the quest to pass or fail?", players=picked_players, private=True)
            if sum([1 if "Fail" == value else 0 for key, value in quest_responses.items()]) > (1 if self.quest_num == 3 and len(self.players) > 6 else 0):
                await channel_ctx.send("The quest has failed!")
                self.passed_quests[self.quest_num] = "Failed"
            else:
                await channel_ctx.send("The quest has passed!")
                self.passed_quests[self.quest_num] = "Passed"
            await channel_ctx.send(f"Quest {self.quest_num + 1} is over. Moving on to Quest {self.quest_num + 2}...")
            await channel_ctx.send("".join([f"Quest {i + 1}: {result}\n" for i, result in enumerate(self.passed_quests)]))
            # TODO checks for winners
            self.quest_num += 1
        # TODO stuff with assassinations

    async def enumerate_players(self, players):
        message = ""
        for player in players:
            message += player.mention + ", "
        if len(message) > 0:
            message = message[:-2]
        return message

    async def send_player_order(self, channel_id: int):
        channel = self.bot.get_channel(channel_id)
        message = "The order of players is:\n"
        for count, p in enumerate(self.players):
            if count == 0:
                message += f"⭐ {str(count + 1)}. {self.displayname(p)} \n"
            else:
                message += str(count + 1) + ". " + self.displayname(p) + "\n"
        await channel.send(message)
    
    async def call_vote(self, channel_id: int, message: str, players: list[Member], private: bool):
        responses = {}
        channel = self.bot.get_channel(channel_id)
        buttons = [
            create_button(style=ButtonStyle.green, label="Pass"),
            create_button(style=ButtonStyle.red, label="Fail")
        ]
        action_row = create_actionrow(*buttons)
        await channel.send(message, components=[action_row])
        while len(responses) != len(players):
            button_ctx: ComponentContext = await wait_for_component(self.bot, components=action_row)
            if button_ctx.author not in players:
                continue
            responses[button_ctx.author] = button_ctx.component["label"]
            if private:
                await button_ctx.send(f"{len(responses)}/{len(players)} team members have voted.")
            else:
                await button_ctx.send(f"{button_ctx.author.mention} voted to {button_ctx.component['label'].lower()}.")
        return responses

    async def make_dropdown(self, channel_id: int, message: str, players: list[Member], player_select_list: list[Member], num_opt: int):
        result = {}
        channel = self.bot.get_channel(channel_id)
        select = create_select(
            options=[
                create_select_option(self.displayname(player), value=str(player.id)) for player in player_select_list
            ],
            placeholder="Select players...",
            min_values=num_opt,
            max_values=num_opt
        )
        action_row = create_actionrow(select)
        await channel.send(message, components=[action_row])
        while len(result) != len(players):
            dropdown_ctx: ComponentContext = await wait_for_component(self.bot, components=action_row)
            if dropdown_ctx.author not in players:
                continue
            result[dropdown_ctx.author] = [player for player in player_select_list if str(
                player.id) in dropdown_ctx.values]
            await dropdown_ctx.send(f"{dropdown_ctx.author.mention} made their selection.")
        return result


def setup(bot: Bot):
    bot.add_cog(Avalon(bot))
