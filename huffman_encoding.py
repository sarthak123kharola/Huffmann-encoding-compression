import heapq
import pickle
import os
from collections import defaultdict

# --- Huffman Encoding Implementation ---

class HuffmanNode:
    def __init__(self, char, freq):
        self.char = char      # character or None (for internal nodes)
        self.freq = freq      # frequency count
        self.left = None      # left child
        self.right = None     # right child

    # This method is required for the priority queue (heapq) to compare nodes.
    def __lt__(self, other):
        return self.freq < other.freq

def build_frequency_table(data):
    frequency = defaultdict(int)
    for char in data:
        frequency[char] += 1
    return frequency

def build_huffman_tree(frequency):
    heap = [HuffmanNode(char, freq) for char, freq in frequency.items()]
    heapq.heapify(heap)
    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        merged = HuffmanNode(None, left.freq + right.freq)
        merged.left = left
        merged.right = right
        heapq.heappush(heap, merged)
    return heap[0]

def build_codes_table(root):
    codes = {}
    def generate_codes(node, current_code):
        if node is None:
            return
        if node.char is not None:  # Leaf node
            codes[node.char] = current_code
            return
        generate_codes(node.left, current_code + "0")
        generate_codes(node.right, current_code + "1")
    generate_codes(root, "")
    return codes

def huffman_encoding(data):
    if not data:
        return "", None
    frequency = build_frequency_table(data)
    root = build_huffman_tree(frequency)
    codes = build_codes_table(root)
    encoded_data = "".join(codes[char] for char in data)
    return encoded_data, root

def huffman_decoding(encoded_data, root):
    if not encoded_data or root is None:
        return ""
    decoded_chars = []
    current_node = root
    for bit in encoded_data:
        current_node = current_node.left if bit == "0" else current_node.right
        if current_node.char is not None:
            decoded_chars.append(current_node.char)
            current_node = root
    return "".join(decoded_chars)

# --- Folder Compression/Decompression Functions ---

def compress_folder(input_folder, output_file, tree_file):
    """
    Reads all text files in the folder (recursively), concatenates their content with a '\0' separator,
    and builds a file index mapping each file's original path to its starting index in the concatenated data.
    The Huffman-encoded data and the tree (with index and original folder path) are saved using pickle.
    """
    data = ""
    file_index = {}  # Maps each file's full path to its starting index in the data string

    for root_dir, _, files in os.walk(input_folder):
        for file in files:
            file_path = os.path.join(root_dir, file)
            try:
                with open(file_path, "rb") as f:
                    # Decode file as UTF-8; ignore errors if not valid text.
                    content = f.read().decode("utf-8", errors="ignore")
                file_index[file_path] = len(data)
                data += content + "\0"  # Using null character as separator
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")

    encoded_data, root = huffman_encoding(data)
    if root is None:
        print("No data to compress.")
        return

    # Ensure the directories for output exist
    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        os.makedirs(os.path.dirname(tree_file), exist_ok=True)
    except Exception as e:
        print(f"Error creating directories: {e}")
        return

    try:
        with open(output_file, "wb") as f:
            pickle.dump(encoded_data, f)
    except Exception as e:
        print(f"Error writing compressed file: {e}")

    try:
        # Save the Huffman tree, file index, and the original folder path for later reconstruction.
        with open(tree_file, "wb") as f:
            pickle.dump((root, file_index, input_folder), f)
    except Exception as e:
        print(f"Error writing tree file: {e}")

    print("Compression complete.")

def decompress_folder(input_file, output_folder, tree_file):
    """
    Loads the Huffman encoded data and tree from files, decodes the data, and reconstructs
    the original folder structure with the files.
    """
    try:
        with open(input_file, "rb") as f:
            encoded_data = pickle.load(f)
    except Exception as e:
        print(f"Error reading compressed file: {e}")
        return

    try:
        with open(tree_file, "rb") as f:
            root, file_index, original_folder = pickle.load(f)
    except Exception as e:
        print(f"Error reading tree file: {e}")
        return

    decoded_data = huffman_decoding(encoded_data, root)

    for file_path, index in file_index.items():
        # Retrieve file content by splitting at the first '\0'
        file_content = decoded_data[index:].split("\0", 1)[0]
        # Compute the relative path of the file with respect to the original folder.
        relative_path = os.path.relpath(file_path, original_folder)
        output_path = os.path.join(output_folder, relative_path)
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(file_content)
        except Exception as e:
            print(f"Error writing decompressed file {output_path}: {e}")

    print("Decompression complete.")

# --- Main Program ---

if __name__ == "__main__":
    # Use double backslashes in the prompt examples to avoid escape sequence issues.
    choice = input("Choose an option: Compress (C) or Decompress (D): ").strip().upper()

    if choice == "C":
        input_path = input("Enter the path of the folder to compress: ")
        output_path = input("Enter the path to save the compressed file (e.g., D:\\output\\compressed_file.huff): ")
        tree_path = input("Enter the path to save the tree file (e.g., D:\\output\\tree_file.pkl): ")
        compress_folder(input_path, output_path, tree_path)
    elif choice == "D":
        input_file = input("Enter the path of the file to decompress: ")
        output_folder = input("Enter the path to save the decompressed folder: ")
        tree_path = input("Enter the path of the tree file used during compression: ")
        decompress_folder(input_file, output_folder, tree_path)
    else:
        print("Invalid choice. Please choose C or D.")
