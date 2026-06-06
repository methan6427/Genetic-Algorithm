"""Extract all images from ODT file."""
import zipfile, os

odt_path = r"c:\akaza\General\Antigravit Projects\AI-Project\report_final_new (1).odt"
out_dir = r"c:\akaza\General\Antigravit Projects\AI-Project\scripts\odt_images"
os.makedirs(out_dir, exist_ok=True)

with zipfile.ZipFile(odt_path, 'r') as z:
    names = z.namelist()
    pics = [n for n in names if n.lower().startswith('pictures/') or n.lower().endswith('.png') or n.lower().endswith('.jpg')]
    print("All picture entries:", pics)
    for p in pics:
        fname = os.path.basename(p)
        with z.open(p) as f:
            data = f.read()
        out_path = os.path.join(out_dir, fname)
        with open(out_path, 'wb') as f:
            f.write(data)
        print(f"Extracted: {fname} ({len(data)} bytes)")
