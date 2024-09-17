let currentLobby = null;

function checkName() {
    const name = document.getElementById("playerName").value.trim();
    if (name.length > 0) {
        document.getElementById("playerNameDisplay").textContent = name;
        document.getElementById("initialScreen").style.display = "none";
        document.getElementById("headerGameLabel").style.display = "none"; 
        document.getElementById("mainContainer").style.display = "flex";
        startLobbyListing();
    } else {
        alert("Please enter your name.");
    }
}

const ws = new WebSocket('ws://localhost:8765');

ws.onopen = () => {
    console.log('Connected to the WebSocket server');
    startLobbyListing();
};

function displayMessage(message) {
    const timestamp = new Date().toLocaleString();
    const formattedMessage = `[${timestamp}]\t${message}`;
    
    const messageElement = document.createElement('div');
    messageElement.textContent = formattedMessage;
    document.getElementById('lobbyMessages').appendChild(messageElement);
}


ws.onmessage = (event) => {
    console.log('Message from server ', event.data);
    const data = JSON.parse(event.data);

    if (data.lobbylist) {
        updateLobbiesList(data.lobbylist);
    }

    if (data.lobby_id) {
        currentLobby = data.lobby_id;
        document.getElementById('myLobbyId').textContent = currentLobby;
        updateLobbiesList(data.lobbylist || []);
    }
    
    if (data.message) {
        displayMessage(data.message);
    }

    if (data.game_started) {
        console.log("Sleeping 4 seconds and then go to game screen")
        setTimeout(function() {
            console.log('Finished sleeping for 4 seconds');
            const playerName = document.getElementById("playerName").value.trim();
            window.location = 'game.html?playerName='+ playerName;
        }, 4000);
    }
};

document.getElementById("createLobbyButton").onclick = function() {
    const playerName = document.getElementById("playerName").value.trim();
    ws.send(JSON.stringify({ action: 'create', player: playerName }));
};

function leaveLobby(lobbyId) {
    const playerName = document.getElementById("playerName").value.trim();
    ws.send(JSON.stringify({ action: 'leave', player: playerName, lobby_id: lobbyId }));
    currentLobby = null;
    document.getElementById('myLobbyId').textContent = 'no lobby';
}

function joinLobby(lobbyId) {
    const playerName = document.getElementById("playerName").value.trim();
    if ( currentLobby != null ) {
        ws.send(JSON.stringify({ action: 'leave', player: playerName, lobby_id: currentLobby }));
    }
    ws.send(JSON.stringify({ action: 'join', player: playerName, lobby_id: lobbyId }));
    currentLobby = lobbyId;
    document.getElementById('myLobbyId').textContent = lobbyId;
}

function startLobbyListing() {
    setInterval(() => {
        ws.send(JSON.stringify({ action: 'list', player: 'any' }));
    }, 1000);
}

$("#playerName").on("keydown",function search(e) { 
    if(e.keyCode == 13) {
        const name = document.getElementById("playerName").value.trim();
        if (name.length > 0) {
            document.getElementById("playerNameDisplay").textContent = name;
            document.getElementById("initialScreen").style.display = "none";
            document.getElementById("mainContainer").style.display = "flex";
            startLobbyListing();
        } else {
            alert("Please enter your name.");
        }
    }
});


function updateLobbiesList(lobbies) {
    const lobbiesListElement = document.getElementById('lobbiesList');
    if (lobbies.length == 0) {
        document.getElementById("emptyLobbiesList").style.display = "flex";
    } else {
        document.getElementById("emptyLobbiesList").style.display = "none";
    }

    lobbiesListElement.innerHTML = '';

    lobbies.forEach(lobbyId => {
        const lobbyItem = document.createElement('div');
        lobbyItem.textContent = lobbyId;
        lobbyItem.className = 'monospace';

        if (lobbyId === currentLobby) {
            lobbyItem.style.color = 'yellow';

            const leaveButton = document.createElement('button');
            leaveButton.textContent = 'Leave Lobby';
            leaveButton.className = 'btn btn-custom small-btn';
            leaveButton.onclick = () => leaveLobby(lobbyId);

            lobbyItem.appendChild(leaveButton);
        }
        else
        {
            const joinButton = document.createElement('button');
            joinButton.textContent = 'Join Lobby';
            joinButton.className = 'btn btn-custom small-btn';
            joinButton.onclick = () => joinLobby(lobbyId);
            lobbyItem.appendChild(joinButton);
        }

        lobbiesListElement.appendChild(lobbyItem);
    });
}
