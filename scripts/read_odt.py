"""Extract plain text from ODT file to check numbers."""
import zipfile
import re
import sys

odt_path = r"c:\akaza\General\Antigravit Projects\AI-Project\report_final_new (1).odt"

with zipfile.ZipFile(odt_path, 'r') as z:
    with z.open('content.xml') as f:
        content = f.read().decode('utf-8')

# Remove XML tags but keep text
text = re.sub(r'<[^>]+>', ' ', content)
# Collapse whitespace
text = re.sub(r'\s+', ' ', text)

# Print full text
sys.stdout.buffer.write(text.encode('utf-8'))
sys.stdout.buffer.write(b'\n')
