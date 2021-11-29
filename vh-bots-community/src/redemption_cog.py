import asyncio
from member import GuildMember

from discord.embeds import Embed
import discord

from cog_helpers import CogHelpers
from discord.ext import commands
from embed_builder import EmbedBuilder
from redemption import Redemption
from settings import BotSettings

class RedemptionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        CogHelpers.set_bot(bot)

    #staticmethod
    def generate_reward_lines(rewards, per_page: int=0, current_page: int=0):
        if len(rewards) == 0:
            raise ValueError('List of rewards is empty', rewards)
        
        if per_page == 0:
            max_page = 0
        else:
            max_page = min(0, (len(rewards) - 1) // per_page)
        
        if current_page > max_page:
            raise ValueError("Invalid value for current_page", current_page)
        
        reward_lines = []
        if per_page == 0:
            reward_indices = range(0, len(rewards))
        else:
            range_start = current_page * per_page
            range_end = min(len(rewards), (current_page + 1) * per_page - 1)
            reward_indices = range(range_start, range_end)
        
        for i in reward_indices:
            reward = rewards[i]
            reward_lines.append("[{0:0>4d}]({1})".format(int(reward._key), str(reward)))
        
        return reward_lines
    
    async def post_to_redeem_channel(self, member, reward):
        user_name = CogHelpers.get_user_full_name(CogHelpers.get_guild_member(member._key))
        embed_lines = ["New reward redemption from {0} ({1})!\n".format(user_name, member.get_mention()),
                        "**Reward Name** - {0}".format(reward.name)]
        
        redeem_embed = EmbedBuilder().setTitle("New Reward Redemption!") \
                                        .setColour(BotSettings.get_setting('admin', 'EMBED_COLOUR').value) \
                                        .setDescriptionFromLines(embed_lines)
        
        post_channel_id = int(BotSettings.get_setting('rewards', 'REDEMPTION_CHANNEL').value)
        post_channel = CogHelpers.get_guild_channel_by_id(post_channel_id)
        await post_channel.send(embed=redeem_embed.build())        
    
    @commands.command(name='redeem')
    @commands.check(CogHelpers.check_is_guild_member)
    @commands.dm_only()
    async def redeem_reward(self, ctx, reward_id: str=None):
        has_profile = await CogHelpers.require_bot_membership(ctx)
        if not has_profile or reward_id is None:
            return
        
        member = GuildMember.get_member_by_id(ctx.author.id)
        
        redeem_embed = EmbedBuilder().setTitle("Redeem Points") \
                                        .setColour(BotSettings.get_setting('admin', 'EMBED_COLOUR').value)
        embed_lines = []
        try:
            reward_id = int(reward_id)
            reward = Redemption.get_redemption_by_key(reward_id)
            if reward is None:
                raise ValueError("Invalid reward ID", reward_id)
            if not reward.enabled:
                raise ValueError("This reward is disabled", reward)
        except ValueError:
            embed_lines.append("You entered an invalid reward ID: `{0}`".format(reward_id))
            redeem_embed = redeem_embed.setDescriptionFromLines(embed_lines).build()
            await ctx.send(embed=redeem_embed)
            return
        
        if not member.can_purchase(reward):
            embed_lines.append("You only have `{0}` points, which is not enough for this reward (needs `{1}` points).".format(member.balance, reward.cost))
            redeem_embed = redeem_embed.setDescriptionFromLines(embed_lines).build()
            await ctx.send(embed=redeem_embed)
            return
        
        embed_lines = ["Redeeming reward `{0:0>4d}`: {1}\n".format(int(reward._key), reward.name),
                        "Are you sure you wish to do this?  You will be spending {0} points".format(reward.cost),
                        "React \N{WHITE HEAVY CHECK MARK} to continue, or \N{CROSS MARK} to stop"]
        redeem_embed = redeem_embed.setDescriptionFromLines(embed_lines).build()
        embed_message = await ctx.send(embed=redeem_embed)

        reply_reactions = ['\N{WHITE HEAVY CHECK MARK}', '\N{CROSS MARK}']
        for reaction in reply_reactions:
            await embed_message.add_reaction(reaction)
        
        def validate_react(react, user):
            return react.emoji in reply_reactions and user.id == ctx.author.id and react.message.id == embed_message.id
        
        try:
            react, user = await self.bot.wait_for('reaction_add', check=validate_react, timeout=30)
        except asyncio.TimeoutError:
            redeem_embed = EmbedBuilder.fromEmbed(redeem_embed) \
                                            .appendToDescription("\n**You took too long to respond!**") \
                                            .build()
            await embed_message.edit(embed=redeem_embed)
        else:
            redeem_embed = EmbedBuilder.fromEmbed(redeem_embed).appendToDescription("\n**You reacted: {0}**".format(react.emoji))
            if react.emoji == '\N{CROSS MARK}':
                redeem_embed.appendToDescription("No action taken - you still have your points!")
            else:
                member.purchase(reward)
                reward.purchased()
                await self.post_to_redeem_channel(member, reward)
                redeem_embed.appendToDescription("You purchased this reward for {0} points!".format(reward.cost))
        finally:
            for reaction in reply_reactions:
                await embed_message.remove_reaction(reaction, self.bot.user)
            await embed_message.edit(embed=redeem_embed.build())


    @commands.command(name='rewards')
    @commands.check(CogHelpers.check_is_guild_member)
    @commands.dm_only()
    async def show_rewards_list(self, ctx, enabled_filter: str=None):
        has_profile = await CogHelpers.require_bot_membership(ctx)
        if not has_profile:
            return

        all_rewards = Redemption.get_all_redemptions(sorter=Redemption.reverse_cost_then_name_sorter)
        
        used_filter = False
        if CogHelpers.check_is_admin(ctx) and enabled_filter in ['all', 'off']:
            used_filter = True
            rewards = [reward for reward in all_rewards if enabled_filter == 'all' or not reward.enabled]
        else:
            rewards = [reward for reward in all_rewards if reward.enabled]
        
        embed_lines = []
        if len(rewards) == 0:
            embed_lines.append("Looks like there aren't any rewards available right now!")
        else:
            embed_lines.append("```md")
            embed_lines.extend(RedemptionCog.generate_reward_lines(rewards, per_page=15))
            embed_lines.append("```")

        if CogHelpers.check_is_admin(ctx):
            if used_filter:
                embed_lines.append("This includes disabled rewards")
            else:
                embed_lines.append("To include disabled rewards, or only view disabled rewards, use "
                                    "`c.rewards [all | off]`")
        else:
            if len(rewards) > 0:
                embed_lines.append("To redeem a reward, use `c.redeem [id]`")

        rewards_embed = EmbedBuilder().setTitle("Available Rewards") \
                                    .setColour(BotSettings.get_setting('admin', 'EMBED_COLOUR').value) \
                                    .setDescriptionFromLines(embed_lines) \
                                    .build()

        await ctx.send(embed=rewards_embed)
    
    @commands.command(name='addreward')
    @commands.check(CogHelpers.check_is_admin)
    @commands.check(CogHelpers.check_is_channel_or_dm)
    async def add_reward(self, ctx):
        embed_base = ["This will guide you through adding a new reward to the bot\n"]
        embed_lines = ["Please enter the name of the new reward in this channel"]

        reward_embed = EmbedBuilder().setTitle("Add New Reward") \
                                        .setColour(BotSettings.get_setting('admin', 'EMBED_COLOUR').value) \
                                        .setDescriptionFromLines(embed_base + embed_lines) \
                                        .build()
        
        embed_message = await ctx.send(embed=reward_embed)

        def validate_reply(message):
            return message.channel == embed_message.channel and message.author.id == ctx.author.id

        try:
            response = await self.bot.wait_for('message', check=validate_reply, timeout=30)
        except asyncio.TimeoutError:
            embed_lines = ["You took too long to reply!  Please start over with `c.addreward`"]
            reward_embed = EmbedBuilder.fromEmbed(reward_embed) \
                                        .setDescriptionFromLines(embed_base + embed_lines) \
                                        .build()
            await embed_message.edit(embed=reward_embed)
            return
        else:
            reward_name = response.content.strip()

            embed_lines = ["Please enter the cost of this reward in points\n", "**Name** - {0}".format(reward_name)]
            reward_embed = EmbedBuilder.fromEmbed(reward_embed) \
                                        .setDescriptionFromLines(embed_base + embed_lines) \
                                        .build()
            await embed_message.edit(embed=reward_embed)
        
        try:
            response = await self.bot.wait_for('message', check=validate_reply, timeout=30)
        except asyncio.TimeoutError:
            embed_lines = ["You took too long to reply!  Please start over with `c.addreward`"]
            reward_embed = EmbedBuilder.fromEmbed(reward_embed) \
                                        .setDescriptionFromLines(embed_base + embed_lines) \
                                        .build()
            await embed_message.edit(embed=reward_embed)
        else:
            reward_cost = response.content.strip()
            try:
                reward_cost = int(reward_cost)
                if reward_cost <= 0:
                    raise ValueError('Reward has to have a positive cost', reward_cost)
            except ValueError:
                embed_lines = ["You have to enter a positive number for the cost.  Please start over with `c.addreward`"]
                reward_embed = EmbedBuilder.fromEmbed(reward_embed) \
                                            .setDescriptionFromLines(embed_base + embed_lines) \
                                            .build()
                await embed_message.edit(embed=reward_embed)
                return
            else:
                embed_lines = ["Should this reward be enabled right away?\n",
                                "**Name** - {0}".format(reward_name),
                                "**Cost** - {0} points".format(reward_cost)]
                reward_embed = EmbedBuilder.fromEmbed(reward_embed) \
                                            .setDescriptionFromLines(embed_base + embed_lines) \
                                            .build()
                await embed_message.edit(embed=reward_embed)
        
        try:
            response = await self.bot.wait_for('message', check=validate_reply, timeout=30)
        except asyncio.TimeoutError:
            embed_lines = ["You took too long to reply!  Please start over with `c.addreward`"]
            reward_embed = EmbedBuilder.fromEmbed(reward_embed) \
                                        .setDescriptionFromLines(embed_base + embed_lines) \
                                        .build()
            await embed_message.edit(embed=reward_embed)
        else:
            enabled = ['y', 'yes', 'true', 'enabled', 'on']
            disabled = ['n', 'no', 'false', 'disabled', 'off']
            reward_enabled = response.content.strip().lower()
            if not reward_enabled in enabled and not reward_enabled in disabled:
                embed_lines = ["You need to say yes/no, on/off, or enabled/disabled.  Please start over with `c.addreward`"]
                reward_embed = EmbedBuilder.fromEmbed(reward_embed) \
                                            .setDescriptionFromLines(embed_base + embed_lines) \
                                            .build()
                await embed_message.edit(embed=reward_embed)
                return
            reward_enabled = bool(reward_enabled in enabled)
        
        reward = Redemption.create_redemption(reward_name, reward_cost, reward_enabled)
        embed_lines = ["Successfully saved new reward!\n",
                        "**ID** - {0:0>4d}".format(int(reward._key)),
                        "**Name** - {0}".format(reward_name),
                        "**Cost** - {0} points".format(reward_cost),
                        "**Enabled** - {0}".format("Yes" if reward_enabled else "No")]
        reward_embed = EmbedBuilder.fromEmbed(reward_embed) \
                                    .setDescriptionFromLines(embed_base + embed_lines) \
                                    .build()
        await embed_message.edit(embed=reward_embed)

    @commands.command(name='setreward')
    @commands.check(CogHelpers.check_is_admin)
    @commands.check(CogHelpers.check_is_channel_or_dm)
    async def set_reward(self, ctx, reward_id: int, field: str=None, *, value: str=None):
        # This needs to be cleaned up at some point somehow
        embed_lines = []
        
        reward_id = int(reward_id)
        reward = Redemption.get_redemption_by_key(reward_id)
        if reward is None:
            embed_lines.append("Could not find a reward with ID `{0:0>4d}`".format(reward_id))
            embed_title = "Reward Info"
        else:
            if field is None:
                embed_title = "Reward Info"
                embed_lines.append("Current information for reward ID `{0:0>4d}`\n".format(reward_id))
                embed_lines.append("**Name** - {0}".format(reward.name))
                embed_lines.append("**Cost** - {0} points".format(reward.cost))
                embed_lines.append("**Enabled** - {0}".format("Yes" if reward.enabled else "No"))
                embed_lines.append("\n")
                embed_lines.append("To set a field, use `c.setreward [reward_id] [field] [new_value]`")
            else:
                field = field.lower()
                valid_fields = ['name', 'cost', 'enabled']
                if not field in valid_fields:
                    embed_lines.append("Invalid field specified: {0}".format(field))
                    embed_lines.append("Valid fields: {0}".format(', '.join(valid_fields)))
                elif value is None or value.strip() == '':
                    embed_lines.append("You have to specify a value in order to change `{0}`".format(field))
                else:
                    updated_reward = False
                    if field == 'name':
                        reward.set_name(value)
                        updated_reward = True
                    elif field == 'cost':
                        try:
                            value_as_int = int(value)
                            if value_as_int <= 0:
                                raise ValueError('Rewards have to have a positive cost')
                            reward.set_cost(value_as_int)
                            updated_reward = True
                        except ValueError:
                            embed_lines.append("Rewards have to cost a positive number of points")
                    elif field == 'enabled':
                        set_enabled = (value.lower() in ['y', 'yes', 'true', 'enabled'])
                        set_disabled = (value.lower() in ['n', 'no', 'false', 'disabled'])

                        if set_enabled:
                            reward.enable()
                            updated_reward = True
                        elif set_disabled:
                            reward.disable()
                            updated_reward = True
                        else:
                            embed_lines.append("Enabled should be set to yes or no")

                    if updated_reward:
                        embed_lines.append("Updated {0} to {1} for reward ID `{2:0>04d}`".format(field, value, reward_id))
                
                embed_title = "Update Reward"

        reward_embed = EmbedBuilder().setTitle(embed_title) \
                                        .setColour(BotSettings.get_setting('admin', 'EMBED_COLOUR').value) \
                                        .setDescriptionFromLines(embed_lines) \
                                        .build()
        
        await ctx.send(embed=reward_embed)


def setup(bot):
    bot.add_cog(RedemptionCog(bot))