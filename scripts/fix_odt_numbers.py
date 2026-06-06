"""Fix wrong percentage in ODT: 38.2% -> 37.8%"""
import zipfile, shutil, os, re

odt_path = r"c:\akaza\General\Antigravit Projects\AI-Project\report_final_new (1).odt"
backup_path = odt_path + ".bak"
tmp_path = odt_path + ".tmp.odt"

# Backup original
shutil.copy2(odt_path, backup_path)
print(f"Backup saved to: {backup_path}")

with zipfile.ZipFile(odt_path, 'r') as zin:
    names = zin.namelist()
    with zipfile.ZipFile(tmp_path, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
        for name in names:
            data = zin.read(name)
            if name == 'content.xml':
                text = data.decode('utf-8')
                # Check for the wrong value
                count = text.count('38.2%')
                print(f"Found '38.2%' {count} time(s) in content.xml")
                text = text.replace('38.2%', '37.8%')
                data = text.encode('utf-8')
            zout.writestr(name, data)

# Replace original with fixed version
os.replace(tmp_path, odt_path)
print("ODT updated: 38.2% -> 37.8%")
