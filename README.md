# DiscordBotRunner

A Discord Bot that can dynamically load and run any number of arbitrary Discord Bots.

## Description
DiscordBotRunner was made to be able to dynamically load and run any number of arbitrary Discord bots under a single Discord Bot instance. That way a single Discord Bot can run theoretically an infinite number of "Discord Bots."

DiscordBotRunner runs a given "Discord Bot" by importing and running an implementation of a "BehaviorSet," which is an abstract class that inherits the Thread class. Users define the Discord Bot's behavior by implementing the BehaviorSet class and can then have the DiscordBotRunner "load" and run them as individual threads.

The defined BehaviorSet can then be provided to the DiscordBotRunner either dynamically or from the outset on initialization. The DiscordBotRunner will import the BehaviorSet and module dependencies and then run the BehaviorSet as a new thread.
After at least one BehaviorSet is loaded, Discord channels and users can be registered to use the BehaviorSet (see admin commands below). This is how a BehaviorSet 'subscribes' to input. 

The DiscordBotRunner will relay the inputs from a Discord User/Channel pair to a BehaviorSet if the former is registered/authorized to use the BehaviorSet (see registration command below).

Any data a BehaviorSet would like to send to a Discord channel is sent to the DiscordBotRunner to handle the forwarding to the Discord Guild and appropriate channel.

Communication between BehaviorSets and DiscordBotRunner is done by using queues from the `queue` package. DiscordBotRunner has a single queue to handle message publishes by all child threads, or BehaviorSets. Each BehaviorSet has its own queue for DiscordBotRunner (the parent thread) to push to. The message data pushed onto the queues is JSON data. See the Notes section for examples of the "schema" which defines the JSON data passed between threads (An actual JSON schema to validate the messages TBD).


Since DiscordBotRunner allows any Python program to be dynamically loaded and ran through Discord (and treat Discord channels as if they are terminals to a Python interpreter), any Guild which uses this bot becomes "Turing Complete"—since Python itself is Turing Complete. The ability for DiscordBotRunner to dynamically load and run any arbitrary Discord Bot compared to a standard Discord Bot—whose behavior is static and constrained to a single input/output framework, echoes this spirit of Turing Completeness (Universal Turing Machine as compared to the Turing Machine). Somewhat silly, but thought why write a Discord bot when I could write a Discord Bot that can run any kind of Discord Bot?

## Notes

*	`/DiscordBotRunner/behavior_sets/` is the relative path to the folder the DiscordBotRunner looks at for loading BehaviorSet implementations upon initialization. It is also the location the DiscordBotRunner will store dynamically loaded BehaviorSets and Python modules. External modules which a given BehaviorSet implementation may use should be imported by the BehaviorSet implementation in a relative fashion (See QuoteBot BehaviorSet example under `/DiscordBotRunner/behavior_sets/`). 

*	The data the child threads push onto the parent queue is JSON data which abides the following "schema" (TODO create actual schema .json file to validate JSON data)
	*	text_message: `{"channel":<integer id of target channel>, "data_type":"text_message", "data":"<Any sort of text data goes here>"}`
	*	file_path:    `{"channel":<integer id of target channel>, "data_type":"file_path",    "file_path":"<path of file to be uploaded>"}`
	*	text/upload:  `{"channel":<integer id of target channel>, "data_type":"text/upload",  "data":"<Any sort of text data goes here>", "file_path":"<path of file to be uploaded>"}`

Check out the MarketBehaviorSet Discord Bot [MarketBehaviorSet](https://github.com/collinharmon/MarketBehaviorSet)!

## Admin Commands

Administrative commands begin with `./admin` and can be executed in any channel provided the DiscordBotRunner is listening on the Guild from which the commands are sent. By default the command status responses are disabled (see log command). To set the ADMIN to a specific Discord user modify the value, `user_id`, in the `/discord_bot_runner/keys/admin.ini` config file (e.g. for me it's aces#5802).

* `./admin log`
  * Description: This command takes exactly one argument, `enable` or `disable` for toggling the admin error and message log.
  * Format:      `./admin log enable`

* `./admin register` (`reg` for short)
	* Description: Registers channels and users on a given BehaviorSet.
	* Format:      `./admin register @some_discord_user, #somechannel on <name of BehaviorSet to register on>`
	* Notes:       `@all` and `#all` will register every user and every channel on the provided BehaviorSet, respectively.

* `./admin remove` (`rm` for short)
	* Description: Removes/Unregisters channels and users on a given BehaviorSet.
	* Format:      `./admin remove @some_discord_user, #somechannel on <name of BehaviorSet to register on>`
	* Notes:       `@all` and `#all` will unregister every user and every channel on the provided BehaviorSet, respectively.

* `./admin show`
	* Description: Shows the available BehaviorSets that have been loaded by the DiscordBotRunner. Or if the name of a loaded BehaviorSet is provided as an argument, show the users and channels that are registered on it.
	* Format:      `./admin show`
  * `./admin show <name of BehaviorSet>`

* `./admin load`
  * Description: Providing this command along with .py file attachments will attempt to load the and import the Python modules.
  * Format:      `./admin load` with provided attachments
  * Notes:       Currently, dragging and dropping files into the Discord Channel chat box will prompt the user to also provide a message with the attachment. This is where the user should provide `./admin load`. If a BehaviorSet has dependencies then simply load each dependency the same way. The ordering of the uploads/imports does not matter.

## Configuration

# Pictorial Examples of admin commands

![./admin show](img/admin_show_1.PNG "`./admin show`")

![`./admin register, log enable, and show (2)`](img/admin_show_2.PNG)

![`./admin remove`](img/admin_remove.PNG)

![`./quotes`](img/quotes_get.PNG)

![`./admin load (1/4)`](img/admin_load_1.PNG)

![`./admin load (2/4)`](img/admin_load_2.PNG)

![`./admin load (3/4)`](img/admin_load_3_1.PNG)

![`./admin load (4/4)`](img/admin_load_3_2.PNG)

### Reloading a module:
![`./admin load (4/4)`](img/admin_load_reload.PNG)


## Built With

* [Python3](https://www.python.org/) - The Python version used

## Contributing

Got a cool feature to add? Submit a pull request and I'll take a look.

## Authors

* **Collin Harmon** [Github](https://github.com/CollinHarmon)

## Acknowledgments

