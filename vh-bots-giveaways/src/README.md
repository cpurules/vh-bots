# VH Giveaway Bot

This is a custom Discord bot written to conduct Villager Haven giveaways.  It performs the following tasks:
* Creates a single giveaway post for server members to react to
* Selects the specified number of unique winners
* Creates an appropriate number of winner channels and roles
* Assigns the appropriate permissions to the winner channels
* Posts a congratulatory message for the winners in the channels

It also allows approved roles to do the following:
* Generate reports on courier deliveries
* Generate reminder messages and auto-clean roles from finished winners
* Clean up channels/roles associated with giveaways/events
* Create blank event/giveaway channels

# Features to (Maybe) Implement
* On startup, validate pitfall emoji - events team ping - category channel
  * Will require guild ID configuration entry

# Requirements
* Python3
* discord.py
* Bot permissions: 268463184
  * Manage Roles
  * Manage Channels
  * View Channels
  * Send Messages
  * Manage Messages
  * Embed Links
  * Add Reactions
  * Needs to have the members intent
  * (as of 1/25/2021) just give it Administrator something is weird with VH
    perms
