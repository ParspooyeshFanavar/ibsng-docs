## IBSng Command-line Interface

This is an inter-active command-line interface for IBSng JSON-RPC API.

### Dependencies

- Python >= 3.11
- `python3 -m pip install prompt_toolkit`

### Usage

Simply run `python3 cli.py` or `./cli.py`

It takes no command-line arguments. And no mandatory environment variables.

### Keyboard

In every prompt:

- Press Tab to see the options (if available / applicable).
- Press Up or Down to access history
- Press Control + C to go back to previous step:
	+ Except in sub-parameters of an "object" parameter:
		- It moves on from that object, leaving the rest of sub-parameters empty

In `>> Method:` prompt:

- Enter `r` to re-send the last request.
- Enter `q` to quit / exit cli.

### Optional Environment Variables

You can set these environment variables if you to avoid entering them every time you run the CLI.

- `IBS_AUTH_TYPE`: `ADMIN`, `NORMAL_USER`, `VOIP_USER`
- `IBS_AUTH_NAME`: Admin name or username
- `IBS_AUTH_PASS`
- `IBS_ADDR`: for example `http://127.0.0.1:1237`
- `IBS_BRANCH`: `E`, `D` or `C`


