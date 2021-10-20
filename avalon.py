import random
from discord import Embed, Member
from discord.ext.commands import Bot, Cog
from discord_slash import cog_ext, SlashContext, ComponentContext
from discord_slash.utils.manage_components import create_button, create_actionrow, wait_for_component
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
        if self.game_status == 2: #TODO erorr xd
            return

        buttons = [
            create_button(style=ButtonStyle.green, label="Join"),
            create_button(style=ButtonStyle.red, label="Leave"),
            create_button(style=ButtonStyle.blue, label="Ready"),
            create_button(style=ButtonStyle.blurple, label="Unready")
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
                    await button_ctx.send(f"{button_ctx.author.mention}, you aren't even in the game, dude.")
            elif button_ctx.component["label"] == "Ready":
                if button_ctx.author not in self.players: # TODO error messages
                    return
                if button_ctx.author in self.ready_players:
                    return
                if self.game_status != 1:
                    return
                
                self.ready_players.append(button_ctx.author)
                await button_ctx.send(f"{button_ctx.author.mention} is now ready! {len(self.ready_players)}/{len(self.players)}")

                if len(self.ready_players) == len(self.players):
                    if len(self.players) < self.min_players:
                        pass # TODO error message
                    else:
                        self.game_status = 2
                        # TODO countdown
                        await self.assign_roles()
            elif button_ctx.component["label"] == "Unready":
                if button_ctx.author not in self.players: # TODO error messages
                    return
                if button_ctx.author not in self.ready_players:
                    return
                if self.game_status != 1:
                    return
                
                self.ready_players.remove(button_ctx.author)
                await button_ctx.send(f"{button_ctx.author.mention} is now unready! ({len(self.ready_players)}/{len(self.players)})")

    async def assign_roles(self):
        roles_for_this_game = []
        role_thumbnails = {"Loyal Servant of Arthur": "http://gamekicker.herokuapp.com/assets/loyal-5b2decd4aa309e12020b50b3950ab440.jpeg",
          "Merlin": "https://www.ultraboardgames.com/avalon/gfx/merlin.jpg",
          "Percival": "https://www.ultraboardgames.com/avalon/gfx/percival.jpg",
          "Morgana": "https://www.ultraboardgames.com/avalon/gfx/morgana.jpg",
          "Mordred": "https://www.ultraboardgames.com/avalon/gfx/mordred.jpg",
          "Assassin": "https://www.ultraboardgames.com/avalon/gfx/assassin.jpg",
          "Minion of Mordred": "http://gamekicker.herokuapp.com/assets/minion-553e9b70b2aea7fbfd37e20e68aab878.jpeg"}

        random.shuffle(self.players)

        for role, number in self.roles[len(self.players)].items():
            for n in range(number):
                roles_for_this_game.append(role)

        for player in self.players:
            self.player_roles.update({player:roles_for_this_game.pop()})
        
        evil_players = []
        for player, role in self.player_roles.items():
            if role in self.evil:
                evil_players.append(player)

        for player, role in self.player_roles.items():
            message = ""
            embed_role = ""
            embed_color = 0x77dd77
            embed_desc = ""
            embed_thumbnail = ""
            if role in self.evil:
                embed_role = "Minion of Mordred"
                embed_color = 0xff4055
                embed_desc = "You are a Minion of Mordred"
                message += "The other players on your team are:\n"
                for p in evil_players:
                    if p != player:
                        message += self.displayname(p) + "\n"
            
            if role in self.good:
                embed_role = "Loyal Servant of Arthur"
                embed_desc = "You are a Loyal Servant of Arthur"

            if role == "Merlin":
                message += "The Minions of Mordred (excluding Mordred) are:\n"
                for p in evil_players:
                    if self.player_roles[p] != "Mordred":
                        message += self.displayname(p) + "\n"
            
            if role == "Percival":
                message += "Merlin and Morgana are (you don't know who is who):\n"
                for p in self.players:
                   if self.player_roles[p] == "Merlin" or self.player_roles[p] == "Morgana":
                        message += self.displayname(p) + "\n"
            
            if role != "Loyal Servant of Arthur" and role != "Minion of Mordred":
                embed_desc = f"You are {role}!\nUse `/guide` to find a guide about your role."
                embed_thumbnail = role_thumbnails[role]
            
            embed = self.make_embed("Avalon", embed_color, embed_desc, embed_role)
            embed.set_thumbnail(url=embed_thumbnail)
            await player.send(embed=embed)
            if message != "":
                await player.send(message)

        await self.sendPlayerOrder()

    async def sendPlayerOrder(self, ctx: SlashContext):
        message = "The order of players is:\n"
        for count, p in enumerate(self.players):
            message += str(count + 1) + ". " + self.displayname(p) + "\n"

        ctx.send(message)

def setup(bot: Bot):
    bot.add_cog(Avalon(bot))
