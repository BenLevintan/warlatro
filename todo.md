# 🃏 Project Roadmap: Warlatro (Retro Edition)

## ✅ Phase 1: Core Systems & Architecture (Completed)
- [x] **Game State Manager:** Implemented `GameState` enum (`DRAWING`, `DECIDING`, `SHOPPING`, `PACK_OPENING`, `GAME_OVER`).
- [x] **Deck & Hand Logic:** `DeckManager` successfully handles the master deck, shuffling, drawing, and discards.
- [x] **The Evaluation Pipeline:** `scoring.py` correctly calculates base hands, applies card modifiers (Bonus/Mult), and evaluates all Jokers in sequence.
- [x] **Visuals & Shaders:** Custom CRT/Scanline fragment shader implemented via Arcade's GL context.

## 🔄 Phase 2: Refactoring & Save Data (Active)
- [ ] **Refactor Joker Scoring (Optional but Recommended):**
  - *Current State:* All Joker logic is hardcoded into `calculate_hand_score`.
  - *Goal:* Move the evaluation logic into the `Joker` class itself (e.g., `joker.calculate_bonus(hand, context)`) to make adding future Jokers fully modular.
- [ ] **Develop `SaveManager` Class:**
  - Import Python's `json` module.
  - Create standard functions: `load_save_data()` and `write_save_data()`.
- [ ] **Map the Save Data Structure:**
  - Create the default dictionary template for lifetime stats (`highest_score`, `total_hands_played`, `favorite_joker`) and unlockable flags.

## ✅ Phase 3: Economy & Joker Expansion (Completed)
- [x] **Wallet Logic:** `ShopManager` handles coins, end-of-round payouts, and pack/joker purchasing.
- [x] **Base Joker Implementation:** Original 17 Jokers fully functional.
- [x] **Economy-Scaling & Generating Jokers:** Added and tested the financial suite:
  - **Severance Package:** +$2 per discarded face card.
  - **The Harvest:** +$5 end-of-round payout.
  - **Petty Cash:** +3 chips per $1 in the bank.
  - **Capital Gains:** +x1 Mult per $10 in the bank.

## 🎵 Phase 4: Audio Polish (Active)
- [x] **Stem Mixing Architecture:** `AudioManager` successfully handles simultaneous tracks and volume lerping.
- [x] **SFX Hooks:** Card clicking, buying, and modifying sounds are hooked up.
- [ ] **Track Expansion (If desired):** Add dynamic game states for the audio manager to track (e.g., an intense music layer that fades in during the final hand/discard).

## 📈 Phase 5: Meta-Progression
- [ ] **Run Analytics:** Hook the `SaveManager` into `GameState.GAME_OVER` to update lifetime stats based on the completed run.
- [ ] **Frequency Tracking:** Add logic to log the most frequently played cards and purchased jokers.
- [ ] **Unlocks System:**
  - After a run, check if any stats cross a threshold.
  - Flip the boolean in the JSON file and display a "New Joker Unlocked!" UI element on the main menu.

## 🚀 Phase 6: CI/CD & Deployment
- [ ] **GitHub Actions Setup:** Write a `.yml` workflow file for automated cross-platform builds.
- [ ] **Linux Build:** Configure the action to run PyInstaller on an Ubuntu runner.
- [ ] **Windows Build:** Configure the action to run PyInstaller on a Windows runner.
- [ ] **Itch.io Page:** Prepare the storefront with screenshots, description, and the compiled builds.