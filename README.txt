README

DiscordBotRunner

DiscordBotRunner was made to be able to dynamically load and run any number of arbitrary Discord bots under a single Discord Bot instance. That way a single Discord Bot can run theoretically an infinite number of "Discord Bots."

DiscordBotRunner runs "Discord Bots" by importing and running an implementation of a "BehaviorSet," which is an abstract class that inherits the Thread class. Users define the Discord Bot's behavior by implementing the BehaviorSet class and can then have the DiscordBotRunner "load" them as individual threads.

The defined BehaviorSet can then be provided to the DiscordBotRunner either dynamically or from the outset on initialization. The DiscordBotRunner will import the BehaviorSet and module dependencies and then run the BehaviorSet as a new thread.
After at least one BehaviorSet is loaded, Discord channels and users can be registered to use the BehaviorSet (see admin commands below). This is how a BehaviorSet 'subscribes' to input. 

The DiscordBotRunner will relay the inputs from a Discord User/Channel pair to a BehaviorSet if the former is registered/authorized to use the BehaviorSet (see registration command below).

Any data a BehaviorSet would like to send to a Discord channel or user is sent to the DiscordBotRunner to handle the sending to the Discord Server and appropriate channel.
Communication between BehaviorSets and DiscordBotRunner is done by using queues from the `queue` package. DiscordBotRunner has a single queue to handle message publishes by all BehaviorSets. Each BehaviorSet has its own queue for DiscordBotRunner to push to.

Since DiscordBotRunner allows any Python program to be dynamically loaded and ran through Discord (and treat Discord channels as if they are terminals to a Python interpreter), any Guild which uses this bot becomes "Turing Complete"--since Python itself is Turing Complete. The ability for this Discord Bot to dynamically load and run any arbitrary Discord Bot echoes this spirit of Turing Completeness (Turing Machine vs Universal Turing Machine).


Admin Commands
Administrative commands begin with `./admin` can be executed in any channel provided the DiscordBotRunner is listening on the Guild from which the commands are sent. By default the command responses are disabled (see log command).

`./admin log`
	Description: This command takes exactly one argument, `enable` or `disable` for toggling the admin error and message log.
	Format:      `./admin log enable`
	
`./admin register` (`reg` for short)
	Description: Registers channels and users on a given behavior set.
	Format:      `./admin register @some_discord_user, #somechannel on <name of BehaviorSet to register on>`
	Notes:       `@all` and `#all` will register every user and every channel on the provided BehaviorSet, respectively.
	
`./admin remove` (`rm` for short)
	Description: Removes/Unregisters channels and users on a given behavior set.
	Format:      `./admin remove @some_discord_user, #somechannel on <name of BehaviorSet to register on>`
	Notes:       `@all` and `#all` will unregister every user and every channel on the provided BehaviorSet, respectively.
	
`./admin show`
	Description: Shows the available BehaviorSets that have been loaded by the DiscordBotRunner. Or if the name of a loaded BehaviorSet is provided as an argument, show the users and channels that are registered on it.
	Format:      `./admin show`
	              `./admin show <name of behavior set>`

`./admin load`
	Description: Providing this command along with .py file attachments will attempt to load the and import the Python modules.
	Format:      `./admin load` with provided attachments
	Notes:       Currently, dragging and dropping files into the Discord Channel chat box will prompt the user to also provide a message with the attachment. This is where the user should provide `./admin load`

