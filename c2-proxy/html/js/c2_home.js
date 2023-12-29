// home window
// set the url values based on the browser ip/hostname & port value
var currentUrl = window.location.href;
var regex = /^(https?:\/\/)(.*)/;
var match = currentUrl.match(regex);
if (match && match[0]) {
  const url = match[1] + match[2];
  var redisSessionsUrl = `${url}/api/redis/sessions/all`
  var ipRegex = /^(https?:\/\/)(\d+\.\d+\.\d+\.\d+)/;
  var ipMatch = currentUrl.match(ipRegex);
  if (ipMatch && ipMatch[2]) {
    var wsPayloadUrl = 'ws://' + ipMatch[2] + ':9999/payload'
    var wsSessionUrl = 'ws://' + ipMatch[2] + ':9999/sessions'
  } else {
    var wsPayloadUrl = 'ws://' + match[2] + ':9999/payload'
    var wsSessionUrl = 'ws://' + match[2] + ':9999/sessions'
  }
}

document.addEventListener('DOMContentLoaded', function() {
// container element
const container = document.getElementById('container');

if (container) {
  // click event listener to the container element 
  container.addEventListener('click', function(event) {
    const clickedElement = event.target;

    // check if the clicked element is an image or part of an image container
    const isImage = clickedElement.tagName === 'IMG';
    const isImageContainer = clickedElement.classList.contains('computer') && clickedElement.classList.contains('online');

    if (isImage || isImageContainer) {
      // get the parent div's id when any image or its container within container is clicked
      const parentId = isImage ? clickedElement.parentNode.id : clickedElement.id;

      // redirect to a new page based on the div's id
      window.open(currentUrl + 'cli-' + parentId, '_blank');
    }
  });
} else {
  console.error('container element not found');
}

});


const wsSession = new WebSocket(wsSessionUrl);

wsSession.onopen = (event) => {
  console.log('Connected to WebSocket session server');

  fetch(redisSessionsUrl)
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(data => {
      let arrayOfObjects;

      if (data.length === 1) {
        const singleObject = JSON.parse(data[0]);
        arrayOfObjects = [singleObject]
        updateComputerStatus(arrayOfObjects);
      } else if (data.length > 1) {
        arrayOfObjects = data.map(jsonString => JSON.parse(jsonString));
        updateComputerStatus(arrayOfObjects);
      } else {
        const computerImg = document.querySelectorAll(".computer.online");
        if (computerImg.length == 0) {
          // if response is empty, create a scan_mode img 
          const imgTag = document.createElement('img');
          imgTag.src = '/img/scan_mode.gif';
          imgTag.id = 'scan_mode';
          imgTag.alt = '';
          imgTag.style.display = 'block';
          imgTag.style.margin = 'auto';
          const computerContainer = document.getElementById('computerContainer');
          computerContainer.appendChild(imgTag);
        }
      }
    })
    .catch(error => {
      console.error('There was a problem with the fetch operation:', error);
      // if response is empty, create a scan_mode img 
      const imgTag = document.createElement('img');
      imgTag.src = '/img/scan_mode.gif';
      imgTag.id = 'scan_mode';
      imgTag.alt = '';
      imgTag.style.display = 'block';
      imgTag.style.margin = 'auto';
      const computerContainer = document.getElementById('computerContainer');
      computerContainer.appendChild(imgTag);
    });
};

wsSession.onmessage = (event) => {
  let arrayOfObjects = [JSON.parse(event.data)];

  updateComputerStatus(arrayOfObjects);
};

wsSession.onclose = () => {
  console.log('Disconnected from WebSocket session server');
};

  // create or update computer status elements based on received data
  function updateComputerStatus(data) {
    // remove scan_mode img before adding computer elements 
    const scanModeImg = document.getElementById("scan_mode");
    if (scanModeImg) {
      // get the parent element
      const computerContainer = document.getElementById('computerContainer');
  
      // remove the img tag from its parent
      computerContainer.removeChild(scanModeImg);
    }

    const computerContainer = document.getElementById('computerContainer');

    data.forEach(clientData => {
      const { session_id, session_type, os_type, created_at, host_name, port, status, user_name, commands } = clientData;

      // check if session ID already exists
      let clientDiv = document.getElementById(session_id);

      if (!clientDiv) {
        // create a new div for the client if it doesn't exist
        clientDiv = document.createElement('div');
        clientDiv.id = session_id;
        clientDiv.className = 'computer online';
        computerContainer.appendChild(clientDiv);
      }

      let clientImage = clientDiv.querySelector('img');
      if (!clientImage) {
        // create the image for the client if it doesn't exist
        clientImage = document.createElement('img');
        clientImage.alt = 'Computer';
        clientDiv.appendChild(clientImage);
      }

      // set or update image source based on status
      // get the current URL
      const currentUrl = window.location.href;
      if (status === 'Connected') {
        clientImage.src = `${currentUrl}/img/online.png`;
      } else if (status === 'Disconnected') {
        clientImage.src = `${currentUrl}/img/offline.png`;
      } else {
        // Use a default image or handle other statuses if needed
        clientImage.src = `${currentUrl}/img/offline.png`;
      }

      let sessionIdSpan = clientDiv.querySelector('.session_id');
      if (!sessionIdSpan) {
        // create session ID span if it doesn't exist
        sessionIdSpan = document.createElement('span');
        sessionIdSpan.className = 'status-text session_id';
        clientDiv.appendChild(sessionIdSpan);
      }

      // update session ID and status
      sessionIdSpan.textContent = 'Session ID: ' + session_id || '';
    });
  }
