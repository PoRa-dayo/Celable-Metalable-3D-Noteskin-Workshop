import tkinter as tk
from tkinter import ttk,messagebox,filedialog
from PIL import Image, ImageTk, ImageSequence
import os, re, shutil, queue, threading, json, copy, sys, tempfile, random
from pathlib import Path
from itertools import combinations

# Each list represents a folder structure to look for
# e.g. ["NoteSkins", "dance"] is NoteSkins/dance
TARGET_PATHS = [
    ["NoteSkins", "dance"]
]
FOLDER_OPTIONS = {
    "Stepmania 5/ITGmania/Etterna/OutFox": ["Stepmania 5", "ITGmania", "Etterna", "OutFox"],
    "NotITG/OpenITG": ["NotITG", "OpenITG"]
}

# Root path is the path containing Customizations, Previews, etc.
# This path is the path containing this .py
if getattr(sys, "frozen", False):
    # Running as a packaged executable
    root_path = Path(sys.executable).resolve().parent.parent
    this_path = Path(sys.executable).resolve().parent
else:
    # Running as a Python script inside Program/
    root_path = Path(__file__).resolve().parent.parent
    this_path = Path(__file__).resolve().parent

# Make sure the working directory is the root path
os.chdir(root_path)
SAVED_SELECTIONS_FILE = this_path / "saved_selections.json"
customization_dropdowns_created = False
cur_path = ""

def show_page(page):
    page1.pack_forget()
    page2.pack_forget()
    page3.pack_forget()
    page.pack(fill="both", expand=True)


# ---------------------PAGE 1: SELECT YOUR PATH-------------------------------
# Check the input folder and its parents and subfolders for paths that match TARGET_PATHS
# Then return the matching folder, and the parent folder which contains the Songs folder
def find_folder(path, max_folders=10000):
    path = os.path.abspath(os.path.expanduser(path))

    if not os.path.isdir(path):
        return None

    checked = 0

    # Search the input directory and its parents
    search_roots = []
    current = path

    while True:
        search_roots.append(current)
        parent = os.path.dirname(current)

        if parent == current:
            break

        current = parent

    # Search subfolders of each root
    for root in search_roots:
        for current_dir, dirs, files in os.walk(root):
            checked += 1

            if checked > max_folders:
                print("Search limit reached.")
                return None
            
            for target_path in TARGET_PATHS:
                current = current_dir
                matched = True

                # Follow the required nested folder structure
                for folder in target_path:
                    folder_match = None

                    for d in dirs:
                        if d.lower() == folder.lower():
                            folder_match = d
                            break

                    if folder_match is None:
                        matched = False
                        break

                    current = os.path.join(current, folder_match)

                    dirs = os.listdir(current)

                if matched:
                    matching_folder = current

                    # Find the parent directory containing "Songs"
                    parent = current_dir

                    while True:
                        if os.path.isdir(os.path.join(parent, "Songs")):
                            return parent, matching_folder

                        grandparent = os.path.dirname(parent)

                        if grandparent == parent:
                            break

                        parent = grandparent

    return None


def check_path():
    path = path_entry.get().strip()

    # Check empty input first
    if not path:
        messagebox.showerror("Error", "Please select your GAME FOLDER.")
        result_label.config(text="")
        result_label2.config(text="")
        return

    result = find_folder(path)

    if result:
        parent_path, matching_folder = result

        # Update the dropdown immediately
        update_dropdown(parent_path)

        # Input displays the parent folder containing /Songs/
        path_entry.config(state="normal")
        path_entry.delete(0, tk.END)
        path_entry.insert(0, parent_path)
        path_entry.config(state="readonly")

        # Label displays the exact matching folder
        result_label.config(text="NoteSkins folder found: " + matching_folder)
        page2_pathDisplay.config(text=f"This noteskin will be installed at:\n{matching_folder}")
        global cur_path
        cur_path = matching_folder

        ok_button.config(state="normal")
    else:
        ok_button.config(state="disabled")
        messagebox.showerror("Error", "Unable to locate the GAME FOLDER.")
        result_label.config(text="Unable to locate the GAME FOLDER")
        result_label2.config(text="")


def update_dropdown(parent_path):
    dropdown.set("")

    # Get the name of parent_path itself
    folder_name = os.path.basename(os.path.normpath(parent_path)).lower()

    for option, targets in FOLDER_OPTIONS.items():
        for target in targets:
            if target.lower() in folder_name:
                dropdown.set(option)
                result_label2.config(text="GAME automatically detected.")
                return

    print("No matching folder names found:", folder_name)
    result_label2.config(text="GAME unknown.")

def on_ok():
    parent_path = path_entry.get().strip()
    choice = dropdown.get().strip()
    path_parts = parent_path.lower().replace("\\", "/").split("/")
    choice_parts = choice.lower().replace("\\", "/").split("/")
    answer = True

    if not parent_path:
        messagebox.showerror("Error", "Please select your GAME FOLDER.")
        return

    if not choice:
        messagebox.showerror("Error", "Please select a GAME.")
        return

    if not any(
        choice_part in path_part
        for path_part in path_parts
        for choice_part in choice_parts
        if choice_part
    ):
        answer = messagebox.askyesno(
            "Confirm Settings",
            "The GAME FOLDER and the GAME do not match.\nAre you sure you want to continue with the current settings?"
        )

    if not answer:
        return

    customizations_path = os.path.join(root_path, "Customizations")
    previews_path = os.path.join(root_path, "Previews")

    if not os.path.isdir(customizations_path):
        messagebox.showerror(
            "Error",
            "'Customizations' folder not found:\n" + customizations_path
        )
        return

    global customization_dropdowns_created

    if not customization_dropdowns_created:
        create_customization_dropdowns(
            customizations_path,
            previews_path
        )
        customization_dropdowns_created = True

    show_page(page2)


# ---------------------INITIAL WINDOW-------------------------------
root = tk.Tk()
root.title("Celable and Metalable Noteskin Workshop: THE PROGRAM")
root.update_idletasks()

icon_path = root_path / "icon.ico"
if icon_path.exists():
    try:
        root.iconbitmap(str(icon_path))
    except tk.TclError:
        pass

width = 640
height = 480

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

x = (screen_width - width) // 2
# Make sure the window doesn't hide behind the taskbar
y = max(0, (screen_height - height) // 2 - 25)

root.geometry("{}x{}+{}+{}".format(width, height, x, y))

root.minsize(640, 480)

page1 = tk.Frame(root)
page2 = tk.Frame(root)
page3 = tk.Frame(root)
page1.pack(fill="both", expand=True)


# --- THE ACTUAL ELEMENTS ON PAGE1 ---
# Image
try:
    image = tk.PhotoImage(file="logo.png")
    image = image.subsample(3, 3)
    image_label = tk.Label(page1, image=image)
    image_label.pack(pady=1)
except tk.TclError:
    image = None
    error_label = tk.Label(page1, text="Error: Could not find or load logo.png")
    error_label.pack()

# String input
tk.Label(
    page1,
    text="Select your GAME FOLDER:"
).pack(padx=10, pady=(10, 0))

path_var = tk.StringVar(value="Click here to select...")
path_entry = tk.Entry(
    page1,
    width=70,
    state="readonly",
    textvariable=path_var,
    fg="gray"
)
path_entry.pack(padx=10, pady=5)

def browse_game_folder(event=None):
    folder = filedialog.askdirectory(
        title="Select your Game Folder",
        mustexist=True
    )

    if folder:
        path_var.set(folder)
        path_entry.config(fg="black")


path_entry.bind("<Button-1>", browse_game_folder)


def on_path_change(*args):
    ok_button.config(state="disabled")


path_var.trace_add("write", on_path_change)

tk.Button(page1, text="Locate", command=check_path).pack(pady=5)

result_label = tk.Label(page1, text="")
result_label.pack()
result_label2 = tk.Label(page1, text="")
result_label2.pack()

# Dropdown menu
tk.Label(page1, text="Select your GAME:").pack(pady=(15, 0))

dropdown = ttk.Combobox(
    page1,
    values=["Stepmania 5/ITGmania/Etterna/OutFox", "NotITG/OpenITG"],
    state="readonly",
    width=70
)
dropdown.set("")
dropdown.pack(pady=5)

# OK button
ok_button = tk.Button(
    page1,
    text="OK",
    command=on_ok,
    state="disabled",
    disabledforeground="gray"
)
ok_button.pack(pady=(35, 10))



# ---------------------PAGE 2: CUSTOMIZE YOUR SKIN-------------------------------

preview_label = None
preview_frames = []
preview_frame_index = 0
preview_after_id = None
preview_photo = None

arrows_notice_label = None

PREVIEW_CATEGORY_MAP = {
    "Holds": "Holds + Rolls",
    "Rolls": "Holds + Rolls",
    "Mine Settings/Size/Normal": "Mine Settings/Size/Mine Size Comparison",
    "Mine Settings/Size/Mini": "Mine Settings/Size/Mine Size Comparison"
}
#left, top, right, bottom
PREVIEW_CROP_MAP = {
    "Holds/Celable/ITG": (0, 150, 1001, 5),
    "Holds/Metalable/ITG": (332, 150, 670, 5),
    "Holds/Metalable/ITG/Default Encore": (286, 150, 711, 5),
    "Holds/Vividable/ITG": (665, 150, 335, 5),
    "Rolls/ITG": (999, 150, 0, 5),
    "Rolls/ITG/Default Encore": (742, 150, 258, 5),

    "Holds/Celable/Toon": (0, 150, 668, 5),
    "Holds/Metalable/Toon": (332, 150, 336, 5),
    "Rolls/Toon": (666, 150, 0, 5),

    "Holds/Celable/VIP": (0, 150, 668, 5),
    "Holds/Celable/VIP/Default Ionic": (110, 125, 560, 30),
    "Holds/Celable/VIP/Default Ionic Border": (580, 125, 86, 30),
    "Holds/Metalable/VIP": (332, 150, 336, 5),
    "Rolls/VIP": (666, 150, 0, 5),

    "Hold Explosions/Celable/Minimal": (471, 0, 997, 0),
    "Hold Explosions/Celable/Spark": (968, 0, 500, 0),
    "Hold Explosions/Celable/Glow": (1452, 0, 0, 0),

    "Hold Explosions/Metalable/Minimal": (471, 0, 997, 0),
    "Hold Explosions/Metalable/Spark": (968, 0, 500, 0),
    "Hold Explosions/Metalable/Glow": (1452, 0, 0, 0),

    "Hold Explosions/Vividable/Minimal": (471, 0, 997, 0),
    "Hold Explosions/Vividable/Spark": (968, 0, 500, 0),
    "Hold Explosions/Vividable/Glow": (1452, 0, 0, 0),

    "Tap Explosions/Celable/Minimal": (0, 885, 0, 0),
    "Tap Explosions/Celable/Spark": (0, 285, 0, 605),
    "Tap Explosions/Celable/Glow": (0, 585, 0, 305),

    "Tap Explosions/Metalable/Minimal": (0, 885, 0, 0),
    "Tap Explosions/Metalable/Spark": (0, 285, 0, 605),
    "Tap Explosions/Metalable/Glow": (0, 585, 0, 305),

    "Tap Explosions/Vividable/Minimal": (0, 885, 0, 0),
    "Tap Explosions/Vividable/Spark": (0, 285, 0, 605),
    "Tap Explosions/Vividable/Glow": (0, 585, 0, 305),
}
PREVIEW_MAX_HEIGHT = {
    "Hold Explosions": 200,
    "Receptors": 170,
    "Mine Settings/Size": 200
}
PREVIEW_FILENAME_REMOVE_WORDS = ["Ionic", "Crystallis"]
TREAT_CHILDREN_AS_CATEGORIES = ["Mine Settings"]
# remove (default) from this
PATH_HAS_ARBITRARY_IMAGE_NAMES = ["Mine Settings/Size/Mine Size Comparison"]
# remove (default) from this
PATH_CHECK_NON_EXACT = [
    "Holds/Celable/ITG/leC",
    "Holds/Metalable/ITG/lateM",
    "Holds/Vividable/ITG/diviV",
    "Holds/Celable/VIP/Default Ionic Border",
    "Holds/Metalable/VIP/Default (Steel) Crystallis",
    "Rolls/VIP/Default (Heliodor)",
    "Rolls/ITG/lateM"
]
PLAYER_SELECTIONS = {}
PAGE2_DROPDOWNS = {}
FOLDER_ORDER_EXCEPTIONS = {
    "Holds": ["Rolls"],
    "Hold Explosions": ["Tap Explosions"],
}
CATEGORY_DESCRIPTIONS = {
    "Tap Explosions": f"In order: (Blue) Fantastic, White Fantastic, Excellent, Great, Decent, Way Off.\nNOTE: The White Fantastic tap explosion is only used in advanced timing windows in Outfox or ITGmania."
}


def clean_folder_name(name):
    # Remove "(default)" at the end, ignoring capitalization
    return re.sub(r"\s*\(default\)$", "", name, flags=re.IGNORECASE)

def sort_folders(folders):
    folders.sort(key=lambda folder: folder["name"].casefold())

    # Move each exception directly after its designated folder
    for anchor, followers in FOLDER_ORDER_EXCEPTIONS.items():
        anchor_index = next(
            (i for i, folder in enumerate(folders)
             if folder["name"].casefold() == anchor.casefold()),
            None
        )

        if anchor_index is None:
            continue

        for follower in followers:
            follower_index = next(
                (i for i, folder in enumerate(folders)
                 if folder["name"].casefold() == follower.casefold()),
                None
            )

            if follower_index is None:
                continue

            item = folders.pop(follower_index)

            # Find the anchor again, since removing an item shifts indices
            anchor_index = next(
                i for i, folder in enumerate(folders)
                if folder["name"].casefold() == anchor.casefold()
            )

            folders.insert(anchor_index + 1, item)

            # Keep multiple followers in their specified order
            anchor = follower

def scan_folders(folder_path):
    result = []

    try:
        entries = sorted(
            os.scandir(folder_path),
            key=lambda e: e.name.lower()
        )

        # Find NotITG or Outfox-ITGmania-Etterna folders at this level
        special_folders = [
            entry for entry in entries
            if entry.is_dir(follow_symlinks=False)
            and entry.name.lower() in ("notitg", "outfox-itgmania-etterna")
        ]

        # If either exists, skip this level and scan inside it
        if special_folders:
            return scan_folders(special_folders[0].path)

        for entry in entries:
            if not entry.is_dir(follow_symlinks=False):
                continue

            if entry.name.lower() == "metcelable-custom-3d":
                continue

            result.append({
                "name": entry.name,
                "path": entry.path,
                "children": scan_folders(entry.path)
            })

    except OSError:
        pass

    return result


def get_max_depth(nodes):
    if not nodes:
        return 0

    return 1 + max(get_max_depth(node["children"]) for node in nodes)

# --- FUNCTIONS FOR THE CUSTOMIZATION DROPDOWNS ---
# For updating the lower level customization dropdowns when a dropdown has its option changed
def update_customization_options(
    dropdowns,
    level_options,
    level,
    nodes,
    category_name,
    preview_category,
    previews_path,
    preview_label
):
    # Clear this level and all levels below it.
    for i in range(level, len(dropdowns)):
        level_options[i] = []
        dropdowns[i]["values"] = ()
        dropdowns[i].set("")

    # Stop when there are no more dropdown levels.
    if level >= len(dropdowns):
        return

    level_options[level] = nodes
    dropdown = dropdowns[level]
    dropdown["values"] = [node["name"] for node in nodes]

    if nodes:
        # Select the default folder, or the first folder.
        selected_index = 0

        for i, node in enumerate(nodes):
            if node["name"].lower().endswith("(default)"):
                selected_index = i
                break

        dropdown.current(selected_index)

        # Initialize the next level first.
        update_customization_options(
            dropdowns,
            level_options,
            level + 1,
            nodes[selected_index]["children"],
            category_name,
            preview_category,
            previews_path,
            preview_label
        )

    # Update the preview only after all dropdown levels are initialized.
    if level == 0:
        update_preview(
            previews_path,
            category_name,
            preview_category,
            dropdowns,
            level_options,
            preview_label
        )


def on_customization_selected(
    dropdowns,
    level_options,
    level,
    category_name,
    previews_path,
    preview_label
):
    index = dropdowns[level].current()

    if index < 0 or index >= len(level_options[level]):
        return

    selected_node = level_options[level][index]

    # Map the customization category to its preview folder.
    preview_category = category_name

    for key in sorted(PREVIEW_CATEGORY_MAP, key=len, reverse=True):
        if (
            preview_category == key
            or preview_category.startswith(key + "/")
        ):
            preview_category = PREVIEW_CATEGORY_MAP[key] + preview_category[len(key):]
            break

    # First rebuild all child dropdowns and select their defaults.
    update_customization_options(
        dropdowns,
        level_options,
        level + 1,
        selected_node["children"],
        category_name,
        preview_category,
        previews_path,
        preview_label
    )

    # Then update the preview using the completed selections.
    update_preview(
        previews_path,
        category_name,
        preview_category,
        dropdowns,
        level_options,
        preview_label
    )

    # Show/Hide the Arrows notice
    if arrows_notice_label is not None:
        # If there's On - Vividable in any string inside PLAYER_SELECTIONS["Arrow Center Animation"]
        if any("On - Vividable" in s for s in PLAYER_SELECTIONS["Arrow Center Animation"]):
            # If there's Vividable on the second string of PLAYER_SELECTIONS["Arrows"]
            if len(PLAYER_SELECTIONS["Arrows"]) > 1 and "Vividable" in PLAYER_SELECTIONS["Arrows"][1]:
                arrows_notice_label.pack_forget()
            else:
                arrows_notice_label.config(text="Arrow Center Animation is 'On - Vividable'. Arrows will be animated at 0.5x the speed of this preview.")
                arrows_notice_label.pack(anchor="w", pady=(5, 0))
        elif any("On - Default" in s for s in PLAYER_SELECTIONS["Arrow Center Animation"]):
            if len(PLAYER_SELECTIONS["Arrows"]) > 1 and "Vividable" in PLAYER_SELECTIONS["Arrows"][1]:
                arrows_notice_label.config(text="Arrow Center Animation is 'On - Default'. Arrows will be animated at 2x the speed of this preview.")
                arrows_notice_label.pack(anchor="w", pady=(5, 0))
            else:
                arrows_notice_label.pack_forget()
        elif any("Off" in s for s in PLAYER_SELECTIONS["Arrow Center Animation"]):
            arrows_notice_label.config(text="Arrow Center Animation is 'Off'.")
            arrows_notice_label.pack(anchor="w", pady=(5, 0))
        else:
            arrows_notice_label.pack_forget()

def cycle_dropdown(dropdown, direction):
    values = dropdown["values"]

    if not values:
        return

    current = dropdown.current()

    # If nothing is selected, start at the first option
    if current < 0:
        current = 0 if direction > 0 else len(values) - 1
    else:
        current = (current + direction) % len(values)

    dropdown.current(current)

    # Trigger the existing selection handler
    dropdown.event_generate("<<ComboboxSelected>>")

def create_customization_dropdowns(customizations_path, previews_path):
    if not os.path.isdir(customizations_path):
        messagebox.showerror(
            "Error",
            "Customizations folder not found:\n" + customizations_path
        )
        return

    # Remove previously generated widgets
    for widget in customization_dropdown_frame.winfo_children():
        widget.destroy()

    # Find immediate category folders
    try:
        folders = []

        for entry in os.scandir(customizations_path):
            if not entry.is_dir(follow_symlinks=False):
                continue

            if entry.name.lower() == "metcelable-custom-3d":
                continue

            if entry.name in TREAT_CHILDREN_AS_CATEGORIES:
                children = list(os.scandir(entry.path))

                # Prefer NotITG or Outfox-ITGmania-Etterna as the category root
                preferred = next(
                    (
                        child for target in ("NotITG", "Outfox-ITGmania-Etterna")
                        for child in children
                        if child.is_dir(follow_symlinks=False)
                        and child.name.lower() == target.lower()
                    ),
                    None
                )

                category_root = preferred.path if preferred else entry.path
                category_prefix = (
                    entry.name + "/" + preferred.name
                    if preferred else entry.name
                )

                for child in os.scandir(category_root):
                    if child.is_dir(follow_symlinks=False):
                        folders.append({
                            "name": category_prefix + "/" + child.name,
                            "path": child.path
                        })
            else:
                folders.append({
                    "name": entry.name,
                    "path": entry.path
                })

        sort_folders(folders)

    except OSError as error:
        messagebox.showerror("Error", str(error))
        return

    tk.Label(
        customization_dropdown_frame,
        text='SELECT A SUITE',
        font=("Arial", 11, "bold")
    ).pack(anchor="w")

    tk.Label(
        customization_dropdown_frame,
        text="Don't know what customizations to pick? Pick a SUITE pre-customized just for you!",
    ).pack(anchor="w")

    tk.Button(
        customization_dropdown_frame,
        text="OPEN Suite Select",
        command=lambda:
            show_page(page3)
    ).pack(anchor="w",pady=(0,10))

    for folder in folders:
        category_name = folder["name"]
        category_path = folder["path"]

        # One container per category
        category_frame = tk.Frame(customization_dropdown_frame)
        category_frame.pack(fill="x", padx=10, pady=(12, 8))

        # If a category in TREAT_CHILDREN_AS_CATEGORIES has its first child as NotITG, then it won't be included in the displayed name
        tk.Label(
            category_frame,
            text=category_name.replace("/", " - ").replace(" - NotITG", ""),
            font=("Arial", 11, "bold")
        ).pack(anchor="w")

        if category_name in CATEGORY_DESCRIPTIONS:
            labil = tk.Label(
                category_frame,
                text="",
                justify="left",
                anchor="w",
                wraplength=560
            )
            labil.pack(fill="x", expand=True)

            labil.config(text=CATEGORY_DESCRIPTIONS[category_name])

            def update_wrap(event, label=labil):
                width = label.winfo_width()
                if width > 1:
                    label.config(wraplength=width)


            labil.bind("<Configure>", update_wrap)

        # Dedicated dropdown container
        dropdown_frame = tk.Frame(category_frame)
        dropdown_frame.pack(fill="x")

        # Dedicated preview for this category
        preview_label = tk.Label(
            category_frame,
            text="No preview available",
            anchor="w"
        )
        preview_label.pack(anchor="w", pady=(5, 0))

        global arrows_notice_label

        if category_name == "Arrows":
            arrows_notice_label = tk.Label(
                category_frame,
                text="AAAAAAAAAAAAAAAAAAAAA",
                fg="red",
                anchor="w",
                justify="left",
                wraplength=520
            )

        # Build this category's dropdown hierarchy
        tree = scan_folders(category_path)
        depth = get_max_depth(tree)

        dropdowns = []
        control_frames = []
        level_options = []

        for level in range(depth):
            # Container for < button, dropdown, > button
            control_frame = tk.Frame(dropdown_frame)

            dropdown = ttk.Combobox(
                control_frame,
                state="readonly",
                width=30
            )

            for event in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
                dropdown.bind(event, on_mousewheel)

            previous_button = tk.Button(
                control_frame,
                text="<",
                width=1,
                command=lambda d=dropdown:
                    cycle_dropdown(d, -1)
            )

            next_button = tk.Button(
                control_frame,
                text=">",
                width=1,
                command=lambda d=dropdown:
                    cycle_dropdown(d, 1)
            )

            previous_button.pack(side="left")
            dropdown.pack(side="left", padx=2)
            next_button.pack(side="left")

            # Store the actual dropdown and its layout container separately
            dropdowns.append(dropdown)
            control_frames.append(control_frame)
            level_options.append([])

            dropdown.bind(
                "<<ComboboxSelected>>",
                lambda event,
                       d=dropdowns,
                       o=level_options,
                       i=level,
                       c=category_name,
                       p=previews_path,
                       pl=preview_label:
                    on_customization_selected(
                        d, o, i, c, p, pl
                    )
            )

        # Wrap dropdowns and all the controls within this category's own container
        dropdown_frame.bind(
            "<Configure>",
            lambda event, f=dropdown_frame, d=control_frames:
                wrap_dropdowns(event, f, d)
        )

        # Populate dropdowns and load the initial preview
        preview_category = category_name

        for key in sorted(PREVIEW_CATEGORY_MAP, key=len, reverse=True):
            if (
                preview_category == key
                or preview_category.startswith(key + "/")
            ):
                preview_category = PREVIEW_CATEGORY_MAP[key] + preview_category[len(key):]
                break

        PAGE2_DROPDOWNS[category_name] = dropdowns

        update_customization_options(
            dropdowns,
            level_options,
            0,
            tree,
            category_name,       # Original Customizations category
            preview_category,    # Mapped Previews folder
            previews_path,
            preview_label
        )

def wrap_dropdowns(event, frame, dropdowns, gap=10):
    frame_width = event.width
    x = 0
    y = 0
    row_height = 35

    for dropdown in dropdowns:
        dropdown.update_idletasks()
        widget_width = dropdown.winfo_reqwidth()

        if x > 0 and x + widget_width > frame_width:
            x = 0
            y += row_height

        dropdown.place(x=x, y=y)
        x += widget_width + gap

    # Reserve enough height for every row
    required_height = y + row_height

    if frame.winfo_height() != required_height:
        frame.configure(height=required_height)

    # Prevent the frame from shrinking around placed widgets
    frame.pack_propagate(False)



# ---FUNCTIONS FOR THE PREVIEWS---

def update_preview(
    previews_path,
    category_name,         # Original Customizations category
    preview_category,      # Mapped Previews folder
    dropdowns,
    level_options,
    preview_label
):
    # Identify this update so stale background loads can be ignored.
    preview_label._load_id = getattr(preview_label, "_load_id", 0) + 1
    load_id = preview_label._load_id

    category_path = os.path.join(previews_path, preview_category)
    image_extensions = (".png", ".jpg", ".jpeg", ".bmp", ".gif")

    selected_names_with_default = []
    # Get selected names, removing "(default)".
    selected_names = []

    for level, dropdown in enumerate(dropdowns):
        if level >= len(level_options) or not level_options[level]:
            break

        index = dropdown.current()

        if index < 0 or index >= len(level_options[level]):
            break

        # Use the node corresponding to the current dropdown selection.
        selected_node = level_options[level][index]
        name = selected_node["name"]

        selected_names_with_default.append(name)

        name = re.sub(
            r"\s*\(default\)$",
            "",
            name,
            flags=re.IGNORECASE
        ).strip()

        selected_names.append(name)

    def find_image(folder_path, selected_name=None):
        # Search only inside the selected folder, preferring its named image.
        if not os.path.isdir(folder_path):
            return None

        try:
            entries = sorted(
                os.scandir(folder_path),
                key=lambda entry: entry.name.lower()
            )

            # Prefer an image whose filename matches the final selection.
            if selected_name:
                for entry in entries:
                    if (
                        entry.is_file()
                        and os.path.splitext(entry.name)[0].lower()
                        == selected_name.lower()
                        and entry.name.lower().endswith(image_extensions)
                    ):
                        return entry.path

            # Search child folders, but allow arbitrary images for specified categories
            current_cust_path = os.path.relpath(folder_path, previews_path).replace("\\", "/")

            if any(
                current_cust_path == path
                or current_cust_path.startswith(path + "/")
                for path in PATH_HAS_ARBITRARY_IMAGE_NAMES
            ):
                for entry in entries:
                    if entry.is_file(follow_symlinks=False):
                        if entry.name.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                            return entry.path

            # Otherwise, do not accept arbitrary images from the current folder
            for entry in entries:
                if entry.is_dir(follow_symlinks=False):
                    result = find_image(entry.path, selected_name)
                    if result:
                        return result

        except OSError:
            pass

        return None

    def candidate_paths(names):
        # Try selected folder names in order, allowing missing levels.
        candidates = []

        for count in range(len(names), -1, -1):
            for subset in combinations(names, count):
                path = os.path.join(category_path, *subset)

                if os.path.isdir(path):
                    candidates.append((count, path))

            if candidates:
                break

        return candidates

    
    image_path = None
    PLAYER_SELECTIONS[category_name] = selected_names_with_default

    # Stop the previous GIF animation if one is playing
    if hasattr(preview_label, "_gif_after_id"):
        try:
            preview_label.after_cancel(preview_label._gif_after_id)
        except Exception:
            pass

    preview_label._gif_after_id = None

    # TO-DO: might need to clean this shit up but god i'm so tired of all this path matching already
    if os.path.isdir(category_path):
        selected_cust_path = "/".join([category_name] + selected_names)

        mapped_path = selected_cust_path

        for key in sorted(PREVIEW_CATEGORY_MAP, key=len, reverse=True):
            if mapped_path == key or mapped_path.startswith(key + "/"):
                mapped_path = (
                    PREVIEW_CATEGORY_MAP[key]
                    + mapped_path[len(key):]
                )
                break

        mapped_parts = mapped_path.split("/")

        category_path = os.path.join(previews_path, mapped_parts[0])
        mapped_selected_names = mapped_parts[1:]

        if any(
            selected_cust_path == path
            or selected_cust_path.startswith(path + "/")
            for path in PATH_HAS_ARBITRARY_IMAGE_NAMES
        ):
            # This category always uses an image from its preview folder,
            # regardless of the selected dropdown options.
            for entry in sorted(
                os.scandir(category_path),
                key=lambda entry: entry.name.lower()
            ):
                if (
                    entry.is_file(follow_symlinks=False)
                    and entry.name.lower().endswith(image_extensions)
                ):
                    image_path = entry.path
                    break

        elif selected_names:
            # Use the mapped path components for preview searching
            search_names = mapped_parts[1:]
            last_selected = search_names[-1]

            # Try the original final dropdown name first.
            filename_candidates = [last_selected]

            # Then try removing configured words from that name.
            fallback_name = last_selected

            for word in PREVIEW_FILENAME_REMOVE_WORDS:
                fallback_name = re.sub(
                    r"\b" + re.escape(word) + r"\b",
                    "",
                    fallback_name,
                    flags=re.IGNORECASE
                )

            fallback_name = re.sub(r"\s+", " ", fallback_name).strip()

            if fallback_name and fallback_name.lower() != last_selected.lower():
                filename_candidates.append(fallback_name)

            # Search the same parent folders as the original code.
            # Check whether this selected path allows partial filename matches
            selected_path = "/".join([category_name] + selected_names)

            allow_partial_match = any(
                selected_path == path or selected_path.startswith(path + "/")
                for path in PATH_CHECK_NON_EXACT
            )

            for count in range(len(search_names) - 1, -1, -1):
                for subset in combinations(search_names[:-1], count):
                    parent_path = os.path.join(category_path, *subset)

                    if not os.path.isdir(parent_path):
                        continue

                    try:
                        entries = sorted(
                            os.scandir(parent_path),
                            key=lambda entry: entry.name.lower()
                        )
                    except OSError:
                        continue

                    for name in filename_candidates:
                        for entry in entries:
                            if not entry.is_file(follow_symlinks=False):
                                continue

                            if not entry.name.lower().endswith(image_extensions):
                                continue

                            filename = os.path.splitext(entry.name)[0].lower()
                            target = name.lower()

                            if (
                                filename == target
                                or (
                                    allow_partial_match
                                    and (
                                        target in filename
                                        or filename in target
                                    )
                                )
                            ):
                                image_path = entry.path
                                break

                        if image_path:
                            break

                    if image_path:
                        break

                if image_path:
                    break

            # If no matching image filename exists, look for a folder
            # matching the final selection, allowing missing levels.
            if image_path is None:
                candidates = candidate_paths(search_names)

                if candidates:
                    _, best_path = candidates[0]

                    if os.path.basename(best_path).lower() == last_selected.lower():
                        image_path = find_image(best_path, last_selected)

    if image_path is None:
        preview_label.configure(
            image="",
            text="No preview available"
        )
        preview_label.image = None
        preview_label._gif_photos = None
        return

    try:
        preview_label._gif_after_id = None

        # Build crop keys from the selected dropdowns.
        crop_keys = [category_name]
        current_key = category_name

        for name in selected_names:
            current_key += "/" + name
            crop_keys.append(current_key)

        # Most-specific crop rule takes priority.
        crop = (0, 0, 0, 0)

        for key in reversed(crop_keys):
            if key in PREVIEW_CROP_MAP:
                crop = PREVIEW_CROP_MAP[key]
                break

        left, top, right, bottom = crop

        max_height = 300

        for key in reversed(crop_keys):
            if key in PREVIEW_MAX_HEIGHT:
                max_height = PREVIEW_MAX_HEIGHT[key]
                break

        def prepare_frame(frame):
            frame = frame.copy().convert("RGBA")
            width, height = frame.size

            if left + right < width and top + bottom < height:
                frame = frame.crop((
                    left,
                    top,
                    width - right,
                    height - bottom
                ))

            frame.thumbnail(
                (550, max_height),
                Image.LANCZOS
            )

            return frame

        # Display the first frame immediately.
        with Image.open(image_path) as image:
            first_frame = prepare_frame(image)

        first_photo = ImageTk.PhotoImage(first_frame)

        preview_label.configure(image=first_photo, text="")
        preview_label.image = first_photo
        preview_label._gif_photos = [first_photo]
        preview_label._gif_index = 0

        results = queue.Queue(maxsize=1)

        # image loading code i totally did not steal
        def load_image():
            try:
                frames = []
                durations = []

                with Image.open(image_path) as image:
                    is_animated = (
                        image.format == "GIF"
                        and getattr(image, "is_animated", False)
                    )

                    if is_animated:
                        for frame in ImageSequence.Iterator(image):
                            # Capture duration before processing the frame.
                            duration = max(
                                20,
                                frame.info.get("duration", 100)
                            )

                            frames.append(prepare_frame(frame))
                            durations.append(duration)

                    else:
                        frames.append(prepare_frame(image))
                        durations.append(100)

                if not frames:
                    raise ValueError("Image contains no frames")

                results.put((
                    frames,
                    durations,
                    is_animated,
                    None
                ))

            except Exception as error:
                results.put((None, None, False, error))

        # Decode, crop and resize away from Tkinter's main thread.
        threading.Thread(
            target=load_image,
            daemon=True
        ).start()

        def check_results():
            # Stop polling if another preview was requested.
            if load_id != preview_label._load_id:
                return

            try:
                frames, durations, is_animated, error = (
                    results.get_nowait()
                )
            except queue.Empty:
                preview_label._gif_after_id = preview_label.after(
                    30, check_results
                )
                return

            preview_label._gif_after_id = None

            if error is not None:
                preview_label.configure(
                    image="",
                    text="Unable to load preview"
                )
                preview_label.image = None
                preview_label._gif_photos = None

                print("Preview error:", image_path, error)
                return

            photos = []

            def create_photos(start=0):
                if load_id != preview_label._load_id:
                    return

                # Create only five Tkinter images per callback.
                end = min(start + 5, len(frames))

                try:
                    for i in range(start, end):
                        photos.append(
                            ImageTk.PhotoImage(frames[i])
                        )
                except Exception as error:
                    preview_label.configure(
                        image="",
                        text="Unable to load preview"
                    )
                    preview_label.image = None
                    preview_label._gif_photos = None

                    print("Preview error:", image_path, error)
                    return

                if end < len(frames):
                    preview_label._gif_after_id = preview_label.after(
                        1,
                        lambda: create_photos(end)
                    )
                    return

                # Keep references so Tkinter does not discard the images.
                preview_label._gif_photos = photos
                preview_label._gif_index = 0

                preview_label.configure(
                    image=photos[0],
                    text=""
                )
                preview_label.image = photos[0]

                if is_animated and len(photos) > 1:
                    animate_gif()

            def animate_gif():
                if load_id != preview_label._load_id:
                    return

                preview_label._gif_index = (
                    preview_label._gif_index + 1
                ) % len(photos)

                index = preview_label._gif_index
                photo = photos[index]

                preview_label.configure(image=photo)
                preview_label.image = photo

                preview_label._gif_after_id = preview_label.after(
                    durations[index],
                    animate_gif
                )

            create_photos()

        # Poll without blocking the GUI.
        check_results()

    except Exception as error:
        preview_label.configure(
            image="",
            text="Unable to load preview"
        )
        preview_label.image = None
        preview_label._gif_photos = None

        print("Preview error:", image_path, error)

def find_custom_3d_folder(category, selections, selected_game, folder_name):
    customizations_path = os.path.join(
            root_path,
            "Customizations"
        )
    current_path = os.path.join(customizations_path, category)

    if not os.path.isdir(current_path):
        return None

    for selection in selections:

        # Handle NotITG/Outfox-ITGmania-Etterna folders wherever they appear
        game_choice_folders = [
            name for name in ("NotITG", "Outfox-ITGmania-Etterna")
            if os.path.isdir(os.path.join(current_path, name))
        ]

        if game_choice_folders:
            if selected_game not in game_choice_folders:
                return None

            current_path = os.path.join(current_path, selected_game)

        # Follow the next selected customization
        current_path = os.path.join(current_path, selection)

        if not os.path.isdir(current_path):
            return None

    # Check the final selected folder
    custom_3d_path = os.path.join(current_path, folder_name)
    if os.path.isdir(custom_3d_path):
        return custom_3d_path

    # Search below the final selected folder for metcelable-custom-3d
    for root, dirs, files in os.walk(current_path):
        if folder_name in dirs:
            return os.path.join(root, folder_name)

    return None

def read_saved_selections():
    try:
        with open(SAVED_SELECTIONS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}
    except (json.JSONDecodeError, OSError):
        return {}

def save_named_selection(name):
    name = name.strip()

    if not name:
        return False

    saved = read_saved_selections()
    saved[name] = copy.deepcopy(PLAYER_SELECTIONS)

    with open(SAVED_SELECTIONS_FILE, "w", encoding="utf-8") as file:
        json.dump(saved, file, indent=4)

    return True

def install_skin(CURRENT_PATH):
    if not noteskin_name_entry.get().strip():
        messagebox.showwarning(
            "Error",
            "Please give this noteskin a NAME."
        )
        return
    answer = messagebox.askyesno(
        "Confirm Settings",
        f"About to install noteskin:\n{CURRENT_PATH}\\{noteskin_name_entry.get()}\n\nThis will also OVERWRITE any existing noteskin with the same name. Continue?"
    )
    if not answer:
        return
    folder_name = "metcelable-custom-3d"
    base_path = os.path.join(
        root_path,
        "Celable-Metalable - BASE"
    )
    GameState = dropdown.get()

    # Choose the desired folder
    if GameState == "Stepmania 5/ITGmania/Etterna/OutFox":
        selected_game = "Outfox-ITGmania-Etterna"
    else:
        selected_game = "NotITG"

    # Source: BASE/NotITG/metcelable-custom-3d or the other one
    source_mclb = os.path.join(
        base_path,
        selected_game,
        folder_name
    )

    if not os.path.isdir(source_mclb):
        messagebox.showerror("Error", "Failed to find metcelable-custom-3d inside Celable-Metalable - BASE.")
        return False

    # Create a temporary working copy of source_mclb
    with tempfile.TemporaryDirectory() as temp_dir:
        working_mclb = os.path.join(temp_dir, "metcelable-custom-3d")

        # Copy the original into the working folder
        shutil.copytree(source_mclb, working_mclb)

        # Merge customizations into the working copy
        for category, selections in PLAYER_SELECTIONS.items():
            source_customizations = find_custom_3d_folder(
                category,
                selections,
                selected_game,
                folder_name
            )

            print('The source:', source_customizations)

            if source_customizations:
                shutil.copytree(
                    source_customizations,
                    working_mclb,
                    dirs_exist_ok=True
                )

        # Destination: CURRENT_PATH/metcelable-custom-3d or user's chosen name
        destination = os.path.join(CURRENT_PATH, noteskin_name_entry.get())

        # Remove existing destination
        if os.path.exists(destination):
            if os.path.isdir(destination) and not os.path.islink(destination):
                shutil.rmtree(destination)
            else:
                os.remove(destination)

        # Copy the finished working copy to destination
        shutil.copytree(working_mclb, destination)

    if selected_game == "Outfox-ITGmania-Etterna":
        messagebox.showinfo("Notice", "Noteskin installed. Reload theme and textures (F2 or F3+F6+6) in your GAME to apply the changes.")
    else:
        messagebox.showinfo("Notice", "Noteskin installed. Restart the GAME to apply the changes.")
    return True


def validate_name_entry(value):
    return re.fullmatch(r"[A-Za-z0-9+_-]*", value) is not None

vcmd = (root.register(validate_name_entry), "%P")


def save_custom_suite():
    suite_name = noteskin_name_entry.get().strip()

    if not suite_name:
        messagebox.showwarning(
            "Error",
            "Please give this SUITE a NAME."
        )
        return

    saved_suites = read_saved_selections()

    if suite_name in saved_suites:
        overwrite = messagebox.askyesno(
            "Notice",
            f'"{suite_name}" already exists. OVERWRITE it?'
        )

        if not overwrite:
            return

    try:
        save_named_selection(suite_name)
        refresh_saved_selection_names()
        custom_dropdown.set(suite_name)

        messagebox.showinfo(
            "Notice",
            f'"{suite_name}" has been saved as a CUSTOM SUITE.\nYou can select this SUITE any time in Suite Select menu.'
        )

    except OSError as error:
        messagebox.showerror("Save Failed", str(error))


# --- THE ACTUAL ELEMENTS ON PAGE2 ---

page2_pathDisplay = tk.Label(page2, text="")
page2_pathDisplay.pack()

name_entry_frame = tk.Frame(page2)
name_entry_frame.pack(pady=(10, 10))

tk.Label(name_entry_frame, text="My noteskin's NAME is:").pack(side="left", padx=5)

noteskin_name_entry = tk.Entry(
    name_entry_frame,
    width=35,
    validate="key",
    validatecommand=vcmd
)
noteskin_name_entry.pack(side="left", padx=5)
noteskin_name_entry.insert(0, "metcelable-custom-3d")

button_frame = tk.Frame(page2)
button_frame.pack(pady=(0, 10))

# Back button
back_button = tk.Button(
    button_frame,
    text="BACK to Game Select",
    command=lambda: show_page(page1),
)
back_button.pack(side="left", padx=5)

suite_save_button = tk.Button(
    button_frame,
    text="SAVE as SUITE",
    command=save_custom_suite
)
suite_save_button.pack(side="left", padx=5)

save_button = tk.Button(
    button_frame,
    text="INSTALL Noteskin",
    command=lambda: install_skin(cur_path),
)
save_button.pack(side="left", padx=5)

# Scrollable area on page2
# Container for the scrolling area
scroll_container = tk.Frame(page2)
scroll_container.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=5
)

page2_canvas = tk.Canvas(scroll_container)
page2_scrollbar = ttk.Scrollbar(
    scroll_container,
    orient="vertical",
    command=page2_canvas.yview
)

page2_canvas.configure(
    yscrollcommand=page2_scrollbar.set
)

page2_scrollbar.pack(side="right", fill="y")
page2_canvas.pack(side="left", fill="both", expand=True)

# Frame containing all customization dropdowns
customization_dropdown_frame = tk.Frame(page2_canvas)

page2_window = page2_canvas.create_window(
    (0, 0),
    window=customization_dropdown_frame,
    anchor="nw"
)

# Update scrollable area when content changes
def update_scroll_region(event=None):
    page2_canvas.configure(
        scrollregion=page2_canvas.bbox("all")
    )

customization_dropdown_frame.bind(
    "<Configure>", update_scroll_region
)

# Keep the inner frame the same width as the canvas
def resize_page2_frame(event):
    page2_canvas.itemconfigure(
        page2_window,
        width=event.width
    )

page2_canvas.bind("<Configure>", resize_page2_frame)

def on_mousewheel(event):
    widget = event.widget

    # Find the canvas containing the widget
    while widget is not None:
        if widget in (page2_canvas, page3_canvas):
            break
        
        if not isinstance(widget, tk.Misc):
            return "break"

        parent = widget.winfo_parent()
        if not parent:
            return "break"

        try:
            widget = widget.nametowidget(parent)
        except (KeyError, tk.TclError):
            return "break"

    if widget not in (page2_canvas, page3_canvas):
        return "break"

    # Scroll direction
    if getattr(event, "num", None) == 4:
        amount = -1
    elif getattr(event, "num", None) == 5:
        amount = 1
    elif event.delta:
        amount = -1 if event.delta > 0 else 1
        if abs(event.delta) >= 120:
            amount = -int(event.delta / 120)
    else:
        return "break"

    widget.yview_scroll(amount, "units")
    return "break"

# Windows / macOS
page2_canvas.bind_all("<MouseWheel>", on_mousewheel)

# Linux (X11)
page2_canvas.bind_all("<Button-4>", on_mousewheel)
page2_canvas.bind_all("<Button-5>", on_mousewheel)


# ---------------------PAGE 3: SELECT A SUITE-------------------------------
SUITE_PREVIEW_WIDTH = 500
SUITE_PREVIEW_HEIGHT = 280

import copy

COMMON_SETTINGS = {
    'Arrow Center Animation': ['On - Default (default)'],
    'Arrows': ['{type} (default)', 'ITG (default)'],
    'Hold Explosions': ['{type}', 'Minimal (default)', 'Default (default)'],
    'Holds': ['{type}', 'ITG (default)', 'Default (default)'],
    'Lifts': ['{type} - Hollowed Spectrum (default)'],
    'Mine Settings/Center Animation': ['On (default)'],
    'Mine Settings/Rotation': ['On - ITG (default)'],
    'Mine Settings/Size': ['Normal (default)'],
    'Mines': ['ITG (default)', 'Unquantized (default)', 'Default P1 (default)'],
    'Receptor Animation': ['On - Default (default)'],
    'Receptors': ['{type} - Traditional (default)', 'Gray (default)'],
    'Rolls': ['ITG (default)', 'Default (default)'],
    'Tap Explosions': ['{type}', 'Glow (default)', 'ITG (default)']
}


def create_suite(type, overrides=None):
    suite = {
        category: [option.format(type=type) for option in options]
        for category, options in COMMON_SETTINGS.items()
    }

    if type == 'Vividable':
        suite['Arrow Center Animation'] = ['On - Vividable']

    if overrides:
        for category, options in overrides.items():
            suite[category] = copy.deepcopy(options)

    return suite

BASE_SUITE_CONFIG = {
    'Celable': create_suite('Celable'),
    'Metalable': create_suite('Metalable'),
    'Vividable': create_suite('Vividable')
}
TEST_SUITE_CONFIG = {
    'Celable - Abridged Suite': {
            'Arrow Center Animation': ['On - Default (default)'],
            'Arrows': ['Celable (default)', 'Excel+ Basic'],
            'Hold Explosions': ['Celable', 'Minimal (default)', 'White'],
            'Holds': ['Celable', 'ITG (default)', 'DDR Hold'],
            'Lifts': ['Celable - Hollowed Spectrum (default)'],
            'Mine Settings/Center Animation': ['On (default)'],
            'Mine Settings/Rotation': ['On - Beta'],
            'Mine Settings/Size': ['Normal (default)'],
            'Mines': ['Beta', 'Default', ''],
            'Receptor Animation': ['On - Default (default)'],
            'Receptors': ['Celable - Frame', 'Gray'],
            'Rolls': ['ITG (default)', 'Note Roll'],
            'Tap Explosions': ['Celable', 'Glow (default)', 'ITG (default)']
        },
    'Celable - Bejeweled Suite': {
            'Arrow Center Animation': ['On - Default (default)'],
            'Arrows': ['Celable - Ionic', 'Gemstones Ionic Vibrant'],
            'Hold Explosions': ['Celable', 'Minimal (default)', 'Fire'],
            'Holds': ['Celable', 'VIP', 'Steel Ionic'],
            'Lifts': ['Celable - Hollowed Spectrum (default)'],
            'Mine Settings/Center Animation': ['On (default)'],
            'Mine Settings/Rotation': ['On - ITG (default)'],
            'Mine Settings/Size': ['Normal (default)'],
            'Mines': ['VIP', 'Unquantized', 'Default'],
            'Receptor Animation': ['On - Default (default)'],
            'Receptors': ['Celable - Ionic', 'Default (Steel)'],
            'Rolls': ['VIP', 'Default (Heliodor)'],
            'Tap Explosions': ['Celable', 'Spark', 'ITG']
        },
    'Celable - Bejeweled 2 Suite': {
            'Arrow Center Animation': ['On - Default (default)'],
            'Arrows': ['Celable - Ionic', 'Gemstones 2 Ionic Vibrant'],
            'Hold Explosions': ['Celable', 'Minimal (default)', 'RGB'],
            'Holds': ['Celable', 'VIP', 'Gold Ionic'],
            'Lifts': ['Celable - Hollowed Spectrum (default)'],
            'Mine Settings/Center Animation': ['On (default)'],
            'Mine Settings/Rotation': ['On - ITG (default)'],
            'Mine Settings/Size': ['Normal (default)'],
            'Mines': ['VIP', 'Unquantized', 'Steel'],
            'Receptor Animation': ['On - Default (default)'],
            'Receptors': ['Celable - Ionic', 'Copper'],
            'Rolls': ['VIP', 'Ice'],
            'Tap Explosions': ['Celable', 'Spark', 'ITG']
        },
    'Celable - Highlighted Suite': {
            'Arrow Center Animation': ['On - Default (default)'],
            'Arrows': ['Celable (default)', 'Lemma DDRainbow Vibrant Animated'],
            'Hold Explosions': ['Celable', 'Minimal (default)', 'Vapor'],
            'Holds': ['Celable', 'ITG (default)', 'Ocean'],
            'Lifts': ['Celable - Hollowed Spectrum (default)'],
            'Mine Settings/Center Animation': ['On (default)'],
            'Mine Settings/Rotation': ['On - ITG (default)'],
            'Mine Settings/Size': ['Normal (default)'],
            'Mines': ['ArrowVortex', 'Default P1', ''],
            'Receptor Animation': ['On - Default (default)'],
            'Receptors': ['Celable - Traditional (default)', 'D A N K'],
            'Rolls': ['ITG (default)', 'Fire Shadow'],
            'Tap Explosions': ['Celable', 'Spark', 'ITG']
        },
    'Celable - Inversed Suite': {
            'Arrow Center Animation': ['On - Default (default)'],
            'Arrows': ['Celable (default)', 'Lucid Addition'],
            'Hold Explosions': ['Celable', 'Minimal (default)', 'Falspawn'],
            'Holds': ['Celable', 'ITG (default)', 'Halloween Shadow'],
            'Lifts': ['Celable - Hollowed Spectrum (default)'],
            'Mine Settings/Center Animation': ['On (default)'],
            'Mine Settings/Rotation': ['On - ITG (default)'],
            'Mine Settings/Size': ['Mini'],
            'Mines': ['ITG (default)', 'Unquantized (default)', 'lateM'],
            'Receptor Animation': ['On - Default (default)'],
            'Receptors': ['Celable - Traditional (default)', 'Purple'],
            'Rolls': ['ITG (default)', 'DDR Hold Shadow'],
            'Tap Explosions': ['Celable', 'Glow (default)', 'ITG (default)']
        },
    'Celable - Kindled Suite': {
            'Arrow Center Animation': ['On - Default (default)'],
            'Arrows': ['Celable (default)','ITG TD Vibrant'],
            'Hold Explosions': ['Celable','Glow','Gold'],
            'Holds': ['Celable','ITG (default)','Fire'],
            'Lifts': ['Celable - Hollowed Spectrum (default)'],
            'Mine Settings/Center Animation': ['On (default)'],
            'Mine Settings/Rotation': ['On - ITG (default)'],
            'Mine Settings/Size': ['Mini'],
            'Mines': ['ITG (default)','Unquantized (default)','Falspawn Vibrant'],
            'Receptor Animation': ['On - Default (default)'],
            'Receptors': ['Celable - Traditional (default)','Halloween'],
            'Rolls': ['ITG (default)','Note Roll Shadow'],
            'Tap Explosions': ['Celable','Spark','ITG']
        },
    'Celable - Outlined Suite': {
            "Arrow Center Animation": ["On - Default (default)"],
            "Arrows": ["Celable - Plain","Dev Toon"],
            "Hold Explosions": ["Celable","Minimal (default)","Red"],
            "Holds": ["Celable","Toon","Default"],
            "Lifts": ["Celable - Hollowed Spectrum (default)"],
            "Mine Settings/Center Animation": ["On (default)"],
            "Mine Settings/Rotation": ["On - ITG (default)"],
            "Mine Settings/Size": ["Normal (default)"],
            "Mines": ["Toon","Purple"],
            "Receptor Animation": ["On - Default (default)"],
            "Receptors": ["Celable - Frame","Blue"],
            "Rolls": ["Toon","Default"],
            "Tap Explosions": ["Celable","Glow (default)","ITG (default)"]
        },
    'Celable - Polished Suite': {
            "Arrow Center Animation": ["On - Default (default)"],
            "Arrows": ["Celable (default)","Gemstones -REFLECTIVE- Vibrant"],
            "Hold Explosions": ["Celable","Glow","Fire"],
            "Holds": ["Celable","ITG (default)","Vapor"],
            "Lifts": ["Celable - Hollowed Spectrum (default)"],
            "Mine Settings/Center Animation": ["On (default)"],
            "Mine Settings/Rotation": ["On - ITG (default)"],
            "Mine Settings/Size": ["Mini"],
            "Mines": ["ITG (default)","Unquantized (default)","Orange -REFLECTIVE- Vibrant"],
            "Receptor Animation": ["On - Default (default)"],
            "Receptors": ["Celable - Frame","Christmas"],
            "Rolls": ["ITG (default)","Falspawn Shadow"],
            "Tap Explosions": ["Celable","Spark","ITG"]
        },
    'Celable - Reinforced Suite': {
            "Arrow Center Animation": ["On - Default (default)"],
            "Arrows": ["Celable (default)","Bright Encore"],
            "Hold Explosions": ["Celable","Minimal (default)","Ocean"],
            "Holds": ["Celable","ITG (default)","Default Shadow"],
            "Lifts": ["Celable - Hollowed Spectrum (default)"],
            "Mine Settings/Center Animation": ["On (default)"],
            "Mine Settings/Rotation": ["On - ITG (default)"],
            "Mine Settings/Size": ["Normal (default)"],
            "Mines": ["ITG (default)","Unquantized (default)","Default P1 -REFLECTIVE-"],
            "Receptor Animation": ["On - Default (default)"],
            "Receptors": ["Celable - Traditional (default)","White"],
            "Rolls": ["ITG (default)","Default Encore"],
            "Tap Explosions": ["Celable","Glow (default)","ITG (default)"]
        },
    'Celable - Sellable Suite': {
            "Arrow Center Animation": ["On - Default (default)"],
            "Arrows": ["Celable (default)","Bright -FLATSHINE- Gold"],
            "Hold Explosions": ["Celable","Glow","Yellow"],
            "Holds": ["Celable","ITG (default)","Gold Shadow"],
            "Lifts": ["Celable - Hollowed Spectrum (default)"],
            "Mine Settings/Center Animation": ["On (default)"],
            "Mine Settings/Rotation": ["On - ITG (default)"],
            "Mine Settings/Size": ["Mini"],
            "Mines": ["ITG (default)","Unquantized (default)","Default P1 -FLATSHINE- Gold"],
            "Receptor Animation": ["On - Default (default)"],
            "Receptors": ["Celable - Traditional (default)","Gold"],
            "Rolls": ["ITG (default)","Gold"],
            "Tap Explosions": ["Celable","Spark","Rainbowmatic"]
        },


    'Metalable - Abridged Suite': {
            'Arrow Center Animation': ['On - Default (default)'],
            'Arrows': ['Metalable (default)', 'Exmetal+ Basic'],
            'Hold Explosions': ['Metalable', 'Minimal (default)', 'White'],
            'Holds': ['Metalable', 'ITG (default)', 'DDR Hold'],
            'Lifts': ['Metalable - Hollowed Spectrum (default)'],
            'Mine Settings/Center Animation': ['On (default)'],
            'Mine Settings/Rotation': ['On - Beta'],
            'Mine Settings/Size': ['Normal (default)'],
            'Mines': ['Beta', 'Default', ''],
            'Receptor Animation': ['On - Default (default)'],
            'Receptors': ['Metalable - Frame', 'Gray'],
            'Rolls': ['ITG (default)', 'Note Roll'],
            'Tap Explosions': ['Metalable', 'Glow (default)', 'ITG (default)']
        },
    'Metalable - Bejeweled Suite': {
            'Arrow Center Animation': ['On - Default (default)'],
            'Arrows': ['Metalable - Crystallis', 'Gemstones Crystallis Vibrant'],
            'Hold Explosions': ['Metalable', 'Minimal (default)', 'Fire'],
            'Holds': ['Metalable', 'VIP', 'Default (Steel) Crystallis'],
            'Lifts': ['Metalable - Hollowed Spectrum (default)'],
            'Mine Settings/Center Animation': ['On (default)'],
            'Mine Settings/Rotation': ['On - ITG (default)'],
            'Mine Settings/Size': ['Normal (default)'],
            'Mines': ['VIP', 'Unquantized', 'Default'],
            'Receptor Animation': ['On - Default (default)'],
            'Receptors': ['Metalable - Crystallis', 'Default (Steel)'],
            'Rolls': ['VIP', 'Default (Heliodor)'],
            'Tap Explosions': ['Metalable', 'Spark', 'ITG']
        },
    'Metalable - Bejeweled 2 Suite': {
            'Arrow Center Animation': ['On - Default (default)'],
            'Arrows': ['Metalable - Crystallis', 'Gemstones 2 Crystallis Vibrant'],
            'Hold Explosions': ['Metalable', 'Minimal (default)', 'RGB'],
            'Holds': ['Metalable', 'VIP', 'Gold Crystallis'],
            'Lifts': ['Metalable - Hollowed Spectrum (default)'],
            'Mine Settings/Center Animation': ['On (default)'],
            'Mine Settings/Rotation': ['On - ITG (default)'],
            'Mine Settings/Size': ['Normal (default)'],
            'Mines': ['VIP', 'Unquantized', 'Steel'],
            'Receptor Animation': ['On - Default (default)'],
            'Receptors': ['Metalable - Crystallis', 'Copper'],
            'Rolls': ['VIP', 'Ice'],
            'Tap Explosions': ['Metalable', 'Spark', 'ITG']
        },
    'Metalable - Highlighted Suite': {
            'Arrow Center Animation': ['On - Default (default)'],
            'Arrows': ['Metalable (default)', 'Lemma DDRainbow Vibrant Animated'],
            'Hold Explosions': ['Metalable', 'Minimal (default)', 'Vapor'],
            'Holds': ['Metalable', 'ITG (default)', 'Ocean'],
            'Lifts': ['Metalable - Hollowed Spectrum (default)'],
            'Mine Settings/Center Animation': ['On (default)'],
            'Mine Settings/Rotation': ['On - ITG (default)'],
            'Mine Settings/Size': ['Normal (default)'],
            'Mines': ['ArrowVortex', 'Default P1', ''],
            'Receptor Animation': ['On - Default (default)'],
            'Receptors': ['Metalable - Traditional (default)', 'D A N K'],
            'Rolls': ['ITG (default)', 'Fire Shadow'],
            'Tap Explosions': ['Metalable', 'Spark', 'ITG']
        },
    'Metalable - Inversed Suite': {
            'Arrow Center Animation': ['On - Default (default)'],
            'Arrows': ['Metalable (default)', 'Lucid Addition'],
            'Hold Explosions': ['Metalable', 'Minimal (default)', 'Falspawn'],
            'Holds': ['Metalable', 'ITG (default)', 'Halloween Shadow'],
            'Lifts': ['Metalable - Hollowed Spectrum (default)'],
            'Mine Settings/Center Animation': ['On (default)'],
            'Mine Settings/Rotation': ['On - ITG (default)'],
            'Mine Settings/Size': ['Mini'],
            'Mines': ['ITG (default)', 'Unquantized (default)', 'lateM'],
            'Receptor Animation': ['On - Default (default)'],
            'Receptors': ['Metalable - Traditional (default)', 'Purple'],
            'Rolls': ['ITG (default)', 'DDR Hold Shadow'],
            'Tap Explosions': ['Metalable', 'Glow (default)', 'ITG (default)']
        },
    'Metalable - Kindled Suite': {
            'Arrow Center Animation': ['On - Default (default)'],
            'Arrows': ['Metalable (default)','ITG TD Over-Vibrant'],
            'Hold Explosions': ['Metalable','Glow','Gold'],
            'Holds': ['Metalable','ITG (default)','Fire'],
            'Lifts': ['Metalable - Hollowed Spectrum (default)'],
            'Mine Settings/Center Animation': ['On (default)'],
            'Mine Settings/Rotation': ['On - ITG (default)'],
            'Mine Settings/Size': ['Mini'],
            'Mines': ['ITG (default)','Unquantized (default)','Falspawn Vibrant'],
            'Receptor Animation': ['On - Default (default)'],
            'Receptors': ['Metalable - Traditional (default)','Halloween'],
            'Rolls': ['ITG (default)','Note Roll Shadow'],
            'Tap Explosions': ['Metalable','Spark','ITG']
        },
    'Metalable - Outlined Suite': {
            "Arrow Center Animation": ["On - Default (default)"],
            "Arrows": ["Metalable - Plain","Dev Toon"],
            "Hold Explosions": ["Metalable","Minimal (default)","Red"],
            "Holds": ["Metalable","Toon","Default"],
            "Lifts": ["Metalable - Hollowed Spectrum (default)"],
            "Mine Settings/Center Animation": ["On (default)"],
            "Mine Settings/Rotation": ["On - ITG (default)"],
            "Mine Settings/Size": ["Normal (default)"],
            "Mines": ["Toon","Purple"],
            "Receptor Animation": ["On - Default (default)"],
            "Receptors": ["Metalable - Frame","Blue"],
            "Rolls": ["Toon","Default"],
            "Tap Explosions": ["Metalable","Glow (default)","ITG (default)"]
        },
    'Metalable - Polished Suite': {
            "Arrow Center Animation": ["On - Default (default)"],
            "Arrows": ["Metalable (default)","Gemstones -REFLECTIVE- Vibrant"],
            "Hold Explosions": ["Metalable","Glow","Fire"],
            "Holds": ["Metalable","ITG (default)","Vapor"],
            "Lifts": ["Metalable - Hollowed Spectrum (default)"],
            "Mine Settings/Center Animation": ["On (default)"],
            "Mine Settings/Rotation": ["On - ITG (default)"],
            "Mine Settings/Size": ["Mini"],
            "Mines": ["ITG (default)","Unquantized (default)","Orange -REFLECTIVE- Vibrant"],
            "Receptor Animation": ["On - Default (default)"],
            "Receptors": ["Metalable - Frame","Christmas"],
            "Rolls": ["ITG (default)","Falspawn Shadow"],
            "Tap Explosions": ["Metalable","Spark","ITG"]
        },
    'Metalable - Reinforced Suite': {
            "Arrow Center Animation": ["On - Default (default)"],
            "Arrows": ["Metalable (default)","Bright Encore"],
            "Hold Explosions": ["Metalable","Minimal (default)","Ocean"],
            "Holds": ["Metalable","ITG (default)","Default Encore"],
            "Lifts": ["Metalable - Hollowed Spectrum (default)"],
            "Mine Settings/Center Animation": ["On (default)"],
            "Mine Settings/Rotation": ["On - ITG (default)"],
            "Mine Settings/Size": ["Normal (default)"],
            "Mines": ["ITG (default)","Unquantized (default)","Default P1 -REFLECTIVE-"],
            "Receptor Animation": ["On - Default (default)"],
            "Receptors": ["Metalable - Traditional (default)","White"],
            "Rolls": ["ITG (default)","Default Encore"],
            "Tap Explosions": ["Metalable","Glow (default)","ITG (default)"]
        },
    'Metalable - Sellable Suite': {
            "Arrow Center Animation": ["On - Default (default)"],
            "Arrows": ["Metalable (default)","Bright -FLATSHINE- Gold"],
            "Hold Explosions": ["Metalable","Glow","Yellow"],
            "Holds": ["Metalable","ITG (default)","Gold Shadow"],
            "Lifts": ["Metalable - Hollowed Spectrum (default)"],
            "Mine Settings/Center Animation": ["On (default)"],
            "Mine Settings/Rotation": ["On - ITG (default)"],
            "Mine Settings/Size": ["Mini"],
            "Mines": ["ITG (default)","Unquantized (default)","Default P1 -FLATSHINE- Gold"],
            "Receptor Animation": ["On - Default (default)"],
            "Receptors": ["Metalable - Traditional (default)","Gold"],
            "Rolls": ["ITG (default)","Gold"],
            "Tap Explosions": ["Metalable","Spark","Rainbowmatic"]
        }
}

def batch_update_page2_dropdowns():
    for category, selections in PLAYER_SELECTIONS.items():
        dropdowns = PAGE2_DROPDOWNS.get(category, [])

        for dropdown, selection in zip(dropdowns, selections):
            dropdown.set(selection)
            dropdown.event_generate("<<ComboboxSelected>>")

def randomize_page2_dropdowns():
    for category, dropdowns in PAGE2_DROPDOWNS.items():
        for dropdown in dropdowns:
            options = dropdown["values"]

            if options:
                dropdown.set(random.choice(options))
                dropdown.event_generate("<<ComboboxSelected>>")

def update_suite_preview(
    previews_path,
    suite_name,
    the_preview_label
):
    # Cancel previous animation
    if hasattr(the_preview_label, "_gif_after_id"):
        if the_preview_label._gif_after_id is not None:
            the_preview_label.after_cancel(the_preview_label._gif_after_id)

    the_preview_label._gif_after_id = None

    category_path = os.path.join(previews_path, "TEST SUITES")
    image_extensions = (".png", ".jpg", ".jpeg", ".bmp", ".gif")
    
    # category_path\suite_name .png/.gif/etc. or None
    image_path = next(
        (
            os.path.join(category_path, f"{suite_name}{ext}")
            for ext in image_extensions
            if os.path.isfile(os.path.join(category_path, f"{suite_name}{ext}"))
        ),
        None
    )

    if image_path is None:
        the_preview_label.configure(
            image="",
            text="No preview available"
        )
        the_preview_label.image = None
        return

    # Unique ID so an older load cannot overwrite a newer selection
    the_preview_label._load_id = getattr(the_preview_label, "_load_id", 0) + 1
    load_id = the_preview_label._load_id

    # Immediately display the first frame while the rest loads.
    try:
        with Image.open(image_path) as image:
            first_frame = image.copy()
            first_frame.thumbnail(
                (SUITE_PREVIEW_WIDTH, SUITE_PREVIEW_HEIGHT)
            )

        first_photo = ImageTk.PhotoImage(first_frame)

        the_preview_label.configure(image=first_photo, text="")
        the_preview_label.image = first_photo
        the_preview_label._gif_photos = [first_photo]
        the_preview_label._gif_index = 0

    except Exception as error:
        the_preview_label.configure(image="", text="Unable to load preview")
        the_preview_label.image = None
        print("Preview error:", image_path, error)
        return

    results = queue.Queue()

    def load_image():
        try:
            frames = []
            durations = []

            with Image.open(image_path) as image:
                for frame in ImageSequence.Iterator(image):
                    frame = frame.copy()
                    frame.thumbnail((SUITE_PREVIEW_WIDTH, SUITE_PREVIEW_HEIGHT))

                    frames.append(frame)
                    durations.append(
                        max(20, frame.info.get("duration", 100))
                    )

            results.put((load_id, frames, durations, None))

        except Exception as error:
            results.put((load_id, None, None, error))

    # Start background loading
    threading.Thread(target=load_image, daemon=True).start()

    def check_results():
        try:
            result_id, frames, durations, error = results.get_nowait()
        except queue.Empty:
            the_preview_label.after(50, check_results)
            return

        # Ignore results from an outdated selection
        if result_id != the_preview_label._load_id:
            return

        if error:
            the_preview_label.configure(image="", text="Unable to load preview")
            the_preview_label.image = None
            print("Preview error:", image_path, error)
            return

        photos = []

        # Create PhotoImages in small batches on Tkinter's main thread
        def create_photos(start=0):
            if load_id != the_preview_label._load_id:
                return

            end = min(start + 5, len(frames))

            for i in range(start, end):
                photos.append(ImageTk.PhotoImage(frames[i]))

            if end < len(frames):
                the_preview_label.after(1, lambda: create_photos(end))
            else:
                the_preview_label._gif_photos = photos
                the_preview_label._gif_durations = durations
                the_preview_label._gif_index = 0

                the_preview_label.configure(image=photos[0], text="")
                the_preview_label.image = photos[0]

                if len(photos) > 1:
                    animate_gif()

        def animate_gif():
            if load_id != the_preview_label._load_id:
                return

            the_preview_label._gif_index = (
                the_preview_label._gif_index + 1
            ) % len(photos)

            index = the_preview_label._gif_index
            the_preview_label.configure(image=photos[index])
            the_preview_label.image = photos[index]

            the_preview_label._gif_after_id = the_preview_label.after(
                durations[index], animate_gif
            )

        if frames:
            create_photos()
        else:
            the_preview_label.configure(image="", text="No preview available")
            the_preview_label.image = None

    check_results()


# ---ACTUAL ELEMENTS ON PAGE3---

# Back button
tk.Button(
    page3,
    text="BACK to Noteskin Customization",
    command=lambda: show_page(page2),
).pack(anchor="w", pady=10)

# Scrollable container
page3_scroll_area = tk.Frame(page3)
page3_scroll_area.pack(fill="both", expand=True)

page3_canvas = tk.Canvas(page3_scroll_area)
page3_scrollbar = tk.Scrollbar(
    page3_scroll_area,
    orient="vertical",
    command=page3_canvas.yview
)

page3_canvas.configure(yscrollcommand=page3_scrollbar.set)

page3_scrollbar.pack(side="right", fill="y")
page3_canvas.pack(side="left", fill="both", expand=True)

# Container for all scrollable widgets
page3_container = tk.Frame(page3_canvas)

page3_canvas_window = page3_canvas.create_window(
    (0, 0),
    window=page3_container,
    anchor="nw"
)

# Update the scrollable area when widgets are added or resized
page3_container.bind(
    "<Configure>",
    lambda event: page3_canvas.configure(
        scrollregion=page3_canvas.bbox("all")
    )
)

# Keep the inner frame the same width as the canvas
page3_canvas.bind(
    "<Configure>",
    lambda event: page3_canvas.itemconfigure(
        page3_canvas_window,
        width=event.width
    )
)

# Windows / macOS
page3_canvas.bind_all("<MouseWheel>", on_mousewheel)

# Linux (X11)
page3_canvas.bind_all("<Button-4>", on_mousewheel)
page3_canvas.bind_all("<Button-5>", on_mousewheel)

# --- BASE SUITES
base_suite_frame = tk.Frame(page3_container)
base_suite_frame.pack(fill="x", padx=10, pady=(5, 8))

tk.Label(
    base_suite_frame,
    text='BASE SUITES',
    font=("Arial", 11, "bold")
).pack(anchor="w",pady=(0,5))

base_dropdown = ttk.Combobox(
    base_suite_frame,
    width=30,
    state="readonly",
    values=list(BASE_SUITE_CONFIG.keys())
)
for event in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
    base_dropdown.bind(event, on_mousewheel)
base_dropdown.bind(
    "<<ComboboxSelected>>",
    lambda event: update_suite_preview(
        os.path.join(root_path, "Previews"),
        base_dropdown.get(),
        base_preview_label
    )
)

base_previous_button = tk.Button(
    base_suite_frame,
    text="<",
    width=1,
    command=lambda d=base_dropdown:
        cycle_dropdown(d, -1)
)

base_next_button = tk.Button(
    base_suite_frame,
    text=">",
    width=1,
    command=lambda d=base_dropdown:
        cycle_dropdown(d, 1)
)

def load_base_suite():
    answer = messagebox.askyesno(
        "Confirm Settings",
        "This will OVERWRITE all current customizations with those of this SUITE.\nContinue?"
    )

    if not answer:
        return
    
    global PLAYER_SELECTIONS

    PLAYER_SELECTIONS = copy.deepcopy(
            BASE_SUITE_CONFIG[base_dropdown.get()]
        )
    batch_update_page2_dropdowns()

base_set = tk.Button(
    base_suite_frame,
    text="Use this SUITE",
    command=load_base_suite
)

base_previous_button.pack(side="left")
base_dropdown.pack(side="left", padx=2)
base_next_button.pack(side="left")
base_set.pack(side="left", padx=10)

base_preview_label = tk.Label(
    page3_container,
    text="No preview available",
    anchor="w"
)
base_preview_label.pack(anchor="w", pady=(5, 10))

base_dropdown.current(0)
update_suite_preview(
    os.path.join(root_path, "Previews"),
    base_dropdown.get(),
    base_preview_label
)


# --- TEST SUITES
test_suite_frame = tk.Frame(page3_container)
test_suite_frame.pack(fill="x", padx=10, pady=(5, 8))

tk.Label(
    test_suite_frame,
    text='TEST SUITES',
    font=("Arial", 11, "bold")
).pack(anchor="w",pady=(0,5))

test_dropdown = ttk.Combobox(
    test_suite_frame,
    width=30,
    state="readonly",
    values=list(TEST_SUITE_CONFIG.keys())
)
for event in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
    test_dropdown.bind(event, on_mousewheel)
test_dropdown.bind(
    "<<ComboboxSelected>>",
    lambda event: update_suite_preview(
        os.path.join(root_path, "Previews"),
        test_dropdown.get(),
        test_preview_label
    )
)

test_previous_button = tk.Button(
    test_suite_frame,
    text="<",
    width=1,
    command=lambda d=test_dropdown:
        cycle_dropdown(d, -1)
)

test_next_button = tk.Button(
    test_suite_frame,
    text=">",
    width=1,
    command=lambda d=test_dropdown:
        cycle_dropdown(d, 1)
)

def load_test_suite():
    answer = messagebox.askyesno(
        "Confirm Settings",
        "This will OVERWRITE all current customizations with those of this SUITE.\nContinue?"
    )

    if not answer:
        return
    
    global PLAYER_SELECTIONS

    PLAYER_SELECTIONS = copy.deepcopy(
        TEST_SUITE_CONFIG[test_dropdown.get()]
    )
    batch_update_page2_dropdowns()

test_set = tk.Button(
    test_suite_frame,
    text="Use this SUITE",
    command=load_test_suite
)

test_previous_button.pack(side="left")
test_dropdown.pack(side="left", padx=2)
test_next_button.pack(side="left")
test_set.pack(side="left", padx=10)

test_preview_label = tk.Label(
    page3_container,
    text="No preview available",
    anchor="w"
)
test_preview_label.pack(anchor="w", pady=(5, 10))

test_dropdown.current(0)
update_suite_preview(
    os.path.join(root_path, "Previews"),
    test_dropdown.get(),
    test_preview_label
)


# --- CUSTOM SUITES
custom_suite_frame = tk.Frame(page3_container)
custom_suite_frame.pack(fill="x", padx=10, pady=(5, 8))

tk.Label(
    custom_suite_frame,
    text='CUSTOM SUITES',
    font=("Arial", 11, "bold")
).pack(anchor="w",pady=(0,5))

custom_dropdown = ttk.Combobox(
    custom_suite_frame,
    width=30,
    state="readonly"
)
for event in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
    custom_dropdown.bind(event, on_mousewheel)

def refresh_saved_selection_names():
    names = list(read_saved_selections().keys())
    custom_dropdown["values"] = names

    if names:
        if custom_dropdown.get() not in names:
            custom_dropdown.current(0)
    else:
        custom_dropdown.set("")

custom_previous_button = tk.Button(
    custom_suite_frame,
    text="<",
    width=1,
    command=lambda d=custom_dropdown:
        cycle_dropdown(d, -1)
)

custom_next_button = tk.Button(
    custom_suite_frame,
    text=">",
    width=1,
    command=lambda d=custom_dropdown:
        cycle_dropdown(d, 1)
)

def load_custom_suite():
    suite_name = custom_dropdown.get()

    if not suite_name:
        messagebox.showwarning(
            "Warning",
            "There are no custom SUITES to load."
        )
        return

    answer = messagebox.askyesno(
        "Confirm Settings",
        "This will OVERWRITE all current customizations with those of this SUITE.\nContinue?"
    )

    if not answer:
        return

    global PLAYER_SELECTIONS

    saved_suites = read_saved_selections()

    if suite_name not in saved_suites:
        messagebox.showerror(
            "Error",
            "This SUITE no longer exists. Refreshing the list."
        )
        refresh_saved_selection_names()
        return

    PLAYER_SELECTIONS = copy.deepcopy(saved_suites[suite_name])
    batch_update_page2_dropdowns()

custom_set = tk.Button(
    custom_suite_frame,
    text="Use this SUITE",
    command=load_custom_suite
)

custom_previous_button.pack(side="left")
custom_dropdown.pack(side="left", padx=2)
custom_next_button.pack(side="left")
custom_set.pack(side="left", padx=10)

tk.Label(
    page3_container,
    text="No preview available",
    anchor="w"
).pack(anchor="w", pady=(5, 0))

refresh_saved_selection_names()


# --- THE NEFARIOUS RANDOMIZER
random_suite_frame = tk.Frame(page3_container)
random_suite_frame.pack(fill="x", padx=10, pady=(5, 8))

tk.Label(
    random_suite_frame,
    text='THE NEFARIOUS RANDOMIZER',
    font=("Arial", 11, "bold")
).pack(anchor="w",pady=(0,5))

def load_random_suite():

    answer = messagebox.askyesno(
        "Confirm Settings",
        "This will OVERWRITE all current customizations with those of this SUITE.\nContinue?"
    )

    if not answer:
        return

    randomize_page2_dropdowns()

random_set = tk.Button(
    random_suite_frame,
    text="Generate and Use a RANDOM SUITE",
    command=load_random_suite
)

random_set.pack(side="left", padx=10)

tk.Label(
    page3_container,
    text="No preview available",
    anchor="w"
).pack(anchor="w", pady=(5, 15))


root.mainloop()