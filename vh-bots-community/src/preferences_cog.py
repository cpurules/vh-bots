import asyncio
from asyncio.tasks import wait, wait_for
import discord

from cog_helpers import CogHelpers
from discord.ext import commands
from embed_builder import EmbedBuilder
from member import GuildMember
from member_preferences import MemberPreferences
from settings import BotSettings

class PreferencesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        CogHelpers.set_bot(bot)
    
    @commands.command(name='preferences')
    @commands.check(CogHelpers.check_is_guild_member)
    @commands.dm_only()
    async def manage_preferences(self, ctx, action: str=None):
        has_profile = await CogHelpers.require_bot_membership(ctx)
        if not has_profile:
            return
        
        preferences = MemberPreferences.get_preferences_by_member_id(ctx.author.id)
        if preferences is None:
            preferences = MemberPreferences.create_preferences(ctx.author.id)
        
        preferences_embed = EmbedBuilder().setTitle("User Preferences") \
                                            .setColour(BotSettings.get_setting('admin', 'EMBED_COLOUR').value)
        
        wait_for_reacts = []
        if action is None:       
            preferences_embed = preferences_embed.appendToDescription("Hello {0}!".format(ctx.author.mention)) \
                                                    .appendToDescription("Below are your preferences for the Community Bot.") \
                                                    .appendToDescription("To update your preferences, use `c.preferences edit`") \
                                                    .appendToDescription("") \
                                                    .appendToDescription("DM on Award: `{0}`".format(preferences.notify_on_award))
        elif action == 'edit':
            preferences_embed = preferences_embed.appendToDescription("To toggle DMs on award, click the \N{E-MAIL SYMBOL} react.")
            wait_for_reacts.append('\N{E-MAIL SYMBOL}')
        else:
            preferences_embed = preferences_embed.appendToDescription("Oops!  I don't recognize that option.") \
                                                    .appendToDescription("") \
                                                    .appendToDescription("Use `c.preferences` to list your current preferences.") \
                                                    .appendToDescription("Use `c.preferences edit` to update your preferences.")
        
        preferences_msg = await ctx.send(embed=preferences_embed.build())

        if len(wait_for_reacts) > 0:
            for react in wait_for_reacts:
                await preferences_msg.add_reaction(react)
            
            def validate_reaction(reaction, user):
                return reaction.emoji in wait_for_reacts and reaction.message.id == preferences_msg.id and not user.bot
            
            try:
                pref_react, pref_user = await self.bot.wait_for('reaction_add', timeout=15, check=validate_reaction)
            except asyncio.TimeoutError:
                preferences_embed = preferences_embed.setDescription("Oops!  You took to long to react!") \
                                                        .appendToDescription("You can update your preferences with `c.preferences edit`")
                await preferences_msg.edit(embed=preferences_embed.build())
                return
            
            if pref_react.emoji == '\N{E-MAIL SYMBOL}':
                preferences.notify_on_award = not preferences.notify_on_award
                preferences.save()
                preferences_embed = preferences_embed.setDescription("Successfully updated your DM preference to `{0}`".format(preferences.notify_on_award))
            
            await preferences_msg.edit(embed=preferences_embed.build())


def setup(bot):
    bot.add_cog(PreferencesCog(bot))