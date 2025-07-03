#!/usr/bin/env python3
"""
Enhanced AI Wordle Solver with Constraint-Based Logic
=====================================================

This solver uses a constraint-based approach that is robust against unknown words
in the target dictionary. It can generate valid guesses even when the correct answer
is not in the word list.

Key Features:
- Constraint-based letter filtering
- Dynamic word generation as failsafe
- Robust duplicate letter handling
- Comprehensive performance testing
"""

import requests
import csv
from typing import Set, List, Dict, Any, Tuple
import random
import time
from collections import defaultdict


def load_word_list(filename: str = "combined_words.csv") -> Set[str]:
    """
    Load 5-letter words from text file.
    
    Args:
        filename: Path to the file containing words (one word per line)
        
    Returns:
        Set of 5-letter words in uppercase
    """
    words = set()
    
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            for line in file:
                word = line.strip().upper()  # Remove whitespace and convert to uppercase
                if len(word) == 5 and word.isalpha():  # Validate 5-letter alphabetic word
                    words.add(word)
    
    except FileNotFoundError:
        print(f"Error: Could not find file {filename}")
        print("Make sure WORDS.csv is in the same directory as this script")
        return set()
    except Exception as e:
        print(f"Error loading word list: {e}")
        return set()
    
    print(f"Loaded {len(words)} words from {filename}")
    return words


def get_feedback(guess: str, seed: int, base_url: str = "https://wordle.votee.dev:8000") -> List[Dict[str, Any]]:
    """
    Submit a guess to the Wordle API and get feedback.
    
    Args:
        guess: 5-letter word guess
        seed: Random seed for consistent game
        base_url: Base URL for the API
        
    Returns:
        List of GuessResult objects with feedback for each letter
    """
    try:
        # Construct the URL for the /random endpoint
        url = f"{base_url}/random"
        
        # Set up parameters
        params = {
            'guess': guess.upper(),
            'seed': seed,
            'size': 5
        }
        
        # Make the API request
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Return the JSON response
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []


class WordleSolver:
    """
    AI solver for Wordle puzzle game using constraint-based letter filtering.
    This approach is robust against unknown words in the target dictionary.
    """
    
    def __init__(self, all_words: Set[str]):
        """
        Initialize the solver with a set of all possible words.
        
        Args:
            all_words: Set of all valid 5-letter words (used for strategic guessing)
        """
        self.all_words = all_words.copy()
        self.guess_count = 0
        self.guesses_made = []
        
        # Constraint-based approach: track what's possible for each position
        self.slot_possibilities = [set('ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(5)]
        self.must_include_letters = set()  # Letters that must be in the word somewhere
        self.absent_letters = set()        # Letters that are definitely not in the word
        self.confirmed_positions = {}      # slot -> letter for confirmed positions
        
    def get_next_guess(self) -> str:
        """
        Get the next word to guess using constraint-based logic.
        
        Returns:
            Next word to guess
        """
        if self.guess_count == 0:
            # First guess: use a word with high vowel count and common letters
            first_guess = "RAISE"  # R, A, I, S, E are common letters with good vowel coverage
            return first_guess
        
        # Filter our word list based on current constraints
        valid_words = self._filter_words_by_constraints()
        
        if valid_words:
            # Strategy: Pick the word that uses the most uncommon letters we haven't tried yet
            # For now, just pick the first valid word (can be enhanced later)
            return next(iter(valid_words))
        else:
            # Fallback: Generate a word that satisfies our constraints
            # This is the key innovation - we don't give up when our word list is exhausted
            print("🔧 No words in dictionary match constraints. Generating failsafe guess...")
            return self._generate_constraint_satisfying_word()
    
    def _filter_words_by_constraints(self) -> Set[str]:
        """
        Filter the word list based on current constraints.
        
        Returns:
            Set of words that satisfy all current constraints
        """
        valid_words = set()
        
        for word in self.all_words:
            if self._word_satisfies_constraints(word):
                valid_words.add(word)
        
        return valid_words
    
    def _word_satisfies_constraints(self, word: str) -> bool:
        """
        Check if a word satisfies all current constraints.
        
        Args:
            word: Word to check
            
        Returns:
            True if word satisfies all constraints
        """
        word = word.upper()
        
        # Check confirmed positions
        for slot, letter in self.confirmed_positions.items():
            if word[slot] != letter:
                return False
        
        # Check slot possibilities
        for slot, letter in enumerate(word):
            if letter not in self.slot_possibilities[slot]:
                return False
        
        # Check that all required letters are present
        for letter in self.must_include_letters:
            if letter not in word:
                return False
        
        # Check that no absent letters are present
        for letter in self.absent_letters:
            if letter in word:
                return False
        
        return True
    
    def _generate_constraint_satisfying_word(self) -> str:
        """
        Generate a word that satisfies all current constraints.
        This is our failsafe when no dictionary words work.
        
        Returns:
            A 5-letter word that satisfies constraints
        """
        word = [''] * 5
        
        # First, fill in confirmed positions
        for slot, letter in self.confirmed_positions.items():
            word[slot] = letter
        
        # Then, place required letters that don't have confirmed positions
        unplaced_required = self.must_include_letters - set(self.confirmed_positions.values())
        
        for letter in unplaced_required:
            # Find a slot where this letter can go
            for slot in range(5):
                if word[slot] == '' and letter in self.slot_possibilities[slot]:
                    word[slot] = letter
                    break
        
        # Fill remaining slots with valid letters
        for slot in range(5):
            if word[slot] == '':
                # Choose the first valid letter for this slot
                available_letters = (self.slot_possibilities[slot] - 
                                   self.absent_letters - 
                                   set(word))  # Avoid duplicates
                if available_letters:
                    word[slot] = next(iter(available_letters))
                else:
                    # Last resort: use any letter that's possible for this slot
                    word[slot] = next(iter(self.slot_possibilities[slot]))
        
        return ''.join(word)
    
    def update_constraints(self, guess: str, feedback: List[Dict[str, Any]]):
        """
        Update constraints based on feedback from a guess.
        
        Args:
            guess: The word that was guessed
            feedback: List of feedback objects from the API
        """
        guess = guess.upper()
        self.guess_count += 1
        self.guesses_made.append(guess)
        
        # Track letters by their feedback in this guess
        correct_letters = {}    # slot -> letter
        present_letters = {}    # slot -> letter (letter is in word but wrong position)
        absent_letters = set()  # letters not in word
        
        # First pass: categorize feedback
        for result in feedback:
            slot = result['slot']
            letter = result['guess'].upper()
            status = result['result']
            
            if status == 'correct':
                correct_letters[slot] = letter
            elif status == 'present':
                present_letters[slot] = letter
            elif status == 'absent':
                absent_letters.add(letter)
        
        # Second pass: update constraints carefully
        # Handle correct positions
        for slot, letter in correct_letters.items():
            self.confirmed_positions[slot] = letter
            self.slot_possibilities[slot] = {letter}  # Only this letter is possible
            self.must_include_letters.add(letter)
        
        # Handle present letters (in word but wrong position)
        for slot, letter in present_letters.items():
            self.must_include_letters.add(letter)
            self.slot_possibilities[slot].discard(letter)  # Not in this position
        
        # Handle absent letters (tricky with duplicates)
        for letter in absent_letters:
            # Only mark as truly absent if it's not also correct or present
            if (letter not in correct_letters.values() and 
                letter not in present_letters.values()):
                self.absent_letters.add(letter)
                # Remove from all slot possibilities
                for slot in range(5):
                    self.slot_possibilities[slot].discard(letter)
    
    # Keep the old method name for compatibility
    def update_possible_words(self, guess: str, feedback: List[Dict[str, Any]]):
        """Compatibility wrapper for the old method name."""
        self.update_constraints(guess, feedback)
    
    @property
    def possible_words(self) -> Set[str]:
        """Compatibility property - returns words that match constraints."""
        return self._filter_words_by_constraints()


def play_wordle_game(seed: int = None, max_attempts: int = None, verbose: bool = True) -> Tuple[bool, int, str]:
    """
    Play a complete Wordle game using the AI solver.
    
    Args:
        seed: Random seed for the game (if None, will use a random seed)
        max_attempts: Maximum number of guesses allowed (if None, runs until completion)
        verbose: Whether to print detailed output
        
    Returns:
        Tuple of (success, attempts_used, final_word)
    """
    # Configuration
    base_url = "https://wordle.votee.dev:8000"
    
    # Use random seed if not provided
    if seed is None:
        seed = random.randint(1, 100000)
    
    if verbose:
        print(f"🎮 Starting Wordle Game with seed: {seed}")
        print("=" * 50)
    
    # Load word list and create solver
    words = load_word_list()
    if not words:
        if verbose:
            print("❌ Failed to load word list!")
        return False, 0, ""
    
    solver = WordleSolver(words)
    
    # Game loop - run until we win or can't generate valid guesses
    attempt = 0
    while True:
        attempt += 1
        
        # Safety check to prevent infinite loops
        if max_attempts and attempt > max_attempts:
            if verbose:
                print(f"\n😞 Game Over! Failed to solve in {max_attempts} attempts.")
            break
        
        # Additional safety: if we've tried too many times, something is wrong
        if attempt > 50:  # Reasonable upper bound
            if verbose:
                print(f"\n🚨 Safety limit reached at {attempt} attempts. Stopping.")
            break
        
        if verbose:
            max_display = f"/{max_attempts}" if max_attempts else ""
            print(f"\n🔄 Attempt {attempt}{max_display}")
        
        # Get next guess from solver
        try:
            guess = solver.get_next_guess()
        except Exception as e:
            if verbose:
                print(f"❌ Error generating guess: {e}")
            break
        
        if verbose:
            print(f"🤖 AI Guess: {guess}")
        
        # Submit guess to API
        feedback = get_feedback(guess, seed, base_url)
        
        if not feedback:
            if verbose:
                print("❌ Failed to get feedback from API!")
            return False, attempt, guess
        
        # Display feedback
        if verbose:
            print("📋 Feedback:")
            for result in feedback:
                slot = result['slot']
                letter = result['guess'].upper()
                status = result['result']
                
                # Choose emoji based on status
                if status == 'correct':
                    emoji = "🟢"
                elif status == 'present':
                    emoji = "🟡"
                else:  # absent
                    emoji = "⚫"
                
                print(f"  Position {slot}: '{letter}' {emoji} ({status})")
        
        # Check if we won
        all_correct = all(result['result'] == 'correct' for result in feedback)
        if all_correct:
            if verbose:
                print(f"\n🎉 SUCCESS! Won in {attempt} attempts!")
                print(f"🏆 The word was: {guess}")
            return True, attempt, guess
        
        # Update solver with feedback for next iteration
        solver.update_possible_words(guess, feedback)
        
        # Check if we have possible words left
        valid_words = solver.possible_words
        if verbose:
            print(f"After guess '{guess}': {len(valid_words)} dictionary words match constraints")
            if len(valid_words) <= 10 and len(valid_words) > 0:
                print(f"Matching words: {sorted(list(valid_words))}")
    
    if verbose:
        print(f"\n😞 Game Over! Failed to solve in {attempt} attempts.")
        valid_words = solver.possible_words
        print(f"🤔 Remaining possibilities: {len(valid_words)}")
        if valid_words and len(valid_words) <= 5:
            print(f"🔍 Remaining words: {sorted(list(valid_words))}")
    
    return False, attempt, ""


def append_word_to_dataset(word: str, filename: str = "WORDS.csv") -> bool:
    """
    Append a new word to the word dataset if it's not already there.
    
    Args:
        word: The word to add
        filename: The dataset file to append to
        
    Returns:
        True if word was added, False if it already existed or error occurred
    """
    word = word.upper().strip()
    
    # Validate the word
    if len(word) != 5 or not word.isalpha():
        return False
    
    try:
        # Check if word already exists in file
        existing_words = set()
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                for line in file:
                    existing_word = line.strip().upper()
                    if len(existing_word) == 5 and existing_word.isalpha():
                        existing_words.add(existing_word)
        except FileNotFoundError:
            # File doesn't exist yet, that's okay
            pass
        
        # Add word if it's not already there
        if word not in existing_words:
            with open(filename, 'a', encoding='utf-8') as file:
                file.write(f"{word}\n")
            print(f"📝 Added new word to dataset: {word}")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ Error adding word to dataset: {e}")
        return False


def run_performance_test(num_games: int = 20, verbose: bool = True, debug_failures: bool = True, 
                        learn_threshold: int = 8) -> Dict[str, Any]:
    """
    Run multiple games to test the solver's performance.
    
    Args:
        num_games: Number of games to run
        verbose: Whether to print detailed output for each game
        debug_failures: Whether to run detailed debugging on failed seeds
        learn_threshold: If a word takes more than this many attempts, add it to dataset
        
    Returns:
        Dictionary with performance statistics
    """
    results = {
        'games_won': 0,
        'games_lost': 0,
        'total_attempts': 0,
        'attempt_distribution': defaultdict(int),  # Use defaultdict to handle any number of attempts
        'seeds_used': [],
        'winning_words': [],
        'failed_seeds': [],
        'learned_words': []  # Track words we added to the dataset
    }
    
    print(f"🎯 Running {num_games} games to test solver performance...")
    print(f"🧠 Learning threshold: Words taking >{learn_threshold} attempts will be added to dataset")
    print("=" * 60)
    
    start_time = time.time()
    
    for game_num in range(1, num_games + 1):
        seed = random.randint(1, 100000)
        results['seeds_used'].append(seed)
        
        if verbose:
            print(f"\n🎮 Game {game_num}/{num_games} (Seed: {seed})")
            print("-" * 30)
        
        # Run game
        success, attempts_used, final_word = play_wordle_game(seed=seed, verbose=verbose)
        
        results['total_attempts'] += attempts_used
        
        if success:
            results['games_won'] += 1
            results['attempt_distribution'][attempts_used] += 1
            results['winning_words'].append(final_word)
            
            # Check if we should learn this word
            if attempts_used > learn_threshold:
                if append_word_to_dataset(final_word):
                    results['learned_words'].append(final_word)
                    print(f"🧠 Learned new word: {final_word} (took {attempts_used} attempts)")
            
            if verbose:
                print(f"✅ Won in {attempts_used} attempts! Word: {final_word}")
        else:
            results['games_lost'] += 1
            results['failed_seeds'].append(seed)
            if verbose:
                print(f"❌ Lost game {game_num}")
    
    end_time = time.time()
    
    # Calculate and display statistics
    print("\n" + "=" * 60)
    print("📊 PERFORMANCE SUMMARY")
    print("=" * 60)
    
    win_rate = (results['games_won'] / num_games) * 100
    avg_attempts = results['total_attempts'] / num_games
    
    print(f"🏆 Games Won: {results['games_won']}/{num_games} ({win_rate:.1f}%)")
    print(f"❌ Games Lost: {results['games_lost']}/{num_games} ({100-win_rate:.1f}%)")
    print(f"📈 Average Attempts: {avg_attempts:.2f}")
    print(f"⏱️  Total Time: {end_time - start_time:.2f} seconds")
    print(f"🧠 Words Learned: {len(results['learned_words'])}")
    
    print(f"\n📊 Attempt Distribution:")
    if results['games_won'] > 0:
        max_attempts = max(results['attempt_distribution'].keys()) if results['attempt_distribution'] else 0
        for attempts in range(1, max_attempts + 1):
            count = results['attempt_distribution'][attempts]
            if count > 0:
                percentage = (count / results['games_won']) * 100
                print(f"  {attempts} attempts: {count} games ({percentage:.1f}% of wins)")
    else:
        print("  No games won to show distribution")
    
    if results['failed_seeds']:
        print(f"\n❌ Failed Seeds (for debugging): {results['failed_seeds']}")
        
        # Debug failed seeds if requested
        if debug_failures:
            print(f"\n🔍 DEBUGGING FAILED SEEDS:")
            print("=" * 60)
            for i, failed_seed in enumerate(results['failed_seeds']):
                print(f"\n🚨 Debugging Failed Seed {i+1}/{len(results['failed_seeds'])}: {failed_seed}")
                debug_failed_game(failed_seed)
                
                # Add separator between multiple failed seeds
                if i < len(results['failed_seeds']) - 1:
                    print("\n" + "="*80)
    
    if results['winning_words']:
        print(f"\n🏆 Sample Winning Words: {results['winning_words'][:10]}")
    
    if results['learned_words']:
        print(f"\n🧠 Words Added to Dataset: {results['learned_words']}")
    
    return results


def main():
    """Main function to run the performance test with learning."""
    print("🚀 Enhanced AI Wordle Solver with Constraint-Based Logic")
    print("=" * 60)
    print("This solver uses constraint-based filtering and can generate")
    print("failsafe guesses when dictionary words don't match constraints.")
    print("🔄 Running without attempt limits - solver will continue until completion!")
    print("🧠 Self-improving: Words taking >8 attempts will be added to the dataset!")
    print()
    
    # Run performance test with 100 games for dataset improvement
    print("🎯 Running 100 games to build and improve the dataset...")
    results = run_performance_test(num_games=100, verbose=False, debug_failures=False, learn_threshold=8)
    
    print("\n🎯 Dataset improvement completed!")
    print("Key improvements:")
    print("• Constraint-based letter filtering")
    print("• Dynamic word generation as failsafe")
    print("• Robust duplicate letter handling")
    print("• No artificial attempt limits")
    print("• Self-improving dataset")
    print(f"• Added {len(results['learned_words'])} new words to dataset")
    
    # Show final dataset size
    try:
        final_words = load_word_list()
        print(f"📚 Final dataset size: {len(final_words)} words")
    except:
        print("📚 Final dataset size: Unable to determine")


def debug_failed_game(seed: int) -> None:
    """
    Run a debugging session for a failed game seed.
    Shows comprehensive analysis without verbose output.
    
    Args:
        seed: The seed that failed
    """
    print(f"\n🔍 DEBUGGING FAILED SEED: {seed}")
    print("=" * 80)
    
    # Run the game silently to get final state
    success, attempts, final_word = play_wordle_game(seed=seed, verbose=False)
    
    if success:
        print(f"🤔 Seed {seed} actually succeeded in {attempts} attempts with word: {final_word}")
        return
    
    # Re-run with tracking to analyze the failure
    base_url = "https://wordle.votee.dev:8000"
    words = load_word_list()
    solver = WordleSolver(words)
    
    game_history = []
    attempt = 0
    
    while attempt < 50:  # Safety limit
        attempt += 1
        
        try:
            guess = solver.get_next_guess()
        except Exception as e:
            print(f"❌ Error generating guess at attempt {attempt}: {e}")
            break
        
        feedback = get_feedback(guess, seed, base_url)
        if not feedback:
            print(f"❌ API error at attempt {attempt}")
            break
        
        # Store turn data
        game_history.append({
            'attempt': attempt,
            'guess': guess,
            'feedback': feedback
        })
        
        # Check if won
        all_correct = all(result['result'] == 'correct' for result in feedback)
        if all_correct:
            print(f"🎉 Actually won in {attempt} attempts with: {guess}")
            return
        
        # Update solver
        solver.update_constraints(guess, feedback)
    
    # Show comprehensive analysis
    print(f"\n❌ GAME FAILED AFTER {len(game_history)} ATTEMPTS")
    print("=" * 80)
    
    # Show visual game history
    print("🎮 GAME HISTORY:")
    for turn in game_history:
        visual_guess = ""
        for result in turn['feedback']:
            letter = result['guess'].upper()
            status = result['result']
            
            if status == 'correct':
                emoji = "🟢"
            elif status == 'present':
                emoji = "🟡"
            else:
                emoji = "⚫"
            
            visual_guess += f"{letter}{emoji}"
        
        print(f"  Turn {turn['attempt']}: {turn['guess']} → {visual_guess}")
    
    # Show final constraints
    print(f"\n🔍 FINAL CONSTRAINTS:")
    print(f"  Confirmed positions: {solver.confirmed_positions}")
    print(f"  Must include letters: {solver.must_include_letters}")
    print(f"  Absent letters: {solver.absent_letters}")
    
    # Analyze what went wrong
    print(f"\n🔬 FAILURE ANALYSIS:")
    final_valid_words = solver.possible_words
    print(f"  Dictionary words matching final constraints: {len(final_valid_words)}")
    
    if len(final_valid_words) == 0:
        print("  🚨 ISSUE: No dictionary words match the final constraints!")
        print("  This suggests the target word is not in our dictionary.")
        
        # Try to generate what the failsafe word would be
        try:
            failsafe_word = solver._generate_constraint_satisfying_word()
            print(f"  🔧 Failsafe word would be: {failsafe_word}")
        except Exception as e:
            print(f"  ❌ Error generating failsafe word: {e}")
    
    elif len(final_valid_words) <= 10:
        print(f"  📝 Remaining candidates: {sorted(list(final_valid_words))}")
        print("  🤔 The solver had valid options but may need better selection strategy.")
    
    else:
        print(f"  📈 Too many candidates remaining: {len(final_valid_words)}")
        print("  🎯 The solver needs to be more aggressive in narrowing down options.")


if __name__ == "__main__":
    main()