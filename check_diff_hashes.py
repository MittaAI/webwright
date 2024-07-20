import hashlib
import os

def calculate_file_hash(file_path):
    hash_function = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            hash_function.update(chunk)
    return hash_function.hexdigest()

def check_diff_hashes(file_path):
    # Calculate the current file hash
    current_hash = calculate_file_hash(file_path)
    if not current_hash:
        return "Failed to calculate file hash."

    print(f"Current file hash: {current_hash}")

    # Search for the corresponding diff files
    diff_dir = os.path.expanduser('~/.webwright/diffs')
    file_name = os.path.basename(file_path)
    matching_diffs = []

    for diff in os.listdir(diff_dir):
        if diff.startswith(file_name):
            try:
                _, timestamp, original_hash = diff[:-5].rsplit('_', 2)
                if original_hash == current_hash:
                    matching_diffs.append((diff, timestamp))
            except ValueError:
                continue

    if not matching_diffs:
        return f"No matching diff file for {file_path} found."

    matching_diffs.sort(key=lambda x: x[1], reverse=True)
    return f"Matching diffs: {[file for file, _ in matching_diffs]}"

if __name__ == "__main__":
    file_path = "lib/functions/clear_screen.py"
    result = check_diff_hashes(file_path)
    print(result)
