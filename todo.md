# 🃏 Project Roadmap: Roguelike Deck-Builder

## 🎯 Phase 1: Core Systems & Architecture

### 🗃️ Data & State Management
- [ ] **Game State Manager:** Create a central state machine to handle transitions (Main Menu -> Run Started -> Shop/Draft -> Battle/Blind -> Run Over).
- [ ] **Deck & Hand Logic:** - Implement a `Deck` class (shuffling, drawing, discarding).
  - Implement a `Hand` class (selecting cards, validating poker hands/combinations).
- [ ] **Save Data Architecture:**
  - Create a `SaveManager` class using Python's `json` module.
  - Implement read/write functions for `lifetime_stats` (highest level, favorite cards) and `unlocks`.

### 🧮 The Scoring Engine
- [ ] **Base Scoring:** Write the logic to calculate base chips and multipliers for standard hands.
- [ ] **The Evaluation Pipeline:** Set up the exact order of operations for scoring (Base Hand -> Card Enhancements -> Joker Modifiers).

---

## 🃏 Phase 2: Jokers & Economy

### 💰 The Bank System
- [ ] **Wallet Logic:** Create a robust system for adding, spending, and tracking the player's current money.
- [ ] **End-of-Round Payouts:** Calculate income based on remaining hands, discards, and base round rewards.

### 🤡 Joker Implementation
- [ ] **Base `Joker` Class:** Define standard methods like `on_hand_played()`, `on_discard()`, and `calculate_bonus()`.
- [ ] **Economy-Scaling Jokers:**
  - Implement the **Penny Pincher:** Adds +$2 flat to score for every $1 in the bank.
  - Implement the **Capitalist:** Adds +x1 Multiplier for every $10 in the bank.
  - *Testing:* Ensure these update dynamically during the scoring pipeline without hard-crashing the integer limits.
- [ ] **Coin-Generating Jokers:** Create jokers that trigger specific wallet deposits upon meeting conditions (e.g., discarding a face card).

---

## 🎨 Phase 3: Assets, Audio & Polish

### 👾 Visuals & Interface
- [ ] **Sprite Management:** Load and slice your pixel art sprite sheets for standard cards and jokers.
- [ ] **UI/UX Elements:** Build clean UI containers for the current score, required target score, wallet balance, and run stats.
- [ ] **Animations (Optional Polish):** Add simple lerping (smooth movement) for drawing cards and playing hands.

### 🎵 Dynamic Audio (Stem Mixing)
- [ ] **Audio Manager:** Load the 3 looping background tracks (`arcade.Sound`).
- [ ] **Sync System:** Start all 3 tracks simultaneously at runtime.
- [ ] **State-Based Mixing:** - Write a function to update the `.volume` properties of the tracks (1.0 for active, 0.0 for inactive) based on the current game state (e.g., Shop, Low-Stakes Blind, Boss Blind).

---

## 📈 Phase 4: Meta-Progression

### 🏆 Stat Tracking
- [ ] **Run Analytics:** Hook your data manager into the game loop to track `Largest Hand Played` and `Highest Level Reached` in real-time.
- [ ] **Frequency Tracking:** Add logic to log the `Favorite Card` and `Favorite Joker` upon run completion.

### 🔓 Unlocks System
- [ ] **Condition Checks:** After writing the run data to the JSON file, check if any locked Jokers' specific thresholds are met.
- [ ] **The "New" Flag:** Add a visual indicator in the game's collection menu when a new Joker is unlocked.

---

## 🚀 Phase 5: CI/CD & Deployment

### ⚙️ Automated Build Pipeline
- [ ] **GitHub Actions Setup:** Write a `.yml` workflow file in your repository's `.github/workflows` directory.
- [ ] **Linux Build:** Configure the action to run PyInstaller on an Ubuntu runner.
- [ ] **Windows Build:** Configure the action to run PyInstaller on a Windows runner.
- [ ] **Release Generation:** Set the action to automatically zip the executables and attach them to a GitHub Release upon a new tag.
- [ ] **Itch.io Page:** Prepare the storefront with screenshots, a description, and the final compiled builds.