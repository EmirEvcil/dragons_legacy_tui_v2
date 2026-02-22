# Legend of Dragon's Legacy - Development Log

## Project Overview

**Legend of Dragon's Legacy** is a turn-based, TUI (Terminal User Interface) multiplayer RPG game built with Python. The game features a modern, beautiful interface using Textual, a FastAPI backend with WebSocket support, and local SQLite database storage.

## 🏗️ Architecture

### Backend (FastAPI)
- **FastAPI** for REST API endpoints
- **WebSocket** support for real-time multiplayer features
- **SQLAlchemy** with async SQLite for database operations
- **JWT authentication** with secure password hashing
- **Security questions** for password recovery

### Frontend (Textual TUI)
- **Textual** for modern terminal user interface
- **Custom CSS styling** for beautiful appearance
- **Form validation** with real-time feedback
- **Async HTTP client** for API communication
- **Screen-based navigation** system

### Database
- **SQLite** with async operations
- **User management** with email/password authentication
- **Security questions** system for password recovery
- **Character data** storage (expandable for game features)

## 📁 Project Structure

```
dragons_legacy/
├── __init__.py
├── backend/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   └── schemas.py           # Pydantic models
├── database/
│   ├── __init__.py
│   └── database.py          # Database configuration
├── models/
│   ├── __init__.py
│   ├── user.py              # User model
│   ├── security_question.py # Security question model
│   ├── character.py         # Character model
│   ├── world_data.py        # Map graph, NPCs, travel time
│   ├── item_data.py         # Item catalog (classes, rarities, stats)
│   └── inventory.py         # InventoryItem DB model
├── utils/
│   ├── __init__.py
│   └── auth.py              # Authentication utilities
└── frontend/
    ├── __init__.py
    ├── app.py               # Main Textual application
    ├── api_client.py        # HTTP client for API
    ├── styles.py            # CSS styles
    └── screens/
        ├── __init__.py
        ├── login_screen.py           # Login interface
        ├── registration_screen.py    # Registration interface
        ├── forgot_password_screen.py # Password reset interface
        ├── character_creation_screen.py # Character creation (race, gender, nickname)
        └── game_screen.py            # Game screen (HUD, location, NPCs, travel)
```

## 🚀 Features Implemented

### ✅ Authentication System
- **User Registration**
  - Email validation
  - Password strength requirements (minimum 6 characters)
  - Password confirmation
  - Security question selection from 5 predefined options
  - Secure password hashing with bcrypt
  - Email uniqueness validation

- **User Login**
  - Email/password authentication
  - JWT token generation
  - Input validation with real-time feedback
  - Error handling for invalid credentials

- **Password Recovery**
  - Email-based user lookup
  - Security question verification
  - New password setting with confirmation
  - Multi-step process with clear progression

### ✅ Modern TUI Interface
- **Beautiful Design**
  - Dragon-themed styling with emojis
  - Modern color scheme with CSS variables
  - Responsive form layouts
  - Hover and focus states
  - Loading indicators

- **User Experience**
  - Keyboard navigation (Tab, Enter)
  - Real-time form validation
  - Clear error and success messages
  - Intuitive button placement
  - Screen transitions

### ✅ Backend API
- **RESTful Endpoints**
  - `POST /register` - User registration
  - `POST /login` - User authentication
  - `GET /security-questions` - Get available security questions
  - `GET /user/{email}/security-question` - Get user's security question
  - `POST /reset-password` - Password reset
  - `POST /characters` - Character creation (nickname, race, gender)
  - `GET /characters/by-email/{email}` - Get user's character data
  - `POST /characters/travel` - Travel to an adjacent region
  - `GET /world/regions/{name}` - Get region info and connected regions
  - `GET /world/npcs/{name}` - Get NPCs in a region
  - `GET /items` - Get the complete item catalog
  - `GET /inventory/{email}` - Get player's inventory (server-side)
  - `POST /inventory/add` - Add item to inventory
  - `POST /inventory/delete` - Delete item from inventory
  - `WebSocket /ws` - Real-time communication (ready for game features)

- **Database Integration**
  - Async SQLite operations
  - Automatic table creation
  - Relationship management
  - Data validation

### ✅ Security Features
- **Password Security**
  - Bcrypt hashing
  - Secure salt generation
  - Password strength validation

- **JWT Authentication**
  - Token-based authentication
  - Configurable expiration times
  - Secure secret key management

- **Security Questions**
  - 5 predefined questions:
    1. "What was the name of your first pet?"
    2. "What is your mother's maiden name?"
    3. "What was the name of your first school?"
    4. "What city were you born in?"
    5. "What is your favorite childhood memory location?"
  - Case-insensitive answer matching
  - Secure answer hashing

## 🔧 Installation & Setup

### Prerequisites
- Python 3.8+
- pip package manager

### Dependencies
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
websockets==12.0
textual==0.45.1
sqlalchemy==2.0.23
aiosqlite==0.19.0
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0
python-multipart==0.0.6
email-validator==2.1.0
httpx==0.25.2
```

### Installation Steps
1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the backend server:**
   ```bash
   python main.py backend
   ```
   - API available at: http://localhost:8000
   - API documentation at: http://localhost:8000/docs

3. **Start the TUI client (in another terminal):**
   ```bash
   python main.py frontend
   ```

## 🎮 How to Use

### Starting the Game
1. Run `python main.py` for usage instructions
2. Start the backend server first
3. Start the frontend client in another terminal

### User Registration
1. Click "Register" on the login screen
2. Enter email and password
3. Confirm password
4. Select a security question
5. Provide security answer
6. Account created successfully

### User Login
1. Enter email and password on login screen
2. Click "Login" or press Enter
3. Successful login redirects to character creation

### Password Recovery
1. Click "Forgot Password?" on login screen
2. Enter your email address
3. Answer your security question
4. Set new password
5. Return to login with new credentials

## ✅ Character Creation Screen

The character creation screen has been fully implemented with the following features:

### Implemented Features:
- **Race Selection** - Two races defined:
  - **Magmar** - Displayed with red styling (🚧 **Coming Soon** — disabled, not selectable)
  - **Human** - Displayed with green styling when selected (✅ **Available**)
- **Gender Selection** - Two options:
  - **Female**
  - **Male**
- **Nickname Entry** - With strict validation rules:
  - Maximum 12 characters
  - No spaces allowed
  - No special characters allowed (only letters and numbers)
  - Unique nickname enforcement (server-side)

### Flow:
- After successful registration → redirected to Character Creation screen (new user, no character yet)
- After successful login:
  - If the user **has a character** → redirected directly to Game screen
  - If the user **does not have a character** → redirected to Character Creation screen
- After character creation → redirected to Game screen

### Technical Details:
- `NicknameValidator` class for client-side nickname validation
- Race and gender selection via toggle buttons with visual feedback
- `POST /characters` API endpoint for character creation with server-side validation
- `CharacterCreate` Pydantic schema with `field_validator` for nickname, race, and gender
- Character model updated with `nickname`, `race`, `gender`, and `current_map` fields
- Nickname uniqueness enforced at database level (unique constraint + API check)
- Login response (`Token` schema) includes `has_character` boolean flag to enable smart routing
- The `/login` endpoint queries the `characters` table to determine if the authenticated user has an existing character
- Starting map is automatically assigned based on race (`RACE_STARTING_MAP` dictionary)
- Magmar race creation is blocked on both frontend (disabled button) and backend (schema validation)

## ✅ Game Screen (HUD & Action Menu)

The game screen features a full 3-panel layout with a character HUD and action menu:

### Layout:
- **Top Bar** — Displays the current map name (e.g., "📍 Settlement of Klesva")
- **Left Panel (Character Stats)** — Shows:
  - Character nickname
  - Race & Gender
  - Level
  - Experience (EXP)
  - HP (red, bold)
  - Mana (blue, bold)
- **Center Panel (Game Area)** — Dynamic content area that shows:
  - Welcome message on login
  - Location panel with travel buttons
  - NPC list with interaction buttons
  - Travel countdown timer
  - TODO placeholders for other features
- **Right Panel (Actions)** — Six action buttons:
  - 🎒 Inventory (TODO)
  - 📍 Location (✅ Implemented — shows connected regions, travel)
  - ⚔️ Hunt (TODO)
  - 📬 Mailbox (TODO)
  - 📋 Quests (TODO)
  - 🧙 NPC List (✅ Implemented — shows region NPCs)
- **Bottom Bar** — Logout button

### Maps:
- **Human Starting Map:** Settlement of Klesva
- **Magmar Starting Map:** TBD (race not yet playable)

### Technical Details:
- Character data is fetched via `GET /characters/by-email/{email}` on screen show
- HUD dynamically updates all stat widgets from API response
- `current_map` field added to Character model and `CharacterResponse` schema
- `RACE_STARTING_MAP` dictionary in character model maps races to starting locations
- Center panel uses a `#dynamic_area` container for mounting/unmounting travel and NPC buttons at runtime

## ✅ Location & Travel System

Regions are connected in a node (graph) structure. Clicking "📍 Location" shows the accessible adjacent regions as travel buttons.

### Human Race Map Path:
```
Settlement of Klesva ↔ Baurwill Town ↔ King's Tomb ↔ Light Square ↔ O'Delvays City Center
```

### Travel Mechanics:
- Clicking a region button **moves you there immediately** — the map, top bar, and NPC list update instantly
- After arriving, a **travel cooldown** starts — this blocks only the next travel, not any other action
- The cooldown countdown is displayed in **real time** in the left stats panel (`⏳ Cooldown: Xs`)
- The Location panel also shows the remaining cooldown when opened during an active cooldown
- When the cooldown expires, a toast notification appears and you may travel again
- If you try to travel while the cooldown is active, a warning message is shown

### Travel Time Formula (by character level):
| Level | Time (seconds) | Calculation |
|-------|---------------|-------------|
| 1     | 10s           | Base        |
| 2     | 25s           | 10 + 15     |
| 3     | 40s           | 10 + 30     |
| 4     | 55s           | 10 + 45     |
| 5     | 70s           | 10 + 60     |
| 6     | 80s           | 70 + 10     |
| 7     | 90s           | 70 + 20     |
| 8     | 100s          | 70 + 30     |
| 9     | 110s          | 70 + 40     |
| 10    | 120s          | 70 + 50     |

- **Levels 1–5:** +15 seconds per level
- **Levels 6–10:** +10 seconds per level
- **Max level:** 10

### Technical Details:
- `world_data.py` module contains `HUMAN_MAP_GRAPH`, `REGION_NPCS`, and `get_travel_time()` function
- `POST /characters/travel` endpoint validates adjacency, **enforces cooldown server-side**, updates `current_map`, sets `travel_cooldown_until` in DB, returns `cooldown_remaining`
- `GET /world/regions/{name}` returns connected regions
- **Server-authoritative cooldown:** The `travel_cooldown_until` UTC timestamp is stored in the `characters` table — logging out and back in, or restarting the client, does **not** bypass the cooldown
- `CharacterResponse` includes a computed `cooldown_remaining` field (seconds) derived from the DB timestamp
- The `Character` model has a `cooldown_remaining` property that computes seconds from `travel_cooldown_until` vs. `datetime.now(UTC)`
- Frontend seeds its display timer from the server's `cooldown_remaining` value on login and after travel
- Frontend uses `set_interval(1.0, ...)` for the visual countdown tick (display only — server is the authority)
- `_sanitize_id()` helper converts region/NPC names to safe widget IDs
- Cooldown is displayed in the left stats panel via `#char_cooldown` widget (yellow, bold)

## ✅ NPC System

Each region has NPCs that appear in the NPC List. Clicking an NPC shows their name, role, and description. Interaction (trading, quests, dialogue) is TODO.

### NPCs by Region:

**Settlement of Klesva:**
- Elder Mirwen (Village Elder)
- Torvak the Smith (Blacksmith)
- Lina (Herbalist)

**Baurwill Town:**
- Captain Roderick (Guard Captain)
- Mara the Merchant (General Merchant)
- Old Gregor (Tavern Keeper)
- Sister Alia (Healer)

**King's Tomb:**
- Warden Duskhelm (Tomb Guardian)
- Spirit of King Aldric (Ancient Spirit)

**Light Square:**
- Archmage Solenne (Magic Instructor)
- Trader Fenwick (Rare Goods Merchant)
- Bard Elowen (Bard)

**O'Delvays City Center:**
- King Aldenvale III (King)
- Chancellor Voss (Royal Advisor)
- Guildmaster Theron (Adventurer's Guild)
- Master Armorer Kael (Master Blacksmith)
- Sage Orinthal (Lorekeeper)

### Technical Details:
- `GET /world/npcs/{region_name}` returns NPC list for a region
- NPC data is defined in `REGION_NPCS` dictionary in `world_data.py`
- NPC buttons are dynamically mounted in the center panel
- Clicking an NPC shows their info card; interaction is TODO

## 🚧 TODO: Magmar Race

The Magmar race is defined in the system but not yet playable:

### What's in place:
- `Race.MAGMAR` enum value exists in the character model
- Magmar button appears on character creation screen (disabled, "Coming Soon")
- Backend schema validation rejects Magmar race creation
- `RACE_STARTING_MAP` has a placeholder entry for Magmar

### What's needed:
- Magmar-specific starting map and map graph
- Magmar-specific NPCs and content
- Enable Magmar selection in frontend and backend
- Separate map system for Magmar vs Human races

## ✅ Item & Equipment System

A complete item catalog with 3 character classes, 4 rarities, consumables, and items spanning levels 1–5.

### Character Classes:
| Class | Weapon Type | Strengths |
|-------|------------|-----------|
| **Bonecrusher** | Two-Handed Axe | Low defense, high damage, high crit chance |
| **Skirmisher** | Sword (L) + Dagger (R) | Balanced stats, high evasion |
| **Heavyweight** | Gauntlet (L) + Shield (R) | High HP, high block, damage reduction |
| **Generalist** | Iron Spear (Lv2 only) | Basic starter gear (levels 1–2 only) |

### Equipment Slots by Level:
| Level | Available Slots |
|-------|----------------|
| 1 | Armor, Cuirass (Generalist only) |
| 2 | Weapon (Generalist only) |
| 3 | Weapon(s), Cuirass, Armor, Shirt, Boots |
| 4 | + Shoulder |
| 5 | + Helmet |

### Item Sets by Rarity:
| Color | Rarity | Bonecrusher | Skirmisher | Heavyweight |
|-------|--------|-------------|------------|-------------|
| 🟢 Green | Uncommon | Executioner | Twilight | Mammoth |
| 🔵 Blue | Rare | Anger | North Wind | Giant Slayer |
| 🟣 Purple | Epic | Mysterious Anger | Mysterious North Wind | Mysterious Giant Slayer |
| ⚪ White | Common | — | — | — (Generalist only) |

### Consumables:
- **HP Potion** — Restores 50 HP
- **Mana Potion** — Restores 30 Mana

### Inventory UI:
The inventory is divided into **6 sections** (categories):
1. 🧪 **Consumables** — Potions and usable items
2. ⚔️ **Equipment** — Weapons, armor, and accessories
3. 🐴 **Moroks & Mount** — Mount items (TODO)
4. 📋 **Quest** — Quest-related items (TODO)
5. 📦 **Other** — Miscellaneous items (TODO)
6. 🎁 **Gifts** — Gift items (TODO)

- Clicking 🎒 Inventory shows category buttons with item counts
- Clicking a category shows items in that section, color-coded by rarity
- Clicking an item opens a **proper Textual ModalScreen** overlay with full stats
- Modal has **Close**, **Delete**, and **Sell (TODO)** buttons
- Delete removes the item from the server-side inventory and refreshes the view
- Inventory **persists across sessions** — logging out and back in retains all items

### Debug: Add Item Button
- A yellow **"+ Add Item"** button in the top-right corner of the game screen
- Opens a panel listing all items from the database catalog
- Clicking an item adds it to the character's **server-side inventory**
- Items go to their correct category (equipment, consumables, etc.)
- This button is **temporary for testing** and will be removed later

### Technical Details:
- `InventoryItem` SQLAlchemy model in `inventory.py` — each row is one item instance owned by a character
- Each instance has a unique `id` (DB primary key) used as `instance_id` — prevents duplicate widget ID crashes when owning multiple copies of the same item
- Server endpoints: `GET /inventory/{email}`, `POST /inventory/add`, `POST /inventory/delete`
- `InventoryItemResponse` schema merges DB row with catalog data (name, stats, etc.)
- `ItemDetailModal` is a proper `ModalScreen` subclass with its own CSS
- Player inventory is fetched from server on every inventory open
- CSS classes for rarity colors: `.item-color-white/green/blue/purple`

## 🚧 TODO: Game Features

The following features are not yet implemented:

- **Item Equipping** — Actually equipping items to character slots
- **Item Selling** — Sell button in modal (currently disabled/TODO)
- **Hunt** — Turn-based combat with creatures, EXP and loot
- **Mailbox** — Player-to-player messaging system
- **Quests** — NPC quest acceptance, tracking, and rewards
- **NPC Interaction** — Trading, dialogue, and quest assignment with NPCs

## 🎯 Future Enhancements

### Game Features
- **Turn-based Combat System**
- **Inventory Management**
- **Quest System**
- **Character Progression**
- **Multiplayer Interactions**
- **Real-time Chat**

### Technical Improvements
- **Configuration Management** - Environment-based settings
- **Logging System** - Comprehensive application logging
- **Error Handling** - More robust error management
- **Testing Suite** - Unit and integration tests
- **Docker Support** - Containerization for easy deployment
- **Database Migrations** - Alembic integration

### UI/UX Enhancements
- **Sound Effects** - Terminal bell integration
- **Animations** - Smooth transitions and effects
- **Themes** - Multiple color schemes
- **Accessibility** - Screen reader support
- **Mobile Support** - Responsive design considerations

## 🔒 Security Considerations

### Current Security Measures
- Password hashing with bcrypt
- JWT token authentication
- Input validation and sanitization
- SQL injection prevention through SQLAlchemy
- HTTPS ready (requires SSL certificate in production)

### Production Recommendations
- Change default JWT secret key
- Implement rate limiting
- Add CORS configuration
- Use environment variables for sensitive data
- Implement proper logging and monitoring
- Add database backup strategies

## 🐛 Known Issues

### Current Limitations
- Game action buttons (Hunt, Mailbox, Quests) show TODO placeholders
- NPC interaction (trading, quests, dialogue) is TODO
- Magmar race is not yet playable (disabled in character creation)
- No actual combat mechanics implemented yet
- WebSocket functionality is basic echo
- No user session persistence
- Limited error handling in some edge cases

### Development Notes
- Database file (`dragons_legacy.db`) is created automatically
- API server must be running before starting TUI client
- All passwords are hashed and cannot be recovered (only reset)
- Security answers are case-insensitive but stored hashed

## 📊 Database Schema

### Users Table
- `id` (Primary Key)
- `email` (Unique, Indexed)
- `hashed_password`
- `is_active`
- `created_at`
- `updated_at`
- `security_question_id` (Foreign Key)
- `security_answer_hash`

### Security Questions Table
- `id` (Primary Key)
- `question_text`
- `is_active`

### Characters Table
- `id` (Primary Key)
- `user_id` (Foreign Key)
- `nickname` (Unique, max 12 chars)
- `race` (magmar / human)
- `gender` (female / male)
- `current_map` (starting map assigned by race)
- `travel_cooldown_until` (UTC timestamp, nullable — server-side cooldown)
- `level`
- `experience`
- `health`
- `mana`
- `strength`
- `dexterity`
- `intelligence`
- `created_at`
- `updated_at`

## 🎨 Design Philosophy

### User Interface
- **Simplicity** - Clean, uncluttered design
- **Accessibility** - Keyboard-friendly navigation
- **Feedback** - Clear visual feedback for all actions
- **Consistency** - Uniform styling across all screens
- **Fantasy Theme** - Dragon and medieval RPG aesthetics

### Code Architecture
- **Modularity** - Separate concerns with clear boundaries
- **Async/Await** - Non-blocking operations throughout
- **Type Hints** - Clear type annotations for maintainability
- **Documentation** - Comprehensive docstrings and comments
- **Error Handling** - Graceful degradation and user feedback

## 🏆 Achievements

This project successfully demonstrates:

1. **Full-Stack Development** - Complete backend and frontend implementation
2. **Modern Python Practices** - Async/await, type hints, modern libraries
3. **Security Implementation** - Authentication, authorization, and data protection
4. **User Experience Design** - Intuitive and beautiful terminal interface
5. **API Design** - RESTful endpoints with proper HTTP status codes
6. **Database Design** - Normalized schema with relationships
7. **Error Handling** - Comprehensive error management and user feedback
8. **Documentation** - Clear and detailed project documentation

---

**Legend of Dragon's Legacy** - *Where your adventure begins in the terminal!* 🐉⚔️