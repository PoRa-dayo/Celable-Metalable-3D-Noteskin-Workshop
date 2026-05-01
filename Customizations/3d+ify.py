import re

# Patterns
header_pattern = re.compile(r'^"(.*?)"\s+\d+\s+\d+$')
triple_pattern = re.compile(r'^-?\d*\.?\d+\s+-?\d*\.?\d+\s+-?\d*\.?\d+$') # 3 floats/integers
seven_pattern = re.compile(r'^(-?\d*\.?\d+\s+){6}-?\d*\.?\d+$') # 7 floats
triangle_pattern = re.compile(r'^(\d+\s+){7}\d+$')  # 8 integers
materials_pattern = re.compile(r'^Materials:\s*\d+$')

def invert_number_str(num_str):
    # Invert a numeric string by flipping the sign manually, keeping formatting.
    num_str = num_str.strip()
    if num_str.startswith('-'):
        return num_str[1:]
    elif num_str == '0' or num_str == '0.0':
        return num_str
    else:
        return '-' + num_str

path = input("\033[91mNOTE: 3D+ (two-sided) NOTESKINS CAN CAUSE UNEXPECTED BEHAVIORS ON NotITG MODCHARTS OR ITS PORTS!!!\n\033[92m>>> Behold, the 3D+-ify-inator!\n>>> This script will replace an arrow/lift Milkshape ASCII.txt file from a 3D (one-sided) noteskin with a 3D+ (two-sided) version of it.\nEnter path to the arrow/lift Milkshape ASCII .txt file: \033[0m ").strip('"')

with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

output = []
i = 0

while i < len(lines):
    line = lines[i].rstrip('\n')

    # Handle "Meshes: <number>"
    meshes_match = re.match(r'^(Meshes:\s*)(\d+)$', line)
    if meshes_match:
        prefix, num = meshes_match.groups()
        doubled = str(int(num) * 2)
        output.append(f"{prefix}{doubled}\n")
        i += 1
        continue

    header_match = header_pattern.match(line)

    if header_match:
        block = [lines[i]]
        i += 1

        # Collect until next header OR Materials line
        while i < len(lines):
            stripped = lines[i].rstrip('\n')
            if header_pattern.match(stripped) or materials_pattern.match(stripped):
                break
            block.append(lines[i])
            i += 1

        # Add original block, but remove its trailing blank line so it touches the duplicate
        if block and block[-1].strip() == "":
            block = block[:-1]
        output.extend(block)

        # If the next line is "Materials:", ensure one blank line before it later
        add_blank_before_materials = (
            i < len(lines) and materials_pattern.match(lines[i].rstrip('\n'))
        )

        # Check if we stopped because of a "Materials:" line
        insert_before_materials = (
            i < len(lines) and materials_pattern.match(lines[i].rstrip('\n'))
        )

        # --- Duplicate + modify block ---
        modified_block = []

        ind = 0
        while ind < len(block):
            b_line = block[ind].rstrip('\n')

            # Modify header line
            m = header_pattern.match(b_line)
            if m:
                name = m.group(1)
                new_name = name + "Back"
                if len(new_name) > 30:
                    new_name = new_name[-30:]
                modified_line = f'"{new_name}"' + b_line[b_line.find('"', 1) + 1:]
                modified_block.append(modified_line)
                ind += 1
                continue

            # Triple float lines = NORMALS
            # Alt+N -> Flip
            if triple_pattern.match(b_line) and '.' in b_line:
                print(b_line, "Normals")
                nums = b_line.split()

                for j in (0, 1, 2):  # nx, ny, nz
                    nums[j] = invert_number_str(nums[j])

                modified_block.append(' '.join(nums))
                print(' '.join(nums))
                ind += 1
                continue

            # 7-number float lines = VERTICES
            # Scale -1 on MilkShape Z
            if seven_pattern.match(b_line) and '.' in b_line:
                print(b_line, "Vertices")
                nums = b_line.split()

                nums[3] = invert_number_str(nums[3])  # Z = -Z

                modified_block.append(' '.join(nums))
                print(' '.join(nums))
                ind += 1
                continue

            # Triangle indices (flip face winding)
            if triangle_pattern.match(b_line):
                print(b_line, "Triangles")
                nums = b_line.split()

                # swap v1 and v2 → reverse winding
                nums[1], nums[2] = nums[2], nums[1]

                modified_block.append(' '.join(nums))
                print(' '.join(nums))
                ind += 1
                continue


            # Otherwise leave as is
            modified_block.append(b_line)
            ind += 1


        # Place duplicate, ensure no extra blank line before Materials
        if modified_block and modified_block[-1] == '':
            modified_block.pop()

        output.extend([line + '\n' for line in modified_block])
        if add_blank_before_materials:
            output.append('\n')



        # Don’t skip Materials line; process it next
    else:
        output.append(lines[i])
        i += 1

# Overwrite file
with open(path, 'w', encoding='utf-8') as f:
    f.writelines(output)

print("Replaced the ASCII .txt file with the newly generated 3D+ version.")
input("\nPress Enter to exit.")
