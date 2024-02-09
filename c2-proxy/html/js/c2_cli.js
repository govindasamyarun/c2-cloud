// CLI window 
const cliWindow = document.getElementById('cli-window');
const userInput = document.getElementById('user-input');

// set the url values based on the browser ip/hostname & port value 
var currentUrl = window.location.href;
var regex = /^(https?:\/\/)([^/]+)\/cli\-(.*)/;
var match = currentUrl.match(regex);
if (match && match[0]) {
  var url_session_id = match[3]
  const url = match[1] + match[2];
  var execUrl = `${url}/api/exec/${url_session_id}/`
  var redisC2Url = `${url}/api/redis/c2/${url_session_id}`
  var redisSessionsUrl = `${url}/api/redis/sessions/${url_session_id}`
  var ipRegex = /^(https?:\/\/)(\d+\.\d+\.\d+\.\d+)/;
  var ipMatch = currentUrl.match(ipRegex);
  // hostname with port number 
  var hostPortRegex = /([^:]+)\:/;
  var hostPortMatch = match[2].match(hostPortRegex);
  if (ipMatch && ipMatch[2]) {
    var wsPayloadUrl = 'ws://' + ipMatch[2] + ':9999/payload'
    var wsSessionUrl = 'ws://' + ipMatch[2] + ':9999/sessions'
  } else if (hostPortMatch && hostPortMatch[1]) {
    var wsPayloadUrl = 'ws://' + hostPortMatch[1] + ':9999/payload'
    var wsSessionUrl = 'ws://' + hostPortMatch[1] + ':9999/sessions'
  } else {
    var wsPayloadUrl = 'ws://' + match[2] + ':9999/payload'
    var wsSessionUrl = 'ws://' + match[2] + ':9999/sessions'
  }
}

// function to handle user input
function handleInput(e) {
  if (e.key === 'Enter') {
    const command = userInput.value.trim();
    const apiUrl = execUrl + btoa(command);
    const result = fetchData(apiUrl); // process command 
    userInput.value = ''; // clear input field
    e.preventDefault();
  }
}

// keystrokes 
document.addEventListener('DOMContentLoaded', function() {
  const userInput = document.getElementById('user-input');
  if (userInput) {
    userInput.addEventListener('keydown', handleInput);
  } else {
    console.error("User input element not found.");
  }
});

function fetchData(url) {
  fetch(url)
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response;
    })
    .catch(error => {
      console.error('There was a problem with the fetch operation:', error);
    });
}

// function to process the entered command 
function processCommand(data) {
  data.forEach(clientData => {
    const { session_id, shell, command, command_date, response, response_date } = clientData;
    if (url_session_id == session_id) {
      // display user command
      const userCommand_div = document.createElement('div');
      userCommand_div.textContent = shell + ' ' + atob(command);
      // display command executed date
      const commandExecuted_div = document.createElement('div');
      commandExecuted_div.textContent = 'Command executed @ ' + command_date;
      // display reseponse received date
      const responseReceived_div = document.createElement('div');
      responseReceived_div.textContent = 'Response received @ ' + response_date + '\n';

      // display response 
      const response_div = document.createElement('div');

      const lines = atob(response).split('\r\n');
      response_div.textContent = 'Response: ';
      lines.forEach(line => {
          const linePre = document.createElement('pre');
          linePre.textContent = line;
          linePre.style.color = 'lime';
          linePre.style.fontSize = 'inherit';
          linePre.style.lineHeight = '0.8';
          linePre.style.whiteSpace = 'pre-wrap';
          commandExecuted_div.appendChild(linePre);
          responseReceived_div.appendChild(linePre);
          response_div.appendChild(linePre);
      });
      // css 'response' class for green color
      commandExecuted_div.classList.add('response');
      responseReceived_div.classList.add('response');
      response_div.classList.add('response');

      // append the command and response before the input line
      // add response above input line
      cliWindow.insertBefore(userCommand_div, userInput.parentElement);
      cliWindow.insertBefore(commandExecuted_div, userInput.parentElement);
      cliWindow.insertBefore(responseReceived_div, userInput.parentElement); 
      cliWindow.insertBefore(response_div, userInput.parentElement);

      // always scroll to the bottom of the CLI window
      cliWindow.scrollTop = cliWindow.scrollHeight;

      // clear input field
      userInput.value = '';
    }
});
}

// payload websocket 
const wsPayload = new WebSocket(wsPayloadUrl);

wsPayload.onopen = (event) => {
  // retrieve payload data 
  console.log('Connected to WebSocket payload server');

  fetch(redisC2Url)
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(data => {
      let arrayOfObjects;

      if (data.length === 0) {
        return
      } else if (data.length === 1) {
        const singleObject = JSON.parse(data[0]);
        arrayOfObjects = [singleObject]
      } else {
        // parse each string element in the array into an object
        arrayOfObjects = data.map(jsonString => JSON.parse(jsonString));
      }
      processCommand(arrayOfObjects);
    })
    .catch(error => {
      console.error('There was a problem with the fetch operation:', error);
    });
};

wsPayload.onmessage = (event) => {
  // payload data from redis pubsub 
  let data = [JSON.parse(event.data)];
  processCommand(data);
  };
  
wsPayload.onclose = () => {
  console.log('Disconnected from WebSocket payload server');
};


// websocket sessions 
const wsSession = new WebSocket(wsSessionUrl);

wsSession.onopen = (event) => {
  console.log('Connected to WebSocket sessions server');

  fetch(redisSessionsUrl)
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(data => {
      let arrayOfObjects;
      if (data.length === 0) {
        return
      } else if (data.length === 1) {
        const singleObject = JSON.parse(data[0]);
        arrayOfObjects = [singleObject]
      } else {
        arrayOfObjects = data.map(jsonString => JSON.parse(jsonString));
      }

      // set the new value for the CLI symbol
      const session_id = arrayOfObjects[0]["session_id"];
      if (url_session_id == session_id) {
        const cliSymbol = document.querySelector('.cli-symbol');
        if (cliSymbol) {
          cliSymbol.textContent = arrayOfObjects[0]["shell"]; 
        }
        // set session ID, client IP & port 
        const shellNameSpan = document.getElementById('shell-name');
        const hostNameSpan = document.getElementById('host-name');
        const osNameSpan = document.getElementById('os-type');
        shellNameSpan.textContent = url_session_id;
        hostNameSpan.textContent = arrayOfObjects[0]["host_name"];
        osNameSpan.textContent = arrayOfObjects[0]["os_type"];
        if (arrayOfObjects[0]["status"] == "Disconnected") {
          const cliWindow = document.getElementById('cli-window');
          const userInput = document.getElementById('user-input');
          if (cliWindow) {
            cliWindow.style.border = '6px solid red';
          }

          userInput.placeholder = '';

          userInput.disabled = true;
        }

    }
    })
    .catch(error => {
      console.error('There was a problem with the fetch operation:', error);
    });

};

wsSession.onmessage = (event) => {
    const parsedData = JSON.parse(event.data);
    const session_id = parsedData["session_id"];
    // to handle the broadcast message 
    if ((parsedData["status"] == "Disconnected") && (url_session_id == session_id)) {
      const cliWindow = document.getElementById('cli-window');
      const userInput = document.getElementById('user-input');
      if (cliWindow) {
        cliWindow.style.border = '6px solid red';
      }
      
      userInput.placeholder = '';
      
      userInput.disabled = true;
    }
  };
  
  wsSession.onclose = () => {
    console.log('Disconnected from WebSocket sessions server');
  };
