import asyncio
import websockets
import json
import uuid
import unittest

class WebSocketServerTest(unittest.TestCase):
    """
    Test class for WebSocket server functionalities focusing on multi-client interactions.
    """

    async def create_lobby(self, ws, player_id):
        """
        Create a lobby using the provided WebSocket connection.
        """
        print(f"[{player_id}] Sending request to create lobby...")
        await ws.send(json.dumps({"action": "create", "player": player_id}))
        response = await ws.recv()
        print(f"[{player_id}] Lobby creation response: {response}")
        return json.loads(response)['lobby_id']

    async def list_lobbies(self, ws, player_id):
        """
        List all available lobbies using the provided WebSocket connection.
        """
        print(f"[{player_id}] Sending request to list lobbies...")
        await ws.send(json.dumps({"action": "list", "player": player_id}))
        response = await ws.recv()
        print(f"[{player_id}] Lobbies list response: {response}")
        return json.loads(response)['lobbylist']

    async def join_lobby(self, ws, player_id, lobby_id):
        """
        Join a specific lobby using the provided WebSocket connection.
        """
        print(f"[{player_id}] Sending request to join lobby {lobby_id}...")
        await ws.send(json.dumps({"action": "join", "player": player_id, "lobby_id": lobby_id}))
        response = await ws.recv()
        print(f"[{player_id}] Join lobby response: {response}")
        return json.loads(response)

    async def test_multi_client_lobby(self):
        """
        Test the workflow where multiple clients interact with the lobby system.
        """
        print("Starting multi-client lobby test...")
        async with websockets.connect("ws://localhost:8765") as ws1, \
                   websockets.connect("ws://localhost:8765") as ws2:
            print("Connected both clients to the server.")

            player1 = str(uuid.uuid4())
            lobby_id = await self.create_lobby(ws1, player1)
            print(f"[{player1}] Created lobby with ID: {lobby_id}")

            player2 = str(uuid.uuid4())
            print(f"[{player2}] is going to list lobbies...")
            lobbies = await self.list_lobbies(ws2, player2)
            print(f"[{player2}] Available lobbies: {lobbies}")

            print(f"[{player2}] Joining lobby {lobby_id}...")
            await self.join_lobby(ws2, player2, lobby_id)

            print(f"[{player1}] Waiting for notification of {player2} joining...")
            join_notification = await ws1.recv()
            print(f"[{player1}] Received join notification: {join_notification}")

            print(f"[{player1}] Waiting for game start notification...")
            game_start_notification = await ws1.recv()
            print(f"[{player1}] Received game start notification: {game_start_notification}")

async def run_async_test():
    """
    Main entry point to run the async test case.
    """
    print("Initializing the async test case...")
    timeout = 20  # seconds, increase if needed
    try:
        await asyncio.wait_for(WebSocketServerTest().test_multi_client_lobby(), timeout)
        print("Multi-client lobby test completed successfully.")
    except asyncio.TimeoutError:
        print(f'Test did not complete within {timeout} seconds. It might be hanging.')
    except Exception as e:
        print(f"An error occurred during the test: {e}")

if __name__ == "__main__":
    print("Starting the test script...")
    asyncio.get_event_loop().run_until_complete(run_async_test())
    print("Test script execution finished.")
