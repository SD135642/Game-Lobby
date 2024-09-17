import argparse
import asyncio
import websockets
import json
import uuid
from datetime import datetime

# Global settings and variables
CONNECTED_CLIENTS = set()
MINIMUM_PLAYERS_TO_START_THE_GAME = 2
PING_INTERVAL = 1
DEFAULT_PORT = 8765
DEFAULT_HOST = 'localhost'
lobby_server = None

class Player:
    """
    Represents a player connected to the server.
    """

    def __init__(self, websocket, id, lobby_id=None):
        """
        Initializes a new Player instance.

        @param websocket: The WebSocket connection for the player.
        @param id: Unique identifier for the player.
        @param lobby_id: Identifier of the lobby the player is currently in, if any.
        """
        self.websocket = websocket
        self.id = id
        self.lobby_id = lobby_id


class Lobby:
    """
    Manages a lobby of players waiting to start a game.
    """

    def __init__(self, id):
        """
        Initializes a new Lobby instance.

        @param id: Unique identifier for the lobby.
        """
        self.players = {}
        self.id = id

    async def notify(self, message, game_started=False):
        """
        Sends a notification message to all players in the lobby.

        @param message: Message to be sent to the players.
        @param game_started: Boolean flag indicating if the game has started.
        """
        for player_id in self.players.keys():
            await self.players[player_id].websocket.send(json.dumps({
                "message": message,
                "lobby_id": self.id,
                "game_started": game_started
            }))


class LobbyServer:
    """
    Manages the entire lobby server, including player connections and lobby management.
    """

    def __init__(self):
        """
        Initializes the LobbyServer.
        """
        self.lobbies = {}
        self.players = {}

    async def check_game_start(self):
        """
        Checks each lobby to see if the game can start based on the number of connected players.
        """
        start_lobbies_ids = set()
        delete_players_ids = set()
        for lobby in self.lobbies.values():
            if len(lobby.players) >= MINIMUM_PLAYERS_TO_START_THE_GAME:
                start_lobbies_ids.add(lobby.id)
                for player in lobby.players.values():
                    delete_players_ids.add(player.id)

        for lobby_id in start_lobbies_ids:
            await self.lobbies[lobby_id].notify(f"Starting Game In Lobby {lobby_id}", game_started=True)
            del self.lobbies[lobby_id]

        for player_id in delete_players_ids:
            del self.players[player_id]

    async def clear_lobbies(self):
        """
        Clears out empty lobbies and removes disconnected players from lobbies.
        """
        delete_lobbies_ids = set()
        for lobby in self.lobbies.values():
            lobby_id = lobby.id
            delete_players = set()
            for player in lobby.players.values():
                if player.websocket not in CONNECTED_CLIENTS:
                    print(f"{player.id} disconnected!")
                    delete_players.add(player.id)

            for player_id in delete_players:
                del lobby.players[player_id]
                del self.players[player_id]
                await lobby.notify(f"player {player_id} left the lobby")

            if not lobby.players:
                delete_lobbies_ids.add(lobby_id)

        for lobby_id in delete_lobbies_ids:
            print(f"lobby {lobby_id} is empty so get removed")
            del self.lobbies[lobby_id]

    async def action_create(self, player_id, websocket):
        """
        Handles the creation of a new lobby by a player.

        @param player_id: The unique identifier of the player creating the lobby.
        @param websocket: The WebSocket connection of the player.
        """
        if player_id not in self.players:
            self.players[player_id] = Player(websocket, player_id)

        player = self.players[player_id]
        lobby = Lobby(str(uuid.uuid4()))
        self.lobbies[lobby.id] = lobby
        lobby.players[player_id] = player

        if player.lobby_id is not None:
            await self.action_leave(player_id)

        player.lobby_id = lobby.id
        await lobby.notify(f"Lobby {lobby.id} created by Player {player_id}")

    async def action_list(self, websocket):
        """
        Sends a list of all available lobbies to the player.

        @param websocket: The WebSocket connection of the player requesting the list.
        """
        await websocket.send(json.dumps({"lobbylist": list(self.lobbies.keys())}))

    async def action_join(self, player_id, lobby_id, websocket):
        """
        Handles a player's request to join a specific lobby.

        @param player_id: The unique identifier of the player joining the lobby.
        @param lobby_id: The identifier of the lobby to join.
        @param websocket: The WebSocket connection of the player.
        """
        if player_id not in self.players:
            self.players[player_id] = Player(websocket, player_id)

        player = self.players[player_id]
        lobby = self.lobbies.get(lobby_id)

        if not lobby:
            await player.websocket.send(json.dumps({"message": f"cannot join {lobby_id}"}))
        else:
            lobby.players[player_id] = player
            await lobby.notify(f"Player {player.id} joined to lobby: {lobby.id}")

    async def action_leave(self, player_id):
        """
        Handles a player's request to leave their current lobby.

        @param player_id: The unique identifier of the player leaving the lobby.
        """
        player = self.players.get(player_id)
        await self.lobbies[player.lobby_id].notify(f"player {player_id} is leaving lobby {player.lobby_id}")

        if player and player.lobby_id:
            lobby = self.lobbies[player.lobby_id]
            del lobby.players[player_id]
            player.lobby_id = None
            await self.clear_lobbies()


async def process_message(websocket, message):
    """
    Processes incoming messages from clients, delegating to specific actions based on the message content.

    @param websocket: The WebSocket connection of the sender.
    @param message: The raw JSON message received from the client.
    """
    data = json.loads(message)
    action = data.get("action")
    player_id = data.get('player')
    lobby_id = data.get('lobby_id')

    if action is None or player_id is None or player_id == "":
        print(f"WARNING: there should be action and player fields in payload: {data=}")
    elif action == "create":
        await lobby_server.action_create(player_id, websocket)
    elif action == "join":
        await lobby_server.action_join(player_id, lobby_id, websocket)
    elif action == "list":
        await lobby_server.action_list(websocket)
    elif action == "leave":
        await lobby_server.action_leave(player_id)

async def handle_connection(websocket, path):
    """
    Manages incoming WebSocket connections, processing messages and maintaining the list of connected clients.

    @param websocket: The WebSocket connection of the client.
    @param path: The HTTP path used to establish the WebSocket connection.
    """
    CONNECTED_CLIENTS.add(websocket)
    try:
        async for message in websocket:
            await process_message(websocket, message)
    except websockets.exceptions.ConnectionClosedOK:
        print("Client Disconnected. Connection closed normally.")
    except websockets.exceptions.ConnectionClosed:
        print("Client Disconnected")
    finally:
        CONNECTED_CLIENTS.remove(websocket)
        await lobby_server.clear_lobbies()

async def ping_clients():
    """
    Periodically pings all connected clients to check if they are alive and manages game start conditions.
    """
    while True:
        print(f"[{ts()}] [heartbeat] Pinging clients, connected clients: {len(CONNECTED_CLIENTS)}")
        await lobby_server.check_game_start()
        disconnected_clients = []
        for websocket in CONNECTED_CLIENTS:
            try:
                await websocket.ping()
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.append(websocket)
        for websocket in disconnected_clients:
            CONNECTED_CLIENTS.remove(websocket)
            await lobby_server.clear_lobbies()
        await asyncio.sleep(PING_INTERVAL)

def ts():
    """
    Gets the current timestamp in a human-readable format.

    @return: Current timestamp formatted as "YYYY-MM-DD HH:MM:SS".
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def main():
    """
    Main entry point for the server application. Starts the WebSocket server and the periodic pinging task.
    """
    global lobby_server
    lobby_server = LobbyServer()

    parser = argparse.ArgumentParser(description="Start the WebSocket server for Lobby Game processing.")
    parser.add_argument("--host", type=str, default=DEFAULT_HOST, help="Host address to bind the server to.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port number to bind the server to.")

    args = parser.parse_args()

    print(f'Running the server with the following configuration: {args}')

    start_server = websockets.serve(handle_connection, args.host, args.port)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_server)

    asyncio.ensure_future(ping_clients())

    loop.run_forever()

if __name__ == "__main__":
    main()
