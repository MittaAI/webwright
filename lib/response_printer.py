import re

from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit import print_formatted_text

if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.util import custom_style

class ResponsePrinter:
    def __init__(self):
        self.current_line = ""
        self.in_code_block = False

    def process_chunk(self, chunk):
        self.current_line += chunk
        if '\n' in self.current_line:
            lines = self.current_line.split('\n')
            for line in lines[:-1]:
                self.print_line(line)
            self.current_line = lines[-1]

    def process_final_chunk(self):
        if self.current_line:
            self.print_line(self.current_line)

    def print_line(self, line):
        formatted_text = []

        math_pattern = re.compile(r'\\\(.*?\\\)')
        inline_code_pattern = re.compile(r'(`.*?`|``.*?``)')
        tag_pattern = re.compile(r'<(\w+)>|</(\w+)>')

        # handle code block start and end
        if line.startswith('```'):
            if self.in_code_block:
                self.in_code_block = False
            else:
                self.in_code_block = True
            return
        
        # handle middle of code block
        if self.in_code_block:
            formatted_text.append(('class:code', ''.join(line)))
            print_formatted_text(FormattedText(formatted_text), style=custom_style)
            return
        
        # handle header
        if line.startswith('#'):
            formatted_text.append(('class:header', ''.join(line[2:])))
            print_formatted_text(FormattedText(formatted_text), style=custom_style)
            return

        # handle inline patterns
        current_class = ''
        parts = re.split(r'(\*\*.*?\*\*|`.*?`|``.*?``|\\\(.*?\\\))', line)
        for part in parts:
            if part.startswith('**') and part.endswith('**'):
                formatted_text.append((f'{current_class} class:bold', part[2:-2]))
            elif inline_code_pattern.match(part):
                # Handle both single and double ticks
                code_content = part[1:-1] if part.startswith('`') else part[2:-2]
                formatted_text.append((f'{current_class} class:inline-code', code_content))
            elif math_pattern.match(part):
                formatted_text.append((f'{current_class} class:math', part[2:-2]))
            else:
                formatted_text.append((current_class, part))
        print_formatted_text(FormattedText(formatted_text), style=custom_style)


if __name__ == "__main__":
    import random
    import time


    sample_response = """
Sure, here's a response combining all of those formatting elements in Markdown:

**This is a block of bold text within a line.**
# Header Level 1
Here's an `inline code block`.
```
# This is a
# multi-line code block
print("Hello, World!")
```
    """

    sample_response_tags = """
<thinking>
To generate a response with some HTML tags for testing purposes, I will use:
- Paragraph tags <p> 
- Heading tags <h1> to <h3>
- A table <table> with table rows <tr> and cells <td> 
- A div <div> with a class attribute
- An ordered list <ol> with list items <li>
- Emphasis <em> and bold <strong> tags
- A horizontal rule <hr> 
</thinking>

<h1>Sample HTML Page</h1>

<p>This is an example <em>HTML response</em> generated for <strong>testing purposes</strong>.</p>

<h2>A Simple Table</h2>
<table>
  <tr>
    <td>Row 1, Cell 1</td>
    <td>Row 1, Cell 2</td>
  </tr>
  <tr>
    <td>Row 2, Cell 1</td>
    <td>Row 2, Cell 2</td>
  </tr>
</table>

<div class="example-class">
  <h3>An Ordered List</h3>
  <ol>
    <li>First item</li>
    <li>Second item</li>
    <li>Third item</li>
  </ol>
</div>

<hr>

<p>Feel free to let me know if you would like me to include any other specific HTML elements or attributes in the example!</p>
    """

    def split_into_random_chunks(text, min_chunk_size=5, max_chunk_size=15):
        """
        Splits the input text into chunks of random sizes.

        Args:
            text (str): The text to split into chunks.
            min_chunk_size (int): Minimum size of each chunk.
            max_chunk_size (int): Maximum size of each chunk.

        Returns:
            List[str]: A list of text chunks.
        """
        chunks = []
        index = 0
        text_length = len(text)
        while index < text_length:
            # Determine the size of the next chunk
            chunk_size = random.randint(min_chunk_size, max_chunk_size)
            # Extract the chunk from the text
            chunk = text[index:index + chunk_size]
            chunks.append(chunk)
            index += chunk_size
        return chunks


    rp = ResponsePrinter()
    chunks = split_into_random_chunks(sample_response, min_chunk_size=5, max_chunk_size=20)
    
    # Feed each chunk into the process_chunk method with a slight delay to simulate streaming
    for chunk in chunks:
        rp.process_chunk(chunk)
        #print(chunk, end='')
        time.sleep(0.2)

