
# Server Overview

This WebSocket server facilitates real-time communication and manages game lobbies. It handles various operations related to game lobby management, such as creating, listing, joining, and leaving lobbies.

## WebSocket Events

The server handles several key actions through WebSocket communication:

- `check_game_start`: Checks if a game can start based on current conditions.
- `clear_lobbies`: Clears out lobbies based on certain criteria (e.g., inactivity or completion).
- `notify_lobby`: Sends a message to all members of a specific lobby.
- `action_create`: Handles lobby creation requests.
- `action_list`: Handles requests to list current lobbies.


## Using Test Scripts

### Test Basic Functionalityu

The `test_basic_functionality.py` script focuses on basic functionality: create, join, leave.

To run it:
```bash
python test_basic_functionality.py
```


### Test Players Interaction

The `test_players_interation.py` script focuses on interactions between multiple clients within lobbies:

- Test multi-client interactions within the lobby, ensuring that actions like joining and leaving are properly synchronized across clients.


To run it:
```bash
python test_players_interation.py
```

## Requirements

- Python 3.7 or higher
- `websockets` library for WebSocket communication
- `asyncio` for asynchronous programming

Install the necessary Python packages using `pip`:

```bash
pip install websockets asyncio
```

## Running the Server

To start the server, navigate to the directory containing the `server.py` file and run:

```bash
python server.py
```

Ensure you have the necessary permissions and environment to run a WebSocket server on the specified host and port.

