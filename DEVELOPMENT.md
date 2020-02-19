# Plugin Development
PagerMaid has a powerful plugin system, which enables convenient debugging of code sharing. This document explains
 how to use the PagerMaid framework to develop your own PagerMaid plugin, and share code you have written for the
 platform.

## Plugin Manager
The plugin manager is a utility to help you manage and share plugins installed to your PagerMaid instance.

### Install
To install a plugin, issue the plugin command replying to a message containing the plugin in it's attachments, with the
 install argument. PagerMaid will download and validate the plugin, and restart after it is installed.

### Remove
To remove a plugin, issue the plugin command with the remove argument, and append the plugin name after the argument,
 PagerMaid will look for the plugin and if present, remove it and restart.

### Enable
To enable a disabled plugin, issue the plugin command with the enable argument, and append the plugin name after the
 argument, PagerMaid will look for the plugin and if present and disabled, enable it and restart.

### Disable
To disable an enabled plugin, issue the plugin command with the disable argument, and append the plugin name after the
 argument, PagerMaid will look for the plugin and if present and enabled, disable it and restart.

### Upload
To upload a plugin, issue the plugin command with the upload argument, and append the plugin name after the argument,
 PagerMaid will look for the plugin and if present, upload it to the current chat.

### Status
To view the status of plugins, issue the plugin command with the status argument, active plugins refer to plugins that
 are enabled and loaded, failed plugins refer to plugins that are enabled but failed to load, disabled plugins refer to
 plugins that are disabled.

## Event Listener
The most important part of a plugin is the event listener, which is how commands are implemented. To register an event
 listener, import listener from pagermaid.listener and use the listener annotation on an async class.

```python
""" Plugin description. """
from pagermaid.listener import listener


@listener(outgoing=True, command="command", diagnostics=False, ignore_edited=False,
          description="My PagerMaid plugin command.",
          parameters="<name>")
async def command(context):
    await context.edit(f"Hello, World! Welcome, {context.parameter[0]}.")
```

The outgoing variable specifies if the message has to be sent by the user, if it is set to False the event listener
 will be invoked on every single message event.

The command variable specifies the command used to trigger the event listener, which will insert the arguments of the
 command to context.pattern_match.group(1).

The pattern variable specifies a regex pattern that overrides the command to be used to trigger the event listener. Case
 insensitivity is implemented within the listener.

The diagnostics variable specifies if exceptions of the event listener is handled by the diagnostics module which sends
 the error report to Kat, defaults to True, you should disable it if you are using exceptions to trigger events.

The ignore_edited variable specifies if the event listener will be triggered by an edit of a message, defaults to False.

The description variable specifies the description that will appear in the help message.

the parameters variable specifies the parameters indicator that will appear in the help message.

## Logging
The PagerMaid framework includes two sets of logging: console and in-chat logging. In-Chat logging respects the
 configuration file. To use logging, import log from the pagermaid class.

```python
from pagermaid import log
await log("This is a log message!")
```

The logging handler will output an entry to the console, and, if configured, will send a message into the logging
 channel the user specified. Beware that log() is a coroutine object, so please do not forget to await it.