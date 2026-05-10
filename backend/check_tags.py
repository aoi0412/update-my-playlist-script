import sys
import mutagen
from mutagen.id3 import ID3

def check_tags(file_path):
    try:
        audio = ID3(file_path)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return

    print(f"\n--- Tag info for {file_path} ---")
    print(f"ID3 Version: 2.{audio.version[0]}.{audio.version[1]}")
    
    if "TPE1" in audio:
        tpe1 = audio["TPE1"]
        print(f"\n[Artist (TPE1)]")
        print(f"Type: {type(tpe1)}")
        print(f"Raw Text: {tpe1.text}")
        print(f"Number of artists recognized: {len(tpe1.text)}")
        for i, artist in enumerate(tpe1.text):
            print(f"  Artist {i+1}: {artist}")
    else:
        print("\nNo TPE1 (Artist) tag found.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_tags.py <path_to_mp3_file>")
    else:
        check_tags(sys.argv[1])
