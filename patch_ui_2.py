with open('src/api/main.py', 'r') as f:
    content = f.read()

from patch_ui import new_html_func

idx1 = content.find("def get_dashboard_html() -> str:")
idx2 = content.find('if __name__ == "__main__":', idx1)

if idx1 != -1 and idx2 != -1:
    new_content = content[:idx1] + new_html_func + '\n\n' + content[idx2:]
    with open('src/api/main.py', 'w') as f:
        f.write(new_content)
    print("Patched successfully")
else:
    print(f"Failed to find indices: idx1={idx1}, idx2={idx2}")
