import os

def fix_mojibake(directory):
    for root, dirs, files in os.walk(directory):
        if any(ignored in root for ignored in ['node_modules', '.venv', '.git', 'coverage']):
            continue
        for file in files:
            if not file.endswith(('.tsx', '.ts', '.css', '.html', '.md', '.example', '.local', '.json', '.yml')):
                continue
            path = os.path.join(root, file)
            with open(path, 'rb') as f:
                content_bytes = f.read()
                
            try:
                content = content_bytes.decode('utf-8')
            except UnicodeDecodeError:
                continue
                
            # Check for common mojibake characters like Ã, â, ð
            if any(bad_char in content for bad_char in ["Ã", "â", "ð", "Â"]):
                # Try to reverse it by encoding as windows-1252 and decoding as utf-8
                try:
                    fixed_content = content.encode('windows-1252').decode('utf-8')
                    if fixed_content != content:
                        with open(path, 'wb') as f:
                            f.write(fixed_content.encode('utf-8'))
                        print(f"Fixed: {path}")
                except Exception as e:
                    print(f"Could not automatically fix {path}: {e}")
                    
fix_mojibake('.')
