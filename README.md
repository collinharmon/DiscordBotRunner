# DiscordBotRunner

A Discord Bot that can dynamically load and run any number of arbitrary Discord Bots.

## Description
DiscordBotRunner was made to be able to dynamically load and run any number of arbitrary Discord bots under a single Discord Bot instance. That way a single Discord Bot can run theoretically an infinite number of "Discord Bots."

DiscordBotRunner runs a given "Discord Bot" by importing and running an implementation of a "BehaviorSet," which is an abstract class that inherits the Thread class. Users define the Discord Bot's behavior by implementing the BehaviorSet class and can then have the DiscordBotRunner "load" and run them as individual threads.

The defined BehaviorSet can then be provided to the DiscordBotRunner either dynamically or from the outset on initialization. The DiscordBotRunner will import the BehaviorSet and module dependencies and then run the BehaviorSet as a new thread.
After at least one BehaviorSet is loaded, Discord channels and users can be registered to use the BehaviorSet (see admin commands below). This is how a BehaviorSet 'subscribes' to input. 

The DiscordBotRunner will relay the inputs from a Discord User/Channel pair to a BehaviorSet if the former is registered/authorized to use the BehaviorSet (see registration command below).

Any data a BehaviorSet would like to send to a Discord channel is sent to the DiscordBotRunner to handle the forwarding to the Discord Guild and appropriate channel.

Communication between BehaviorSets and DiscordBotRunner is done by using queues from the `queue` package. DiscordBotRunner has a single queue to handle message publishes by all child threads, or BehaviorSets. Each BehaviorSet has its own queue for DiscordBotRunner (the parent thread) to push to.


Since DiscordBotRunner allows any Python program to be dynamically loaded and ran through Discord (and treat Discord channels as if they are terminals to a Python interpreter), any Guild which uses this bot becomes "Turing Complete"--since Python itself is Turing Complete. The ability for this Discord Bot to dynamically load and run any arbitrary Discord Bot echoes this spirit of Turing Completeness (Turing Machine vs Universal Turing Machine).

## Notes

`/DiscordBotRunner/behavior_sets/` is the relative path to the folder the DiscordBotRunner looks at for loading BehaviorSet implementations upon initialization. It is also the location the DiscordBotRunner will store dynamically loaded BehaviorSets and Python modules. External modules which a given BehaviorSet implementation may use should be imported by the BehaviorSet implementation in a relative fashion (See QouteBot BehaviorSet example under `/DiscordBotRunner/behavior_sets/`). 

## Admin Commands

Administrative commands begin with `./admin` and can be executed in any channel provided the DiscordBotRunner is listening on the Guild from which the commands are sent. By default the command responses are disabled (see log command). To set the ADMIN to a specific discord user modify the value, `user_id`, in the `/discord_bot_runner/keys/admin.ini` config file (e.g. for me it's #aces#5802).

* `./admin log`
  * Description: This command takes exactly one argument, `enable` or `disable` for toggling the admin error and message log.
  * Format:      `./admin log enable`

* `./admin register` (`reg` for short)
	* Description: Registers channels and users on a given behavior set.
	* Format:      `./admin register @some_discord_user, #somechannel on <name of BehaviorSet to register on>`
	* Notes:       `@all` and `#all` will register every user and every channel on the provided BehaviorSet, respectively.

* `./admin remove` (`rm` for short)
	* Description: Removes/Unregisters channels and users on a given behavior set.
	* Format:      `./admin remove @some_discord_user, #somechannel on <name of BehaviorSet to register on>`
	* Notes:       `@all` and `#all` will unregister every user and every channel on the provided BehaviorSet, respectively.

* `./admin show`
	* Description: Shows the available BehaviorSets that have been loaded by the DiscordBotRunner. Or if the name of a loaded BehaviorSet is provided as an argument, show the users and channels that are registered on it.
	* Format:      `./admin show`
  * `./admin show <name of behavior set>`

* `./admin load`
  * Description: Providing this command along with .py file attachments will attempt to load the and import the Python modules.
  * Format:      `./admin load` with provided attachments
  * Notes:       Currently, dragging and dropping files into the Discord Channel chat box will prompt the user to also provide a message with the attachment. This is where the user should provide `./admin load`. If a BehaviorSet has dependencies then simply load each dependency the same way. The ordering of the uploads/imports does not matter.

# Pictorial Examples of admin commands

![./admin show](img/admin_show_1.PNG "`./admin show`")

![`./admin register, log enable, and show (2)`](img/admin_show_2.PNG)

![`./admin remove`](img/admin_remove.PNG)

![`./quotes`](img/quotes_get.PNG)

![`./admin load (1/4)`](img/admin_load_1.PNG)

![`./admin load (2/4)`](img/admin_load_2.PNG)

![`./admin load (3/4)`](img/admin_load_3_1.PNG)

![`./admin load (4/4)`](img/admin_load_3_2.PNG)


## Built With

* [Python3](https://www.python.org/) - The Python version used

## Contributing

Got a cool feature to add? Submit a pull request and I'll take a look.

## Authors

* **Collin Harmon** [Github](https://github.com/CollinHarmon)

## Acknowledgments

