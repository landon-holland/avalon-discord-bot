import random
import json
from discord import Embed, Member
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
        self.quest_num = 1
        self.game_status = 0  # 0: No Game. 1: Intermission. 2: In game
        self.checkTime = 300
        self.roles = {
            1: {"Loyal Servant of Arthur": 1, "Merlin": 1, "Percival": 1, "Morgana": 1, "Mordred": 1, "Assassin": 0, "Minion of Mordred": 0},
            5: {"Loyal Servant of Arthur": 1, "Merlin": 1, "Percival": 1, "Morgana": 1, "Mordred": 1, "Assassin": 0, "Minion of Mordred": 0},
            6: {"Loyal Servant of Arthur": 2, "Merlin": 1, "Percival": 1, "Morgana": 1, "Mordred": 1, "Assassin": 0, "Minion of Mordred": 0},
            7: {"Loyal Servant of Arthur": 2, "Merlin": 1, "Percival": 1, "Morgana": 1, "Mordred": 1, "Assassin": 1, "Minion of Mordred": 0},
            8: {"Loyal Servant of Arthur": 3, "Merlin": 1, "Percival": 1, "Morgana": 1, "Mordred": 1, "Assassin": 1, "Minion of Mordred": 0},
            9: {"Loyal Servant of Arthur": 4, "Merlin": 1, "Percival": 1, "Morgana": 1, "Mordred": 1, "Assassin": 1, "Minion of Mordred": 0},
            10: {"Loyal Servant of Arthur": 4, "Merlin": 1, "Percival": 1, "Morgana": 1, "Mordred": 1, "Assassin": 1, "Minion of Mordred": 1}
        }
        self.good = ["Loyal Servant of Arthur", "Merlin", "Percival"]
        self.evil = ["Morgana", "Mordred", "Assassin", "Minion of Mordred"]
    
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

    @cog_ext.cog_slash(name="guide", guild_ids=guild_id) # TODO add desc
    async def _guide(self, ctx: SlashContext):
        await ctx.send("Sending to PMs...")
        with open("guides/general1.txt") as f:
            await ctx.author.send(f.read())
        with open("guides/general2.txt") as f:
            await ctx.author.send(f.read())

    @cog_ext.cog_slash(name="start", guild_ids=guild_id) # TODO add desc
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
                        await self.send_player_order(ctx=ctx)
                        await self.make_dropdown(ctx.channel_id, "Temp", self.players, self.players, 2)

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
        with open("role_thumbnails.json") as f:
            role_thumbnails = json.load(f)

        roles_for_this_game = []
        for role, number in self.roles[len(self.players)].items():
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
            embed_thumbnail = role_thumbnails[role]
            embed = self.make_embed("Avalon", embed_color, embed_desc, embed_role)
            embed.set_thumbnail(url=embed_thumbnail)
            await player.send(embed=embed)
        
        for player in [p for p in self.players if self.player_roles[p] in self.evil]:
            evil_players = [p for p in self.players if (self.player_roles[p] in self.evil)]
            await player.send(f"The members of the Minion of Mordred are:\n{await self.enumerate_players(evil_players)}")
        
        for player in [p for p in self.players if self.player_roles[p] == "Merlin"]:
            merlin_players = [p for p in self.players if (self.player_roles[p] in self.evil and self.player_roles[p] != "Mordred")]
            await player.send(f"The Minions of Mordred (excluding Mordred) are:\n{await self.enumerate_players(merlin_players)}")
        
        for player in [p for p in self.players if self.player_roles[p] == "Percival"]:
            percival_players = [p for p in self.players if (self.player_roles[p] == "Merlin" or self.player_roles[p] == "Morgana")]
            await player.send(f"Merlin and Morgana are (you don't know who is who): {await self.enumerate_players(percival_players)}")

    async def enumerate_players(self, players):
        message = ""
        for player in players:
            message += player.mention + ", "
        if len(message) > 0:
            message = message[:-2]
        return message

    async def send_player_order(self, ctx: SlashContext):
        channel = self.bot.get_channel(ctx.channel_id)
        message = "The order of players is:\n"
        for count, p in enumerate(self.players):
            if count == 0:
                message += "⭐" + str(count + 1) + ". " + self.displayname(p) + "\n"
            message += str(count + 1) + ". " + self.displayname(p) + "\n"
        await channel.send(message)

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
            result[dropdown_ctx.author] = [player for player in player_select_list if str(player.id) in dropdown_ctx.values]
            await dropdown_ctx.send(f"{dropdown_ctx.author.mention} made their selection.")
        # for k, v in result.items():
        #     print(f"caller: {self.displayname(k)}")
        #     for player in v:
        #         print(f"option: {self.displayname(player)}")
        return result

def setup(bot: Bot):
    bot.add_cog(Avalon(bot))
