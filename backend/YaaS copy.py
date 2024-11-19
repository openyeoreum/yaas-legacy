import re
import json

def parse_poems(txt_file_path):
    poems = []
    current_poem = None
    content_lines = []
    with open(txt_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    idx = 0
    while idx < len(lines):
        line = lines[idx].strip()
        if line.startswith('<') and '번' in line and '>' in line:
            # Start of a new poem
            # Finish the previous poem if any
            if current_poem:
                current_poem["Content"] = '\n'.join(content_lines)
                poems.append(current_poem)
            # Extract Id and Name
            match = re.match(r'<(\d+)번\s+(.+?)>', line)
            if match:
                Id = int(match.group(1))
                Name = match.group(2)
                current_poem = {
                    "Id": Id,
                    "Tag": "",
                    "Name": Name,
                    "Age": "",  # Fill in if available
                    "Gender": "",  # Fill in if available
                    "Title": "",
                    "Content": ""
                }
                # Next line should be the title
                idx +=1
                if idx < len(lines):
                    title_line = lines[idx].strip()
                    current_poem["Title"] = title_line
                else:
                    current_poem["Title"] = ""
                # Initialize content lines
                content_lines = []
            else:
                # No match, ignore this line
                pass
        else:
            # Continue with content
            if current_poem:
                # Process line for content
                content_line = line.strip()
                if content_line != '':
                    if not content_line.endswith('.'):
                        content_line += '.'
                    content_lines.append(content_line)
                else:
                    # Empty line, add empty line to content
                    content_lines.append('')
            else:
                # Not inside a poem, skip
                pass
        # Increment idx
        idx += 1

    # After the loop, add the last poem if any
    if current_poem:
        # Assign content
        current_poem["Content"] = '\n'.join(content_lines)
        poems.append(current_poem)
    return poems

def main():
    txt_file_path = '/yaas/세종시시집.txt'
    poems = parse_poems(txt_file_path)

    # Optional: Fill in Age and Gender if available
    # Assuming we have a mapping of Name to Age and Gender
    name_info = {
        '국현': {'Age': '11', 'Gender': '남'},
        '김가은': {'Age': '11', 'Gender': '여'},
        # Add other names and their info here
    }
    for poem in poems:
        name = poem['Name']
        if name in name_info:
            poem['Age'] = name_info[name]['Age']
            poem['Gender'] = name_info[name]['Gender']
        else:
            poem['Age'] = ''
            poem['Gender'] = ''

    # Write to JSON file
    json_file_path = '/yaas/세종시시집.json'
    with open(json_file_path, 'w', encoding='utf-8') as f:
        json.dump(poems, f, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    main()