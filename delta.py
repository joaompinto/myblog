import json

def quill_delta_to_html(delta):
    """
    Convert QuillJS delta operations to HTML.

    :param delta: List of delta operations (parsed JSON)
    :return: HTML string
    """
    html = ""
    line_html = ""
    delta = json.loads(delta)
    print("DELTA=", delta)
    save_attributes = {}

    for op in delta.get('ops', []):
        insert_op = op['insert']
        if isinstance(insert_op, str):
            if insert_op.endswith("\n"):
                line_html += insert_op
                attributes = op.get('attributes', {})
                # Replace newlines with HTML line breaks
                line_html = line_html.replace("\n", "<br>")
                line_html = apply_attributes(line_html, attributes)
                html += line_html
                line_html = ""
            else:
                attributes = op.get('attributes', {})
                line_html += apply_attributes(insert_op, attributes)
        elif isinstance(insert_op, dict) and 'customImage' in insert_op:
            attributes = op.get('attributes', {})
            html += apply_image_attributes(insert_op["customImage"], attributes)


    print("HTML=", html)
    return html

def apply_image_attributes(image, attributes):
    attributes_str = ""
    if 'width' in attributes:
        attributes_str += f' width="{attributes["width"]}"'
    if 'height' in attributes:
        attributes_str += f' height="{attributes["height"]}"'
    align = image.get("align")
    if align == "center":
        attributes_str += 'style="display: block; margin: 0 auto;"'
    elif align == "left":
        attributes_str += 'style="display: block; margin: 0 0 0 0;"'
    image = image['src']
    return f'<img src="{image}"{attributes_str} />'

def apply_attributes(text, attributes):
    """
    Apply attributes to a given text.

    :param text: Text to apply attributes to
    :param attributes: Dictionary of attributes
    :return: HTML string with attributes applied
    """
    if not attributes:
        return text

    html = text

    if attributes.get('bold'):
        html = f'<strong>{html}</strong>'
    if attributes.get('italic'):
        html = f'<em>{html}</em>'
    if attributes.get('underline'):
        html = f'<u>{html}</u>'
    if attributes.get('strike'):
        html = f'<s>{html}</s>'
    if 'link' in attributes:
        html = f'<a href="{attributes["link"]}">{html}</a>'
    if 'header' in attributes:
        level = attributes['header']
        if level == 1:
            html = f'<h1 class="text-4xl">{html}</h1>'
        if level == 2:
            html = f'<h1 class="text-2xl">{html}</h1>'

    if 'align' in attributes:
        align = attributes['align']
        html = f'<div style="text-align: {align};">{html}</div>'

    return html


def delta_title(delta):
    """
    Extract the title from the first line of the delta

    :param delta: List of delta operations (parsed JSON)
    :return: Title string
    """
    delta = json.loads(delta)
    for op in delta.get('ops', []):
        if 'insert' in op:
            return op['insert']

# Example usage
if __name__ == "__main__":
    delta_text = '''
    {
      "ops": [
        {"insert": "Hello, "},
        {"insert": "world!", "attributes": {"bold": true}},
        {"insert": "\\n"},
        {"insert": "This is an ", "attributes": {"italic": true}},
        {"insert": "example.", "attributes": {"underline": true}},
        {"insert": "\\n"},
        {"insert": "Check this ", "attributes": {"strike": true}},
        {"insert": "link", "attributes": {"link": "https://example.com"}},
        {"insert": "\\n"}
      ]
    }
    '''
    delta = json.loads(delta_text)
    html_output = quill_delta_to_html(delta)

