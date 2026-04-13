#!/usr/bin/env python3

# --- IMPORTS ---

import subprocess
import datetime
import sys


# --- MISC ---

# Time formatting guide: https://devhints.io/strftime
timestamp_format = "%Y-%m-%d, %H:%M:%S"


# --- LAYOUT CONFIG ---

# Add or remove keyboard layouts here
LAYOUTS = [
    "qwertyuiop[]asdfghjkl;'zxcvbnm,./QWERTYUIOP{}ASDFGHJKL:\"ZXCVBNM<>?", # 0: EN
    "йцукенгшщзхїфівапролджєячсмитьбю.ЙЦУКЕНГШЩЗХЇФІВАПРОЛДЖЄЯЧСМИТЬБЮ,",  # 1: UA
    "йцукенгшщзхъфывапролджэячсмитьбю.ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ,"   # 2: RU
]

# Rules for switching layouts (RU -> UA <-> EN by default)
TRANSITIONS = {
    1: 0, # UA -> EN
    2: 1, # RU -> UA
    0: 1  # EN -> UA
}

# Pre-map each character to its containing layout indices for O(1) lookup
CHAR_TO_LAYOUTS = {}
for idx, layout in enumerate(LAYOUTS):
    for char in layout:
        if char not in CHAR_TO_LAYOUTS:
            CHAR_TO_LAYOUTS[char] = []
        CHAR_TO_LAYOUTS[char].append(idx)


# --- HELPERS ---

def notify(title: str, msg: str) -> None:
    """Show popup message"""
    subprocess.run(["notify-send", "-a", str(title), "-t", "1500", str(msg)])

def switch_layout(text: str) -> str:
    """Converts text across multiple layouts, preserving mixed-text swapping."""
    if not text: return text

    # 1. Pre-load layouts for each character
    char_layouts = [CHAR_TO_LAYOUTS.get(char, []) for char in text]

    # 2. Search base text layout
    first_idx = next((l[0] for l in char_layouts if len(l) == 1), None)
    if first_idx is None:
        first_idx = next((l[0] for l in char_layouts if l), None)
        
    if first_idx is None: return text

    # 3. Setup transition rules
    target_idx = TRANSITIONS.get(first_idx, 0)
    swap_pair = {first_idx: target_idx, target_idx: first_idx}
    
    current_idx = first_idx
    result = []

    # 4. Conversion
    for char, layouts in zip(text, char_layouts):
        if not layouts:
            result.append(char)
            continue

        # Update layout context
        if current_idx not in layouts:
            if first_idx in layouts:
                current_idx = first_idx
            elif target_idx in layouts:
                current_idx = target_idx
            else:
                current_idx = layouts[0]

        char_target = swap_pair.get(current_idx, TRANSITIONS.get(current_idx, 0))
        char_pos = LAYOUTS[current_idx].index(char)
        
        if char_pos < len(LAYOUTS[char_target]):
            result.append(LAYOUTS[char_target][char_pos])
        else:
            result.append(char)

    return "".join(result)


# --- MAIN ---

def main() -> None:
    # Check CLI args
    use_timestamp: bool = "-t" in sys.argv or "--timestamp" in sys.argv

    if use_timestamp:
        # Add a timestamp to the clipboard
        timestamp: str = datetime.datetime.now().strftime(timestamp_format)
        subprocess.run(['/usr/bin/wl-copy'], input=timestamp.encode('utf-8'), check=True)
        notify("Switcher: New Timestamp Added", timestamp)
        return

    # Convert selected text otherwise
    try:
        # Get selected text (primary clipboard, without newline)
        result = subprocess.run(['/usr/bin/wl-paste', '-p', '-n'], capture_output=True, text=True, check=True)
        selected: str = result.stdout
        
        if not selected: sys.exit(0)

        # Convert keyboard layout
        converted: str = switch_layout(selected)

        if converted != selected:
            # Paste to the clipboard and notify
            subprocess.run(['/usr/bin/wl-copy'], input=converted.encode('utf-8'), check=True)
            
            # Show a short preview in the notification
            preview = converted if len(converted) <= 30 else converted[:27] + "..."
            notify("Switcher: Text Converted", preview)

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
