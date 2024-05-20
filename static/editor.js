
var quill = new Quill('#editor-container', {
    theme: 'snow',
    modules: {
        toolbar: '#toolbar-container',
        imageResize: {
            displaySize: true // Set to true to display image size in pixels
        }
    }
});

quill.getModule('toolbar').addHandler('image', () => {
    const input = document.createElement('input');
    input.setAttribute('type', 'file');
    input.setAttribute('accept', 'image/*');
    input.click();

    input.onchange = () => {
        const file = input.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                const range = quill.getSelection();
                quill.insertEmbed(range.index, 'image', e.target.result);
            };
            reader.readAsDataURL(file);
        }
    };
});

quill.on('selection-change', range => {
    const scaleButton = document.getElementById('scale-image-button');
    if (range && range.length === 1) {
        const [leaf] = quill.getLeaf(range.index);
        if (leaf && leaf.domNode.tagName === 'IMG') {
            scaleButton.disabled = false;
        } else {
            scaleButton.disabled = true;
        }
    } else {
        scaleButton.disabled = true;
    }
});

quill.on('text-change', () => {
    // Enable the save button when the editor content changes
    document.getElementById('save-button').disabled = false;
});

document.getElementById('scale-image-button').addEventListener('click', () => {
    const range = quill.getSelection();
    if (range && range.length === 1) {
        const [leaf] = quill.getLeaf(range.index);
        if (leaf && leaf.domNode.tagName === 'IMG') {
            const img = leaf.domNode;
            img.style.width = '50%';
            img.style.height = 'auto';
        }
    }
});

// Load the editor content from the hidden div
document.addEventListener('DOMContentLoaded', function() {

    // Get the content from the hidden div
    var contentId = document.getElementById('content-id').textContent;

    // Do an AJAX request to get the editor content from the database
    var xhr = new XMLHttpRequest();
    xhr.open('GET', `/load/${contentId}`, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onload = function () {
        if (xhr.status >= 200 && xhr.status < 300) {
            quill.setContents(JSON.parse(xhr.responseText).content);
        }
    };
    xhr.send();
});

document.getElementById('save-button').addEventListener('click', () => {
    // Disable the save button upon click
    document.getElementById('save-button').disabled = true;

    // Get the editor content as HTML
    var content = quill.getContents();

    // Create a new XMLHttpRequest object
    var xhr = new XMLHttpRequest();

    // Check if the current URL ends with '/X' where X is a number
    var currentUrl = window.location.href;
    var idMatch = currentUrl.match(/\/(\d+)$/); // Updated regex to match '/X' at the end of URL
    var postUrl = idMatch ? `/save/${idMatch[1]}` : '/save'; // Use the captured number for the save URL
    console.log(postUrl);

    // Define the request parameters
    xhr.open('POST', postUrl, true);
    xhr.setRequestHeader('Content-Type', 'application/json');

    // Clear any previous error messages
    var errorMessage = document.getElementById('error-message');
    errorMessage.innerText = '';
    errorMessage.style.display = 'none';

    // Define the callback function to handle the response
    xhr.onload = function () {
        if (xhr.status >= 200 && xhr.status < 300) {
            // Enable the save button after successful save
            document.getElementById('save-button').disabled = false;
            console.log(xhr.responseText);

            // Show last save info
            var lastSaveInfo = document.getElementById('last-save-info');
            lastSaveInfo.innerText = "Last save at " + new Date().toLocaleTimeString();
            lastSaveInfo.style.display = 'block';

            // Change the current URL to end with 'edit/id'
            var response = JSON.parse(xhr.responseText);
            if (response.id) {
                var newUrl = window.location.origin + window.location.pathname.replace(/\/(\d+)$/, '') + '/' + response.id;
                window.history.pushState({ path: newUrl }, '', newUrl);
            }
            // Change the content id in the hidden div
            document.getElementById('content-id').textContent = response.id;
            document.getElementById('content-render').innerHTML = response.content;

        } else {
            // Enable the save button after encountering an error
            document.getElementById('save-button').disabled = false;
            console.error('Request failed:', xhr.statusText);
            // Show error message in red box
            errorMessage.innerText = 'Failed to save content: ' + xhr.statusText;
            errorMessage.style.display = 'block';

            // If the response contains additional error details, display them
            if (response.detail) {
                errorMessage.innerText += ' - ' + JSON.stringify(response.detail);
            }
        }
    };

    // Define the callback function to handle network errors
    xhr.onerror = function () {
        // Enable the save button after encountering an error
        document.getElementById('save-button').disabled = false;
        console.error('Request failed:', xhr.statusText);
        // Show error message in red box
        errorMessage.innerText = 'Network error occurred';
        errorMessage.style.display = 'block';
    };

    // Send the request with the editor content in the body
    xhr.send(JSON.stringify({ content: content }));
});

document.getElementById('delete-button').addEventListener('click', function(event) {
    var confirmDeletion = confirm('Are you sure you want to delete this content?');
    if (!confirmDeletion) {
        event.preventDefault(); // Prevent the delete action if the user cancels
    }
});
