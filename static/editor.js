// Import ImageBlot from Quill
const ImageBlot = Quill.import('formats/image');

class CustomImageBlot extends ImageBlot {
  static create(value) {
    console.log("Creating from", value)
    let node = super.create(value);
    node.setAttribute('src', value.src);
    node.setAttribute('alt', 'image');
    if(value.align) {
        node.setAttribute('align', value.align);        // Center the image
        node.style.display = 'block';
        node.style.marginLeft = 'auto';
        node.style.marginRight = 'auto';
    }
    return node;
  }

  static formats(node) {
    let formats = super.formats(node);
    if (node.hasAttribute('data-width')) {
      formats.width = node.getAttribute('data-width');
    }
    if (node.hasAttribute('data-align')) {
      formats.align = node.getAttribute('data-align');
    }
    return formats;
  }

  format(name, value) {
    console.log("Formatting single", name, value);
    if (name === 'width') {
      if (value) {
        this.domNode.setAttribute('data-width', value);
        this.domNode.style.width = value;
      } else {
        this.domNode.removeAttribute('data-width');
        this.domNode.style.width = '';
      }
    } else if (name === 'align') {
      if (value) {
        this.domNode.setAttribute('align', value);
        this.domNode.style.display = 'block';
        this.domNode.style.marginLeft = value === 'center' ? 'auto' : '';
        this.domNode.style.marginRight = value === 'center' ? 'auto' : '';
      } else {
        this.domNode.removeAttribute('align');
        this.domNode.style.display = '';
        this.domNode.style.marginLeft = '';
        this.domNode.style.marginRight = '';
      }
    } else {
      super.format(name, value);
    }
  }

  static value(node) {
    console.log("Getting the value of", node)
    return {
        'src' : node.src,
        'width': node.width,
        'align': node.align
    }
  }
}

// Set the blot name and tag name
CustomImageBlot.blotName = 'customImage';
CustomImageBlot.tagName = 'img';

// Register the custom blot with Quill
Quill.register(CustomImageBlot);

var quill = new Quill('#editor-container', {
    theme: 'snow',
    modules: {
        toolbar: '#toolbar-container',
        imageClick: true // Enable the custom module
    }
});

quill.getModule('toolbar').addHandler('image', () => {
    console.log("my own handler");
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
                quill.insertText(range.index, '\n');
                quill.insertEmbed(range.index+1, 'customImage', {'src': e.target.result});
                // Insert a new line after the image
                // Move the cursor to the end of the new line
                quill.setSelection(range.index + 2);
            };
            reader.readAsDataURL(file);
        }
    };
});


quill.on('text-change', () => {
    // Enable the save button when the editor content changes
    document.getElementById('save-button').disabled = false;
});

// Load the editor content from the hidden div
document.addEventListener('DOMContentLoaded', function() {

    // Get the content from content_id if the element exists
    var currentUrl = window.location.href;
    var { authorId, contentId } = extractIdsFromUrl(currentUrl);

    // Do an AJAX request to get the editor content from the database
    var xhr = new XMLHttpRequest();
    xhr.open('GET', `/load/${authorId}/${contentId}`, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onload = function () {
        if (xhr.status >= 200 && xhr.status < 300) {
            quill.setContents(JSON.parse(xhr.responseText).content);
        }
    };
    xhr.send();
});

function extractIdsFromUrl(url) {
  var regex = /\/(\d+)(?:\/(\d+))?$/;
  var match = url.match(regex);
  if (match) {
      return {
          authorId: match[1],
          contentId: match[2] || null
      };
  } else {
      return null;
  }
}

document.getElementById('save-button').addEventListener('click', () => {
    // Disable the save button upon click
    document.getElementById('save-button').disabled = true;

    // Get the editor content as HTML
    var content = quill.getContents();

    // Create a new XMLHttpRequest object
    var xhr = new XMLHttpRequest();

    var currentUrl = window.location.href;
    var { authorId, contentId } = extractIdsFromUrl(currentUrl);

    var postUrl = contentId ? `/save/${authorId}/${contentId}` : `/save/${authorId}`; // Use the captured number for the save URL

    // Define the request parameters
    xhr.open('POST', postUrl, true);
    xhr.setRequestHeader('Content-Type', 'application/json');

    // Clear any previous error messages
    var errorMessage = document.getElementById('error-message');
    errorMessage.innerText = '';
    errorMessage.style.display = 'none';

    console.log(content);

    // Define the callback function to handle the response
    xhr.onload = function () {
        if (xhr.status >= 200 && xhr.status < 300) {
            // Enable the save button after successful save
            document.getElementById('save-button').disabled = false;

            // Show last save info
            var lastSaveInfo = document.getElementById('last-save-info');
            lastSaveInfo.innerText = "Last save at " + new Date().toLocaleTimeString();
            lastSaveInfo.style.display = 'block';

            // Change the current URL to end with 'edit/id'
            var response = JSON.parse(xhr.responseText);

            var newUrl = `/edit/${response.author_id}/${response.content_id}`;
            window.history.pushState({ path: newUrl }, '', newUrl);
            console.log(response);

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
