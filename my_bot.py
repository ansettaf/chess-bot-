#!/usr/bin/env python3
"""
Chess.com Training Bot - Fixed with Chess.com Specific Interactions
A comprehensive bot for playing training and analysis games on Chess.com.
This bot is designed ONLY for training purposes and analysis games, NOT for live competitive play.

Requirements:
- pip install selenium python-chess stockfish webdriver-manager
- Download Stockfish engine from https://stockfishchess.org/download/
- Chrome browser installed

Author: AI Assistant
License: MIT
"""

import os
import time
import random
import logging
import json
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any

import chess
import chess.engine
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

class ChessComBot:
    """
    Chess.com training bot with Chess.com specific move execution.
    """
    
    def __init__(self, stockfish_path: str, headless: bool = False, log_moves: bool = True):
        """Initialize the Chess.com bot."""
        self.stockfish_path = stockfish_path
        self.headless = headless
        self.log_moves = log_moves
        self.driver = None
        self.engine = None
        self.board = chess.Board()
        self.move_log = []
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('chess_bot.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_browser(self) -> None:
        """Set up Chrome browser with appropriate options."""
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless")
            
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("--window-size=1400,900")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.logger.info("Browser setup completed successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to setup browser: {str(e)}")
            raise
    
    def setup_engine(self) -> None:
        """Initialize the Stockfish engine."""
        try:
            if not os.path.exists(self.stockfish_path):
                raise FileNotFoundError(f"Stockfish not found at {self.stockfish_path}")
            
            self.engine = chess.engine.SimpleEngine.popen_uci(self.stockfish_path)
            
            self.engine.configure({
                "Skill Level": 15,
                "Threads": 1,
                "Hash": 16
            })
            
            self.logger.info("Stockfish engine initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Stockfish: {str(e)}")
            raise
    
    def handle_popups(self) -> None:
        """Handle any pop-ups or cookie banners that might appear."""
        try:
            popup_selectors = [
                "button[data-cookie-banner='accept']",
                "button[id*='accept']",
                "button[class*='accept']",
                "button[class*='cookie']",
                ".cookie-banner button",
                "#cookie-banner button",
                "[data-testid*='accept']",
                ".ui_modal-container button",
                ".ui_outside-close-component"
            ]
            
            for selector in popup_selectors:
                try:
                    popup = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if popup.is_displayed():
                        popup.click()
                        self.logger.info(f"Dismissed popup with selector: {selector}")
                        time.sleep(1)
                        break
                except NoSuchElementException:
                    continue
                    
        except Exception as e:
            self.logger.debug(f"No popups to handle: {str(e)}")
    
    def login(self, username: str, password: str) -> bool:
        """Log into Chess.com with provided credentials."""
        try:
            self.logger.info("Attempting to log into Chess.com")
            self.driver.get("https://www.chess.com/login")
            
            wait = WebDriverWait(self.driver, 20)
            
            time.sleep(2)
            self.handle_popups()
            time.sleep(3)
            
            # Find username field
            username_field = None
            username_selectors = [
                (By.ID, "username"),
                (By.NAME, "username"),
                (By.CSS_SELECTOR, "input[placeholder*='username' i]"),
                (By.CSS_SELECTOR, "input[type='text']"),
                (By.CSS_SELECTOR, "input[name='_username']")
            ]
            
            for selector_type, selector_value in username_selectors:
                try:
                    username_field = wait.until(EC.element_to_be_clickable((selector_type, selector_value)))
                    self.logger.info(f"Found username field with selector: {selector_type}={selector_value}")
                    break
                except TimeoutException:
                    continue
            
            if not username_field:
                self.logger.error("Could not find username field")
                return False
            
            username_field.clear()
            time.sleep(0.5)
            username_field.send_keys(username)
            
            # Find password field
            password_field = None
            password_selectors = [
                (By.ID, "password"),
                (By.NAME, "password"),
                (By.CSS_SELECTOR, "input[type='password']"),
                (By.CSS_SELECTOR, "input[name='_password']")
            ]
            
            for selector_type, selector_value in password_selectors:
                try:
                    password_field = self.driver.find_element(selector_type, selector_value)
                    if password_field.is_displayed() and password_field.is_enabled():
                        self.logger.info(f"Found password field with selector: {selector_type}={selector_value}")
                        break
                except NoSuchElementException:
                    continue
            
            if not password_field:
                self.logger.error("Could not find password field")
                return False
            
            password_field.clear()
            time.sleep(0.5)
            password_field.send_keys(password)
            
            # Find login button
            login_button = None
            login_selectors = [
                (By.ID, "login"),
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.CSS_SELECTOR, "input[type='submit']"),
                (By.XPATH, "//button[contains(text(), 'Log In')]"),
                (By.XPATH, "//input[@value='Log In']")
            ]
            
            for selector_type, selector_value in login_selectors:
                try:
                    login_button = self.driver.find_element(selector_type, selector_value)
                    if login_button.is_displayed() and login_button.is_enabled():
                        self.logger.info(f"Found login button with selector: {selector_type}={selector_value}")
                        break
                except NoSuchElementException:
                    continue
            
            if not login_button:
                self.logger.error("Could not find login button")
                return False
            
            time.sleep(0.5)
            login_button.click()
            time.sleep(5)
            
            # Check login success
            success_selectors = [
                (By.CLASS_NAME, "user-username-component"),
                (By.CSS_SELECTOR, "[data-username]"),
                (By.CSS_SELECTOR, ".username"),
                (By.XPATH, "//a[contains(@href, '/member/')]"),
                (By.CSS_SELECTOR, ".nav-user-dropdown")
            ]
            
            for selector_type, selector_value in success_selectors:
                try:
                    wait.until(EC.presence_of_element_located((selector_type, selector_value)))
                    self.logger.info("Login successful")
                    return True
                except TimeoutException:
                    continue
            
            if "login" in self.driver.current_url.lower():
                self.logger.error("Login failed - still on login page")
                return False
            
            self.logger.info("Login appears successful - URL changed")
            return True
                
        except Exception as e:
            self.logger.error(f"Login failed: {str(e)}")
            return False
    
    def navigate_to_analysis_board(self) -> bool:
        """Navigate to the analysis board on Chess.com."""
        try:
            self.logger.info("Navigating to analysis board")
            self.driver.get("https://www.chess.com/analysis")
            
            wait = WebDriverWait(self.driver, 15)
            
            # Wait for chess board to load
            board_selectors = [
                "wc-chess-board",
                ".board",
                "[class*='board']"
            ]
            
            board_element = None
            for selector in board_selectors:
                try:
                    if selector.startswith('.') or selector.startswith('#') or selector.startswith('['):
                        board_element = wait.until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                    else:
                        board_element = wait.until(
                            EC.presence_of_element_located((By.TAG_NAME, selector))
                        )
                    self.logger.info(f"Found board with selector: {selector}")
                    break
                except TimeoutException:
                    continue
            
            if not board_element:
                self.logger.error("Could not find chess board element")
                return False
            
            time.sleep(3)
            self.handle_popups()
            
            self.logger.info("Successfully navigated to analysis board")
            return True
            
        except Exception as e:
            self.logger.error(f"Navigation failed: {str(e)}")
            return False
    
    def find_square_element(self, square: str) -> Optional[Any]:
        """
        Find a specific square element on the Chess.com board.
        
        Args:
            square (str): Chess square notation (e.g., 'e4')
            
        Returns:
            Optional[Any]: The square element if found
        """
        try:
            # Chess.com uses different square identification methods
            square_selectors = [
                f"[data-square='{square}']",
                f".square-{square}",
                f"#{square}",
                f"[class*='{square}']"
            ]
            
            for selector in square_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element and element.is_displayed():
                        self.logger.debug(f"Found square {square} with selector: {selector}")
                        return element
                except NoSuchElementException:
                    continue
            
            # If no direct square found, try calculating position within board
            return self.find_square_by_position(square)
            
        except Exception as e:
            self.logger.debug(f"Error finding square {square}: {str(e)}")
            return None
    
    def find_square_by_position(self, square: str) -> Optional[Any]:
        """
        Find square by calculating its position within the board grid.
        
        Args:
            square (str): Chess square notation (e.g., 'e4')
            
        Returns:
            Optional[Any]: Square element or board element with calculated offset
        """
        try:
            board_element = self.driver.find_element(By.TAG_NAME, "wc-chess-board")
            if not board_element:
                return None
            
            # Create a virtual square element with position data
            file_char = square[0]  # a-h
            rank_char = square[1]  # 1-8
            
            file_index = ord(file_char) - ord('a')  # 0-7
            rank_index = int(rank_char) - 1  # 0-7
            
            # Store position data for later use
            square_info = {
                'element': board_element,
                'file_index': file_index,
                'rank_index': rank_index,
                'square': square
            }
            
            return square_info
            
        except Exception as e:
            self.logger.error(f"Error finding square by position {square}: {str(e)}")
            return None
    
    def get_square_center_coordinates(self, square_info: Dict) -> Tuple[int, int]:
        """
        Calculate the center coordinates of a square.
        
        Args:
            square_info (Dict): Square information including element and indices
            
        Returns:
            Tuple[int, int]: (x, y) coordinates relative to board
        """
        try:
            board_element = square_info['element']
            file_index = square_info['file_index']
            rank_index = square_info['rank_index']
            
            # Get board dimensions
            rect = board_element.rect
            board_width = rect['width']
            board_height = rect['height']
            
            # Calculate square size
            square_width = board_width / 8
            square_height = board_height / 8
            
            # Calculate center position (assuming white perspective)
            # File 0 (a) is leftmost, rank 0 (1) is bottom
            x_offset = (file_index * square_width) + (square_width / 2)
            y_offset = ((7 - rank_index) * square_height) + (square_height / 2)
            
            self.logger.debug(f"Square {square_info['square']}: offset ({x_offset}, {y_offset})")
            
            return int(x_offset), int(y_offset)
            
        except Exception as e:
            self.logger.error(f"Error calculating coordinates: {str(e)}")
            return 0, 0
    
    def execute_move_with_drag_drop(self, move: chess.Move) -> bool:
        """
        Execute move using drag and drop with Chess.com specific handling.
        """
        try:
            from_square = chess.square_name(move.from_square)
            to_square = chess.square_name(move.to_square)
            
            self.logger.info(f"Executing move via drag-drop: {from_square} to {to_square}")
            
            # Find source and destination squares
            from_square_info = self.find_square_by_position(from_square)
            to_square_info = self.find_square_by_position(to_square)
            
            if not from_square_info or not to_square_info:
                self.logger.error("Could not find square elements")
                return False
            
            # Get board element
            board_element = from_square_info['element']
            
            # Calculate coordinates
            from_x, from_y = self.get_square_center_coordinates(from_square_info)
            to_x, to_y = self.get_square_center_coordinates(to_square_info)
            
            if from_x == 0 or to_x == 0:
                self.logger.error("Invalid coordinates calculated")
                return False
            
            # Scroll board into view
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", board_element)
            time.sleep(0.5)
            
            # Perform drag and drop with Chess.com specific events
            actions = ActionChains(self.driver)
            
            # Move to source square and start drag
            actions.move_to_element_with_offset(board_element, from_x, from_y)
            actions.click_and_hold()
            actions.pause(0.1)
            
            # Drag to destination
            actions.move_to_element_with_offset(board_element, to_x, to_y)
            actions.pause(0.1)
            actions.release()
            
            # Execute the action chain
            actions.perform()
            
            # Wait for move animation
            time.sleep(1.5)
            
            self.logger.info(f"Drag-drop move completed: {move}")
            return True
            
        except Exception as e:
            self.logger.error(f"Drag-drop move failed {move}: {str(e)}")
            return False
    
    def execute_move_with_javascript(self, move: chess.Move) -> bool:
        """
        Execute move using JavaScript to directly interact with Chess.com's board.
        """
        try:
            from_square = chess.square_name(move.from_square)
            to_square = chess.square_name(move.to_square)
            
            self.logger.info(f"Executing move via JavaScript: {from_square} to {to_square}")
            
            # JavaScript code to interact with Chess.com's board
            js_code = f"""
            var fromSquare = '{from_square}';
            var toSquare = '{to_square}';
            
            // Try to find Chess.com board component
            var board = document.querySelector('wc-chess-board');
            if (board) {{
                try {{
                    // Try to access board's internal methods
                    if (board.game && board.game.move) {{
                        var result = board.game.move({{from: fromSquare, to: toSquare}});
                        if (result) {{
                            console.log('Move executed via game.move()');
                            return true;
                        }}
                    }}
                    
                    // Try alternative method
                    if (board.move) {{
                        var result = board.move(fromSquare, toSquare);
                        if (result) {{
                            console.log('Move executed via board.move()');
                            return true;
                        }}
                    }}
                    
                    // Try to trigger mouse events on squares
                    var squares = board.querySelectorAll('[class*="square"]');
                    var fromEl = null, toEl = null;
                    
                    squares.forEach(function(square) {{
                        var classes = square.className;
                        if (classes.includes('square-' + fromSquare)) {{
                            fromEl = square;
                        }}
                        if (classes.includes('square-' + toSquare)) {{
                            toEl = square;
                        }}
                    }});
                    
                    if (fromEl && toEl) {{
                        // Simulate mouse events
                        var mouseDown = new MouseEvent('mousedown', {{bubbles: true}});
                        var mouseUp = new MouseEvent('mouseup', {{bubbles: true}});
                        var click = new MouseEvent('click', {{bubbles: true}});
                        
                        fromEl.dispatchEvent(mouseDown);
                        fromEl.dispatchEvent(click);
                        
                        setTimeout(function() {{
                            toEl.dispatchEvent(mouseUp);
                            toEl.dispatchEvent(click);
                        }}, 100);
                        
                        console.log('Move executed via mouse events');
                        return true;
                    }}
                    
                }} catch(e) {{
                    console.log('JavaScript move error:', e);
                }}
            }}
            
            return false;
            """
            
            # Execute JavaScript
            result = self.driver.execute_script(js_code)
            
            if result:
                self.logger.info(f"JavaScript move executed successfully: {move}")
                time.sleep(1)
                return True
            else:
                self.logger.debug("JavaScript move execution returned false")
                return False
                
        except Exception as e:
            self.logger.error(f"JavaScript move failed {move}: {str(e)}")
            return False
    
    def execute_move_with_keyboard(self, move: chess.Move) -> bool:
        """
        Execute move by typing the move notation.
        """
        try:
            from_square = chess.square_name(move.from_square)
            to_square = chess.square_name(move.to_square)
            
            self.logger.info(f"Executing move via keyboard: {from_square} to {to_square}")
            
            # Try to find an input field or focus on the board
            board = self.driver.find_element(By.TAG_NAME, "wc-chess-board")
            if board:
                board.click()  # Focus on board
                time.sleep(0.5)
                
                # Type the move notation
                move_notation = from_square + to_square
                
                # Try different ways to input the move
                from selenium.webdriver.common.keys import Keys
                
                # Method 1: Direct typing
                actions = ActionChains(self.driver)
                actions.send_keys(move_notation)
                actions.send_keys(Keys.ENTER)
                actions.perform()
                
                time.sleep(1)
                
                self.logger.info(f"Keyboard move executed: {move}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Keyboard move failed {move}: {str(e)}")
            return False
    
    def get_board_state(self) -> Optional[chess.Board]:
        """Read the current board state."""
        try:
            board = chess.Board()
            self.logger.info("Using starting position for analysis board")
            return board
            
        except Exception as e:
            self.logger.error(f"Failed to read board state: {str(e)}")
            return None
    
    def calculate_best_move(self, board: chess.Board, time_limit: float = 1.0) -> Optional[chess.Move]:
        """Calculate the best move using Stockfish engine."""
        try:
            if board.is_game_over():
                self.logger.info("Game is over, no moves to calculate")
                return None
            
            result = self.engine.play(board, chess.engine.Limit(time=time_limit))
            
            if result.move:
                self.logger.info(f"Calculated best move: {result.move}")
                return result.move
            else:
                self.logger.warning("Engine returned no move")
                return None
                
        except Exception as e:
            self.logger.error(f"Move calculation failed: {str(e)}")
            return None
    
    def execute_move(self, move: chess.Move) -> bool:
        """Execute a move on the Chess.com board using multiple methods."""
        try:
            from_square = chess.square_name(move.from_square)
            to_square = chess.square_name(move.to_square)
            
            self.logger.info(f"Executing move: {from_square} to {to_square}")
            
            # Try multiple methods in order of preference
            methods = [
                ("drag_drop", self.execute_move_with_drag_drop),
                ("javascript", self.execute_move_with_javascript),
                ("keyboard", self.execute_move_with_keyboard)
            ]
            
            for method_name, method_func in methods:
                try:
                    self.logger.info(f"Trying {method_name} method...")
                    if method_func(move):
                        # Log the successful move
                        if self.log_moves:
                            move_entry = {
                                'timestamp': datetime.now().isoformat(),
                                'move': str(move),
                                'from': from_square,
                                'to': to_square,
                                'method': method_name
                            }
                            self.move_log.append(move_entry)
                        
                        self.logger.info(f"Move executed successfully with {method_name}: {move}")
                        return True
                except Exception as e:
                    self.logger.debug(f"{method_name} method failed: {str(e)}")
                    continue
            
            self.logger.error(f"All move execution methods failed for {move}")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to execute move {move}: {str(e)}")
            return False
    
    def save_move_log(self) -> None:
        """Save move log to file."""
        if self.move_log:
            try:
                filename = f"chess_moves_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, 'w') as f:
                    json.dump(self.move_log, f, indent=2)
                self.logger.info(f"Move log saved to {filename}")
            except Exception as e:
                self.logger.error(f"Failed to save move log: {str(e)}")
    
    def play_game_loop(self, max_moves: int = 100) -> None:
        """Main game loop for playing moves."""
        moves_played = 0
        consecutive_failures = 0
        max_failures = 3
        current_board = chess.Board()
        
        self.logger.info(f"Starting game with maximum {max_moves} moves...")
        
        while moves_played < max_moves:
            try:
                # Check if game is over
                if current_board.is_game_over():
                    result = current_board.result()
                    if result == "1-0":
                        self.logger.info("Game Over: White wins!")
                    elif result == "0-1":
                        self.logger.info("Game Over: Black wins!")
                    elif result == "1/2-1/2":
                        self.logger.info("Game Over: Draw!")
                    else:
                        self.logger.info(f"Game Over: {result}")
                    break
                
                # Reset failure counter on successful iteration start
                consecutive_failures = 0
                
                # Show current position info
                turn = "White" if current_board.turn else "Black"
                self.logger.info(f"Move {moves_played + 1}: {turn} to play")
                
                # Calculate best move
                best_move = self.calculate_best_move(current_board, time_limit=2.0)
                if not best_move:
                    self.logger.error("Could not calculate move, skipping turn")
                    time.sleep(5)
                    continue
                
                # Execute the move
                if self.execute_move(best_move):
                    moves_played += 1
                    
                    # Update our internal board state
                    current_board.push(best_move)
                    
                    # Log move in algebraic notation
                    try:
                        # Get the move in standard algebraic notation
                        temp_board = current_board.copy()
                        temp_board.pop()  # Remove the move we just made
                        san_move = temp_board.san(best_move)
                        self.logger.info(f"Successfully played move {moves_played}: {san_move} ({best_move})")
                    except:
                        self.logger.info(f"Successfully played move {moves_played}: {best_move}")
                    
                    # Show some position info occasionally
                    if moves_played % 10 == 0:
                        self.logger.info(f"Position after {moves_played} moves: {current_board.fen()}")
                        
                else:
                    self.logger.error("Move execution failed, retrying...")
                    consecutive_failures += 1
                    if consecutive_failures >= max_failures:
                        self.logger.error("Too many move execution failures, stopping")
                        break
                    time.sleep(2)
                    continue
                
                # Wait before next move (shorter for faster play)
                time.sleep(random.uniform(2, 4))
                
            except KeyboardInterrupt:
                self.logger.info("Game loop interrupted by user")
                break
            except Exception as e:
                self.logger.error(f"Error in game loop: {str(e)}")
                consecutive_failures += 1
                if consecutive_failures >= max_failures:
                    break
                time.sleep(5)
        
        # Final game summary
        if moves_played > 0:
            self.logger.info(f"Game completed with {moves_played} moves played")
            self.logger.info(f"Final position: {current_board.fen()}")
        else:
            self.logger.info("No moves were played")
    
    def cleanup(self) -> None:
        """Clean up resources."""
        try:
            if self.engine:
                self.engine.quit()
                self.logger.info("Stockfish engine closed")
            
            if self.driver:
                self.driver.quit()
                self.logger.info("Browser closed")
            
            if self.log_moves:
                self.save_move_log()
                
        except Exception as e:
            self.logger.error(f"Cleanup error: {str(e)}")
    
    def run(self, username: str, password: str, max_moves: int = 50) -> None:
        """Main run method to execute the bot."""
        try:
            self.setup_browser()
            self.setup_engine()
            
            if not self.login(username, password):
                raise Exception("Login failed")
            
            if not self.navigate_to_analysis_board():
                raise Exception("Failed to navigate to analysis board")
            
            self.logger.info("Starting game loop...")
            self.play_game_loop(max_moves)
            
        except Exception as e:
            self.logger.error(f"Bot execution failed: {str(e)}")
        finally:
            self.cleanup()

def main():
    """Main function to run the Chess.com bot."""
    # CONFIGURATION - Update these paths and credentials
    STOCKFISH_PATH = "/usr/bin/stockfish"
    CHESS_COM_USERNAME = "ur mail"
    CHESS_COM_PASSWORD = "ur pass"
    
    # Bot settings
    HEADLESS_MODE = False
    LOG_MOVES = True
    MAX_MOVES = 100  # Play a full game (50 moves per side)
    CONTINUOUS_PLAY = False  # Set to True for unlimited games
    
    # Validate Stockfish path
    if not os.path.exists(STOCKFISH_PATH):
        print(f"Error: Stockfish not found at {STOCKFISH_PATH}")
        print("Please download Stockfish from https://stockfishchess.org/download/")
        print("and update the STOCKFISH_PATH variable with the correct path.")
        return
    
    # Initialize bot
    bot = ChessComBot(
        stockfish_path=STOCKFISH_PATH,
        headless=HEADLESS_MODE,
        log_moves=LOG_MOVES
    )
    
    try:
        if CONTINUOUS_PLAY:
            # Play multiple games
            game_count = 0
            while True:
                game_count += 1
                print(f"\n=== Starting Game {game_count} ===")
                try:
                    bot.run(CHESS_COM_USERNAME, CHESS_COM_PASSWORD, MAX_MOVES)
                    print(f"Game {game_count} completed")
                    
                    # Ask if user wants to continue
                    response = input("Play another game? (y/n): ").lower()
                    if response != 'y' and response != 'yes':
                        break
                        
                    # Reset for next game
                    time.sleep(2)
                    
                except KeyboardInterrupt:
                    print(f"\nStopped during game {game_count}")
                    break
                except Exception as e:
                    print(f"Game {game_count} failed: {str(e)}")
                    response = input("Try another game? (y/n): ").lower()
                    if response != 'y' and response != 'yes':
                        break
        else:
            # Play single game
            bot.run(CHESS_COM_USERNAME, CHESS_COM_PASSWORD, MAX_MOVES)
            
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Bot failed: {str(e)}")
    
    print("Chess bot session ended.")

if __name__ == "__main__":
    main()
