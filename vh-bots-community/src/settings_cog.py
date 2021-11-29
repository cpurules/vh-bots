# This whole cog needs to be cleaned up at some point

import asyncio
import re

from award_channel import AwardChannel
from cog_helpers import CogHelpers
from discord.ext import commands
from embed_builder import EmbedBuilder
from math import ceil
from settings import *

class SettingsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        CogHelpers.set_bot(bot)
    
    async def award_enabled_channels_handler(self, ctx, setting: BotSetting):
        editor_embed = EmbedBuilder().setTitle("Update Setting - AWARD_ENABLED_CHANNELS") \
                                        .setColour(BotSettings.get_setting('admin', 'EMBED_COLOUR').value)
        
        action = None
        action_stage = 0    
        ended = False
        timed_out = False
        response_type = None
        reply_value = None
        react_index = None
        page = 0
        max_page = ceil(len(setting.value) / 7) - 1

        def get_page_items(page: int):
            page_start = 7 * page
            page_end = min(len(setting.value), page_start + 7)
            return setting.value[page_start:page_end]

        while not ended:
            edit_flag = False

            if action is None or action == 'list':
                response_type = 'react'
                if not reply_value is None:
                    if reply_value == CogHelpers.NEXT_EMOJI:
                        page = min(page + 1, max_page)
                    elif reply_value == CogHelpers.PREV_EMOJI:
                        page = max(0, page - 1)
                    else:
                        if reply_value == CogHelpers.CANCEL_EMOJI:
                            action = 'remove'
                            continue
                        elif reply_value == CogHelpers.CHECK_EMOJI:
                            action = 'new'
                            continue
                else:
                    action = 'list'

                embed_lines = ["The list of AWARD_ENABLED_CHANNELS is below\n",
                                "To **__add__** a new item, click the {0} react".format(CogHelpers.CHECK_EMOJI)]
                reacts = [CogHelpers.CHECK_EMOJI]
                if len(setting.value) > 1:
                    reacts.append(CogHelpers.CANCEL_EMOJI)
                    embed_lines.append("To **__remove__** an item from the list, click the {0} react".format(CogHelpers.CANCEL_EMOJI))
                if len(setting.value) > 0:
                    embed_lines.append("To **__change__** an item, click the corresponding item's react")

                nav_reacts = []
                if max_page > 0:
                    if page > 0:
                        embed_lines.append("To **__view the previous page__**, click the \N{BLACK LEFT-POINTING TRIANGLE} react")
                        nav_reacts.append(CogHelpers.PREV_EMOJI)
                    elif page < max_page:
                        embed_lines.append("To **__view the next page__**, click the \N{BLACK RIGHT-POINTING TRIANGLE} react")
                        nav_reacts.append(CogHelpers.NEXT_EMOJI)
        
                embed_lines.append("")

                page_items = get_page_items(page)
                item_idx = 0
                for item in page_items:
                    letter = chr(ord('a') + item_idx)
                    emoji = chr(ord('\N{REGIONAL INDICATOR SYMBOL LETTER A}') + item_idx)
                    award_channel = AwardChannel.create_from_db_obj(item)
                    channel = CogHelpers.get_guild_channel_by_id(award_channel.id)
                    embed_lines.append("**{0}**. {1} (`ID {2}`)".format(letter.upper(), channel.mention, channel.id))
                    reacts.append(emoji)
                    item_idx = item_idx + 1
                
                reacts.extend(nav_reacts)

            elif action == 'new':
                embed_base_lines = ["To add a new award channel to the settings, follow the prompts below\n"]
                if action_stage == 0:
                    response_type = 'message'
                    action_stage = 1
                    embed_prompt = ["Enter the **channel ID** of the new award-enabled channel"]
                    embed_value_lines = []
                else:
                    edit_flag = True
                    if action_stage < 3: response_type = 'message'

                    if action_stage == 1:
                        channel = CogHelpers.get_guild_channel_by_id(int(reply_value))
                        award_channels = [AwardChannel.create_from_db_obj(x) for x in setting.value if x['id'] == str(reply_value)]
                        if channel is None:
                            embed_prompt = ["Couldn't find a channel with ID `{0}`".format(reply_value),
                                            "Enter the **channel ID** of the new award-enabled channel"]
                        elif str(reply_value) in [x['id'] for x in setting.value]:
                            embed_prompt = ["Looks like channel ID `{0}` is already in the list!".format(reply_value),
                                            "Enter the **channel ID** of the new award-enabled channel"]
                        else:
                            embed_prompt = ["Enter the **award chance multiplier** for this channel"]
                            embed_value_lines.append("**Channel** - {0} (ID: `{1}`)".format(channel.mention, channel.id))
                            action_stage += 1
                    elif action_stage == 2:
                        try:
                            chance_multiplier = float(reply_value)
                            if chance_multiplier < 0:
                                raise ValueError("Must be a positive multiplier")
                        except ValueError:
                            embed_prompt = ["Invalid multiplier entered: `{0}`".format(reply_value),
                                            "Enter the **award chance multiplier** for this channel"]
                        else:
                            embed_prompt = ["Enter the **point multiplier** for this channel"]
                            embed_value_lines.append("**Chance Multiplier** - `{0}`".format(float(reply_value)))
                            action_stage += 1
                    elif action_stage == 3:
                        try:
                            point_multiplier = float(reply_value)
                            if point_multiplier < 0:
                                raise ValueError("Must be a positive multiplier")
                        except ValueError:
                            embed_prompt = ["Invalid multiplier entered: `{0}`".format(reply_value),
                                            "Enter the **point multiplier** for this channel"]
                        else:
                            new_award_channel = AwardChannel(channel.id, chance_multiplier, point_multiplier)
                            new_award_channel_value = new_award_channel.get_as_db_dict()
                            setting.value.append(new_award_channel_value)
                            setting.save(overwrite=True)
                            embed_prompt = ["Created new award channel with the below details"]
                            embed_value_lines.append("**Point Multiplier** - `{0}`".format(float(reply_value)))
                            ended = True
                
                embed_lines = embed_base_lines + embed_prompt + (([""] + embed_value_lines) if len(embed_value_lines) > 0 else [])

            elif action == 'remove':
                if action_stage == 0:
                    response_type = 'message'
                    embed_lines = ["To remove a channel from the award channels list, enter the channel ID below"]
                    action_stage = 1
                else:
                    if action_stage == 1:
                        award_channels = [AwardChannel.create_from_db_obj(x) for x in setting.value if x['id'] == str(reply_value)]
                        if len(award_channels) == 0:
                            embed_lines = ["Could not find an existing award channel with ID `{0}`\n".format(reply_value),
                                            "To remove a channel from the award channels list, enter the channel ID below"]
                        else:
                            award_channel = award_channels[0]
                            response_type = 'react'
                            reacts = ['\N{NEGATIVE SQUARED CROSS MARK}','\N{WHITE HEAVY CHECK MARK}']
                            embed_lines = ["You have entered channel ID: `{0}`\n".format(reply_value),
                                            "**Are you sure you wish to disable awards from this channel?**"]
                            action_stage = action_stage + 1
                    elif action_stage == 2:
                        edit_flag = True
                        if reply_value == CogHelpers.CANCEL_EMOJI:
                            embed_lines = ["OK!  No action taken - award channel `{0}` has not been removed".format(award_channel.id)] 
                        elif reply_value == CogHelpers.CHECK_EMOJI:
                            setting.value = [x for x in setting.value if not x['id'] == str(award_channel.id)]
                            setting.save(overwrite=True)
                            embed_lines = ["Successfully removed award processing from channel `{0}`".format(award_channel.id)]
                            ended = True
            #TODO
            elif action == 'change':
                pass
                item = setting.value[page*7+react_index]
                if reply_value is None:
                    response_type = 'message'
                    embed_lines = ["To update this list item value (currently `{0}`), enter the value to change it to below".format(item)]
                else:
                    setting.value[page*7+react_index] = reply_value
                    setting.save(overwrite=True)
                    ended = True
                    continue
            
            editor_embed.setDescriptionFromLines(embed_lines)
            if not edit_flag:
                editor_message = await ctx.send(embed=editor_embed.build())
            else:
                await editor_message.edit(embed=editor_embed.build())
            
            if ended or response_type is None:
                return
            
            if response_type == 'react':
                for r in reacts:
                    await editor_message.add_reaction(r)

                def validate_react(react, user):
                    return user.id == ctx.author.id and react.emoji in reacts and react.message.id == editor_message.id
                
                try:
                    react, user = await self.bot.wait_for('reaction_add', check=validate_react, timeout=30)
                except asyncio.TimeoutError:
                    timed_out = True
                    ended = True
                else:
                    reply_value = react.emoji

            elif response_type == 'message':                
                try:
                    reply = await self.bot.wait_for('message', check=lambda m: CogHelpers.validate_is_reply(m, editor_message, expected_author=ctx.author.id), timeout=30)
                except asyncio.TimeoutError:
                    timed_out = True
                    ended = True
                else:
                    reply_value = reply.content.strip()

        if timed_out:
            embed_lines = ["Sorry, you took too long to respond!\n", "You can start over by using `c.settings {0} {1} {2}`".format(setting.area, setting.token, "edit")]
            editor_embed.setDescriptionFromLines(embed_lines)
            await editor_message.edit(embed=editor_embed.build())
    
    async def embed_colour_handler(self, ctx, setting: BotSetting):
        editor_embed = EmbedBuilder().setTitle("Update Setting - EMBED_COLOUR") \
                                        .setColour(setting.value)
        
        timed_out = False
        reply_value = None

        reacts = []

        if reply_value is None:
            embed_lines = ["The current (R, G, B) color of the embed is ({0}, {1}, {2})\n".format(*setting.value),
                            "This is the colour you see on this embed.",
                            "If you want to change the color, click the \N{PENCIL} react"]
            reacts = ['\N{PENCIL}']
            editor_embed.setDescriptionFromLines(embed_lines)
            editor_message = await ctx.send(embed=editor_embed.build())
            for r in reacts:
                await editor_message.add_reaction(r)
            
            def validate_react_1(react, user):
                return react.emoji in reacts and react.message.id == editor_message.id and user.id == ctx.author.id

            try:
                react, user = await self.bot.wait_for('reaction_add', check=validate_react_1, timeout=30)
            except asyncio.TimeoutError:
                timed_out = True
            else:
                embed_lines = ["Enter the RGB value you wish to set the embed to.  Valid formats:\n",
                                "`[r] [g] [b] - e.g. {0} {1} {2}`".format(*setting.value),
                                "`[r],[g],[b] - e.g. {0},{1},{2}`".format(*setting.value),
                                "`[r], [g], [b] - e.g. {0}, {1}, {2}`".format(*setting.value)]
                reply_embed = EmbedBuilder.fromEmbed(editor_embed) \
                                            .setDescriptionFromLines(embed_lines)
                
                reply_message = await ctx.send(embed=reply_embed.build())

                def validate_msg(msg):
                    return msg.channel.id == reply_message.channel.id and msg.author.id == ctx.author.id
                
                try:
                    reply = await self.bot.wait_for('message', check=validate_msg, timeout=30)
                except asyncio.TimeoutError:
                    reply_embed.setDescription("You took too long to reply!  You can start over using `c.settings admin EMBED_COLOUR edit`")
                    await reply_message.edit(embed=reply_embed.build())
                    return
                else:
                    reply = reply.content.strip()
                    reply_match = re.match(r"^(\d+),? ?(\d+),? ?(\d+)$", reply)
                    valid_rgb = False
                    if reply_match is not None:
                        reply_match = CogHelpers.intmap(reply_match.groups())
                        if min(reply_match) >= 0 and max(reply_match) <= 255:
                            valid_rgb = True
                
                    if not valid_rgb:
                        reply_embed.setDescription("Sorry, `{0}` does not look like a valid RGB value!".format(reply))
                        await reply_message.edit(embed=reply_embed.build())
                        return
                    
                    embed_lines = ["You have set the RGB value for EMBED_COLOUR to `({0}, {1}, {2})`\n".format(*reply_match),
                                    "This embed has been set to have this colour as a preview.",
                                    "Do you wish to update EMBED_COLOUR to this RGB value?"]
                    
                    preview_embed = EmbedBuilder.fromEmbed(reply_embed) \
                                                .setColour(reply_match) \
                                                .setDescriptionFromLines(embed_lines)
                    preview_message = await ctx.send(embed=preview_embed.build())
                    
                    reacts = ['\N{NEGATIVE SQUARED CROSS MARK}','\N{WHITE HEAVY CHECK MARK}']
                    for r in reacts:
                        await preview_message.add_reaction(r)
                    
                    def validate_react_2(react, user):
                        return react.emoji in reacts and react.message.id == preview_message.id and user.id == ctx.author.id
                    
                    try:
                        react, user = await self.bot.wait_for('reaction_add', check=validate_react_2, timeout=30)
                    except asyncio.TimeoutError:
                        preview_embed.setDescription("You took too long to reply!  You can start over using `c.settings admin EMBED_COLOUR edit`")
                        await preview_message.edit(embed=preview_embed.build())
                        return
                    else:
                        if react.emoji == '\N{NEGATIVE SQUARED CROSS MARK}':
                            preview_embed.setDescription("OK!  No action taken, the setting has been left alone")
                            await preview_message.edit(embed = preview_embed.build())
                        elif react.emoji == '\N{WHITE HEAVY CHECK MARK}':
                            setting.value = reply_match
                            setting.save(overwrite=True)
                            preview_embed.setDescription("All set!  The embed RGB colour has been set to `{0}, {1}, {2}`".format(*setting.value))
                            preview_message = await ctx.send(embed=preview_embed.build())

    async def list_menu_handler(self, ctx, setting: BotSetting):
        editor_embed = EmbedBuilder().setTitle("Update List Setting") \
                                        .setColour(BotSettings.get_setting('admin', 'EMBED_COLOUR').value)
        
        action = None
        ended = False
        timed_out = False
        response_type = None
        reply_value = None
        react_index = None
        page = 0
        max_page = ceil(len(setting.value) / 7) - 1

        def get_page_items(page: int):
            page_start = 7 * page
            page_end = min(len(setting.value), page_start + 7)
            return setting.value[page_start:page_end]

        while not ended: # action is None and not timed_out:
            if action is None or action in ['next', 'prev']:
                response_type = 'react'

                if not action is None:
                    if action == 'next':
                        page = min(page + 1, max_page)
                    elif action == 'prev':
                        page = max(0, page - 1)
                    action = None

                reacts = ['\N{WHITE HEAVY CHECK MARK}', '\N{NEGATIVE SQUARED CROSS MARK}']

                embed_lines = ["{0} is set to the list of values shown below.\n".format(setting.token),
                                "To **__add__** a new item, click the \N{WHITE HEAVY CHECK MARK} react",
                                "To **__remove__** an item from the list, click the \N{NEGATIVE SQUARED CROSS MARK} react",
                                "To **__change__** an item, click the corresponding item's react"]

                nav_reacts = []
                if max_page > 0:
                    if page > 0:
                        embed_lines.append("To **__view the previous page__**, click the \N{BLACK LEFT-POINTING TRIANGLE} react")
                        nav_reacts.append('\N{BLACK LEFT-POINTING TRIANGLE}')
                    elif page < max_page:
                        embed_lines.append("To **__view the next page__**, click the \N{BLACK RIGHT-POINTING TRIANGLE} react")
                        nav_reacts.append('\N{BLACK RIGHT-POINTING TRIANGLE}')
        
                embed_lines.append("")

                page_items = get_page_items(page)
                item_idx = 0
                for item in page_items:
                    letter = chr(ord('a') + item_idx)
                    emoji = chr(ord('\N{REGIONAL INDICATOR SYMBOL LETTER A}') + item_idx)
                    embed_lines.append("**{0}**. {1}".format(letter.upper(), item))
                    reacts.append(emoji)
                    item_idx = item_idx + 1
                
                reacts.extend(nav_reacts)

            elif action == 'new':
                if reply_value is None:
                    response_type = 'message'
                    embed_lines = ["To add a new list item to the **{0}** (`{1}`) setting, enter the value to add below".format(setting.display_name, setting.token)]
                else:
                    setting.value.append(reply_value)
                    setting.save(overwrite=True)
                    ended = True
                    continue

            elif action == 'remove':
                if reply_value is None:
                    response_type = 'message'
                    embed_lines = ["To remove a list item from the **{0}** (`{1}`) setting, enter the value to remove below".format(setting.display_name, setting.token)]
                else:
                    if not reply_value in setting.value:
                        response_type = 'message'
                        embed_lines = ["Looks like `{0}` isn't currently a value in this list setting!",
                                        "To remove a list item from the **{0}** (`{1}`) setting, enter the value to remove below".format(setting.display_name, setting.token)]
                    else:
                        setting.value = [x for x in setting.value if not x == reply_value]
                        setting.save(overwrite=True)
                        ended = True
                        continue
            
            elif action == 'change':
                item = setting.value[page*7+react_index]
                if reply_value is None:
                    response_type = 'message'
                    embed_lines = ["To update this list item value (currently `{0}`), enter the value to change it to below".format(item)]
                else:
                    setting.value[page*7+react_index] = reply_value
                    setting.save(overwrite=True)
                    ended = True
                    continue
            
            editor_embed.setDescriptionFromLines(embed_lines)
            editor_message = await ctx.send(embed=editor_embed.build())

            if response_type == 'react':
                for r in reacts:
                    await editor_message.add_reaction(r)

                def validate_react(react, user):
                    return user.id == ctx.author.id and react.emoji in reacts and react.message.id == editor_message.id
                
                try:
                    react, user = await self.bot.wait_for('reaction_add', check=validate_react, timeout=30)
                except asyncio.TimeoutError:
                    timed_out = True
                    ended = True
                else:
                    if react.emoji == '\N{BLACK LEFT-POINTING TRIANGLE}':
                        action = 'prev'
                    elif react.emoji == '\N{BLACK RIGHT-POINTING TRIANGLE}':
                        action = 'next'
                    elif react.emoji == '\N{WHITE HEAVY CHECK MARK}':
                        action = 'new'
                    elif react.emoji == '\N{NEGATIVE SQUARED CROSS MARK}':
                        action = 'remove'
                    else:
                        action = 'change'
                        react_index = ord(react.emoji) - ord('\N{REGIONAL INDICATOR SYMBOL LETTER A}')

            elif response_type == 'message':
                def validate_msg(msg):
                    return msg.author.id == ctx.author.id and msg.channel.id == ctx.channel.id
                
                try:
                    reply = await self.bot.wait_for('message', check=validate_msg, timeout=30)
                except asyncio.TimeoutError:
                    timed_out = True
                    ended = True
                else:
                    reply_value = type(self.value[0])(reply.content.strip()) # I think this is clever :)

        if timed_out:
            embed_lines = ["Sorry, you took too long to respond!\n", "You can start over by using `c.settings {0} {1} {2}`".format(setting.area, setting.token, "edit")]
            editor_embed.setDescriptionFromLines(embed_lines)
            await editor_message.edit(embed=editor_embed.build())
        else:
            editor_embed.setDescription("Successfully updated setting **{0}** (`{1}`)".format(setting.display_name, setting.token))
            await editor_message.edit(embed=editor_embed.build())


    async def edit_setting_handler(self, ctx, setting: BotSetting, action: str):
        action = action.strip()
        args = None
        if " " in action:
            action, args = action.split(" ", 1)
            args = args.strip()
        
        if setting.is_complex() and (args is not None or action != "edit"):
            raise ValueError("Cannot perform this action on this setting")
        elif not setting.is_complex() and (args is None or args == "" or action != "set"):
            raise ValueError("Cannot perform this action on this setting")
        
        if action == "set":
            token_type_casts = {
                'background': {
                    'AWARD_PROCESS_DELAY': int,
                    'AWARD_PROCESS_INTERVAL': int,
                    'PROCESS_AWARDS': CogHelpers.parsebool
                },
                'activity': {
                    'BASE_AWARD_CHANCE': float
                }
            }

            def passthru(x): return x
            value_cast_func = token_type_casts[setting.area].get(setting.token, passthru) if setting.area in token_type_casts else passthru

            setting.value = value_cast_func(args)
            setting.save(overwrite=True)

            edit_embed = EmbedBuilder().setTitle("Successfully Updated Setting") \
                                        .setColour(BotSettings.get_setting('admin', 'EMBED_COLOUR').value) \
                                        .setDescription("Successfully updated **{0}** (`{1}`) to `{2}`".format(setting.display_name, setting.token, setting.value))
            
            await ctx.send(embed=edit_embed.build())
        elif action == "edit":
            if setting.is_simple_list() and not setting.token == 'EMBED_COLOUR':
                await self.list_menu_handler(ctx, setting)
            else:
                # launch per-command handlers
                if setting.token == 'EMBED_COLOUR':
                    await self.embed_colour_handler(ctx, setting)
                elif setting.token == 'AWARD_ENABLED_CHANNELS':
                    await self.award_enabled_channels_handler(ctx, setting)
        

    @commands.command(name='settings')
    @commands.check(CogHelpers.check_is_admin)
    @commands.check(CogHelpers.check_is_channel_or_dm)
    async def manage_settings(self, ctx, area: str=None, token: str=None, *, action: str=None):
        embed_lines = []
        embed_fields = []
        action = None if action is None else action.strip()

        if area is None:
            embed_lines = ["The available settings categories are below.\n"]
            all_areas = BotSettings.get_all_areas()
            embed_lines = embed_lines + ['- `{0}`'.format(x.lower()) for x in all_areas]
        else:
            if token is None:
                try:
                    area_settings = BotSettings.get_all_area_settings(area)
                except DocumentNotFoundError:
                    embed_lines = ["Looks like the configuration area `{0}` doesn't exist!".format(area)]
                else:
                    embed_lines = ["The below settings exist within the `{0}` configuration area:\n".format(area)]
                    for setting_token in area_settings:
                        setting = area_settings[setting_token]
                        embed_lines.append("- ** {0}** (`{1}`) ".format(setting.display_name, setting.token))
                    embed_lines.extend(["", "To view more information about a setting, including its current value, use `c.settings {0} [setting]`".format(area)])
            else:
                try:
                    setting = BotSettings.get_setting(area, token)
                except DocumentNotFoundError:
                    embed_lines = ["Looks like the setting `{0}` in configuration area `{1}` doesn't exist!".format(token, area)]
                else:
                    if not action is None and not action == "":
                        await self.edit_setting_handler(ctx, setting, action)
                        return

                    embed_lines = ["Information for this setting is below.",
                                    "Note that `[]` around a value means a list, and `...` in a value means a complex-structured setting.\n"]
                    embed_lines.append("To edit this setting, use this command:")
                    if setting.is_complex():
                        embed_lines.append("`c.settings {0} {1} edit`".format(area, token))
                    else:
                        embed_lines.append("`c.settings {0} {1} set [new value]`".format(area, token))
                    embed_lines.append("")  
                    embed_fields = [
                        {
                            'name': "Name/Token",
                            'value': token,
                            'inline': False,
                        },
                        {
                            'name': "Display Name",
                            'value': setting.display_name,
                            'inline': False,
                        }
                    ]
                    if setting.has_description():
                        embed_fields.append({
                            'name': "Description",
                            'value': setting.description,
                            'inline': False
                        })
                    embed_fields.append({
                        'name': "Value",
                        'value': setting.value_str(),
                        'inline': False,
                    })
        
        settings_embed = EmbedBuilder().setTitle("Settings Management") \
                                        .setColour(BotSettings.get_setting('admin', 'EMBED_COLOUR').value) \
                                        .setDescriptionFromLines(embed_lines)
        
        for field in embed_fields:
            settings_embed.addField(field)
        
        await ctx.send(embed=settings_embed.build())

def setup(bot):
    bot.add_cog(SettingsCog(bot))