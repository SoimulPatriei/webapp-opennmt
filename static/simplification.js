function nmtSimplifyText() {
  const inputText = document.getElementById('inputText').value;
  const outputText = document.getElementById('outputText');
  const loadingSpinner = document.getElementById('loadingSpinner');

  if (!inputText.trim()) {
    alert("Please enter a sentence.");
    return;
  }

  // Show the loading spinner
  loadingSpinner.style.display = "block";
  outputText.innerHTML = ""; // Clear previous output

  // Send the request to the server
  fetch('http://mavs.hpc.ut.ee:5000/nmt_simplify', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ text: inputText })
  })
    .then(response => response.json())
    .then(data => {
      // Hide the spinner
      loadingSpinner.style.display = "none";

      if (data.error) {
        console.error('Error:', data.error);
        outputText.innerHTML = `Error occurred: ${data.error}`;
      } else {
        console.log('Success:', data);
        outputText.innerHTML = data.translation;
      }
    })
    .catch(error => {
      // Hide the spinner and display an error message
      loadingSpinner.style.display = "none";
      console.error('Error:', error);
      outputText.innerHTML = "Error occurred: " + error;
    });
}
