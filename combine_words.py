#!/usr/bin/env python3
"""
Script to combine two word CSV files while removing duplicates.
"""

def combine_word_files(file1, file2, output_file):
    """
    Combine two word CSV files and remove duplicates.
    
    Args:
        file1 (str): Path to first CSV file
        file2 (str): Path to second CSV file  
        output_file (str): Path to output combined CSV file
    """
    # Set to store unique words
    unique_words = set()
    
    # Read words from first file
    print(f"Reading words from {file1}...")
    try:
        with open(file1, 'r', encoding='utf-8') as f:
            for line in f:
                word = line.strip().lower()  # Convert to lowercase for consistency
                if word:  # Skip empty lines
                    unique_words.add(word)
        print(f"Added {len(unique_words)} words from {file1}")
    except FileNotFoundError:
        print(f"Error: File {file1} not found!")
        return
    except Exception as e:
        print(f"Error reading {file1}: {e}")
        return
    
    # Read words from second file
    print(f"Reading words from {file2}...")
    initial_count = len(unique_words)
    try:
        with open(file2, 'r', encoding='utf-8') as f:
            for line in f:
                word = line.strip().lower()  # Convert to lowercase for consistency
                if word:  # Skip empty lines
                    unique_words.add(word)
        new_words = len(unique_words) - initial_count
        print(f"Added {new_words} new words from {file2}")
    except FileNotFoundError:
        print(f"Error: File {file2} not found!")
        return
    except Exception as e:
        print(f"Error reading {file2}: {e}")
        return
    
    # Sort words alphabetically
    sorted_words = sorted(unique_words)
    
    # Write combined words to output file
    print(f"Writing {len(sorted_words)} unique words to {output_file}...")
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for word in sorted_words:
                f.write(word + '\n')
        print(f"Successfully created {output_file}")
        print(f"Total unique words: {len(sorted_words)}")
    except Exception as e:
        print(f"Error writing to {output_file}: {e}")
        return

def main():
    """Main function to run the word combination script."""
    file1 = "words_new.csv"
    file2 = "WORDS.csv"
    output_file = "combined_words.csv"
    
    print("Word CSV Combiner")
    print("=" * 50)
    
    combine_word_files(file1, file2, output_file)
    
    print("\nDone!")

if __name__ == "__main__":
    main() 