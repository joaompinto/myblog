class ImageClickModule {
    constructor(quill, options) {
        this.quill = quill;
        this.options = options;
        this.toolbar = null; // Store reference to the current toolbar
        this.image = null; // Store reference to the current image

        // Listen for click events on images in the editor
        this.quill.root.addEventListener('click', this.handleClick.bind(this));
    }

    handleClick(event) {
        if (event.target.tagName === 'IMG') {
        this.image = event.target;

        // Remove the previous toolbar if it exists
        if (this.toolbar) {
            this.toolbar.remove();
        }

        // Create a new toolbar element
        this.createToolbar(event.pageY, event.pageX);
        }
    }

    createToolbar(top, left) {
        const toolbar = document.createElement('div');
        toolbar.innerHTML = `
        <button data-size="small">Small</button>
        <button data-size="medium">Medium</button>
        <button data-size="large">Large</button>
        `;
        toolbar.style.position = 'absolute';
        toolbar.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
        toolbar.style.color = '#fff';
        toolbar.style.padding = '5px';
        toolbar.style.borderRadius = '3px';
        toolbar.style.top = top + 'px';
        toolbar.style.left = left + 'px';

        // Add click event listener to toolbar buttons
        toolbar.querySelectorAll('button').forEach(button => {
        button.addEventListener('click', () => {
            // Remove the toolbar after resizing
            if (this.toolbar) {
                this.toolbar.remove();
                this.toolbar = null; // Reset the reference
            }
            const size = button.getAttribute('data-size');
            this.resizeImage(size);
        });
        });

        // Append the toolbar to the document body
        document.body.appendChild(toolbar);

        // Store the reference to the current toolbar
        this.toolbar = toolbar;

        // Remove the toolbar after a certain time or on click
        setTimeout(() => {
        if (this.toolbar) {
            this.toolbar.remove();
            this.toolbar = null; // Reset the reference
        }
        }, 5000);
    }

    resizeImage(size) {
        if (!this.image) return;

        let width;
        switch (size) {
        case 'small':
            width = '100px';
            break;
        case 'medium':
            width = '300px';
            break;
        case 'large':
            width = '500px';
            break;
        default:
            return;
        }

        // Update the image style
        this.image.style.width = width;
        this.image.style.height = 'auto';

        // Update the image attributes in the Quill delta
        const range = this.quill.getSelection(true);
        if (range) {
        const [leaf, offset] = this.quill.getLeaf(range.index);
        if (leaf && leaf.domNode === this.image) {
            const blot = Quill.find(this.image);
            blot.format('width', width);
        }
        }
    }
}

 // Register the custom module with Quill
Quill.register('modules/imageClick', ImageClickModule);