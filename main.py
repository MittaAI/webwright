import asyncio

async def main():
    # Presuming there's an async main() function you'd call
    pass


def entry_point():
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("system> Exiting gracefully...")
        # Cancel all running tasks
        for task in asyncio.all_tasks():
            task.cancel()
        # Wait until all tasks are cancelled
        asyncio.get_event_loop().run_until_complete(asyncio.gather(*asyncio.all_tasks(), return_exceptions=True))


from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.clipboard import ClipboardData

bindings = KeyBindings()

# Intercept Ctrl+V
@bindings.add('c-v')
def _(event):
    print("system> Use mouse right-click to paste.\n")
    clipboard_data = event.app.clipboard.get_data()
    if isinstance(clipboard_data, ClipboardData):
        event.current_buffer.insert_text(clipboard_data.text)
