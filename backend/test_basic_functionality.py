import asyncio
import websockets
import json
import uuid
import unittest

class WebSocketServerTest(unittest.TestCase):
    """
    Test class for WebSocket server functionalities.
    """

    @staticmethod
    async def create_lobby(ws, player_id):
        print("Creating lobby...")
        await ws.send(json.dumps({"action": "create", "player": player_id}))
        response = await ws.recv()
        print(f"Lobby created: {response}")
        return json.loads(response)

    @staticmethod
    async def list_lobbies(ws, player_id):
        print("Listing lobbies...")
        await ws.send(json.dumps({"action": "list", "player": player_id}))
        response = await ws.recv()
        print(f"Lobbies listed: {response}")
        return json.loads(response)

    @staticmethod
    async def join_lobby(ws, player_id, lobby_id):
        print(f"Joining lobby {lobby_id}...")
        await ws.send(json.dumps({"action": "join", "player": player_id, "lobby_id": lobby_id}))
        response = await ws.recv()
        print(f"Joined lobby: {response}")
        return json.loads(response)

    @staticmethod
    async def leave_lobby(ws, player_id):
        print(f"Leaving player lobby...")
        await ws.send(json.dumps({"action": "leave", "player": player_id}))
        response = await ws.recv()
        print(f"Left lobby: {response}")
        return json.loads(response)

    async def test_lobby_workflow(self):
        print("Starting lobby workflow test...")
        async with websockets.connect("ws://localhost:8765") as ws:
            player_id = str(uuid.uuid4())
            print(f"Testing with player ID: {player_id}")

            create_response = await self.create_lobby(ws, player_id)
            self.assertIn('lobby_id', create_response, "Lobby creation failed to return lobby_id.")

            lobby_id = create_response['lobby_id']
            print(f"Lobby ID obtained: {lobby_id}")

            list_response = await self.list_lobbies(ws, player_id)
            self.assertIn(lobby_id, list_response['lobbylist'], "Created lobby not found in lobby list.")

            join_response = await self.join_lobby(ws, player_id, lobby_id)
            self.assertEqual(join_response['lobby_id'], lobby_id, "Failed to join the created lobby.")

            leave_response = await self.leave_lobby(ws, player_id)
            self.assertNotIn(player_id, leave_response.get('players', {}), "Failed to leave the lobby correctly.")

async def run_async_test():
    timeout = 10  # seconds
    try:
        print("Running lobby workflow test with timeout...")
        await asyncio.wait_for(WebSocketServerTest().test_lobby_workflow(), timeout)
        print("Test completed successfully.")
    except asyncio.TimeoutError:
        print(f'Test did not complete within {timeout} seconds. It might be hanging.')
    except Exception as e:
        print(f"An error occurred during the test: {e}")

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(run_async_test())
