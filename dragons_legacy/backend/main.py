"""
Main FastAPI application for Legend of Dragon's Legacy
"""

from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict
import json

from dragons_legacy.database import get_database, init_database
from dragons_legacy.models.user import User
from dragons_legacy.models.security_question import SecurityQuestion, PREDEFINED_SECURITY_QUESTIONS
from dragons_legacy.utils.auth import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    get_user_by_email,
    verify_security_answer
)
from dragons_legacy.models.character import Character, RACE_STARTING_MAP, Race
from dragons_legacy.models.world_data import (
    get_connected_regions,
    is_valid_travel,
    get_travel_time,
    get_npcs_for_region,
    HUMAN_MAP_GRAPH,
)
from dragons_legacy.models.item_data import get_all_items, ITEMS_BY_ID
from dragons_legacy.models.inventory import InventoryItem
from dragons_legacy.backend.schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    SecurityQuestionResponse,
    PasswordReset,
    CharacterCreate,
    CharacterResponse,
    TravelRequest,
    TravelResponse,
    RegionResponse,
    NPCResponse,
    ItemResponse,
    InventoryItemResponse,
    AddInventoryItemRequest,
    DeleteInventoryItemRequest,
)

app = FastAPI(title="Legend of Dragon's Legacy API", version="0.1.0")
security = HTTPBearer()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    await init_database()
    
    # Initialize security questions if they don't exist
    async for db in get_database():
        result = await db.execute(select(SecurityQuestion))
        existing_questions = result.scalars().all()
        
        if not existing_questions:
            for question_text in PREDEFINED_SECURITY_QUESTIONS:
                question = SecurityQuestion(question_text=question_text)
                db.add(question)
            await db.commit()
        break


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to Legend of Dragon's Legacy API"}


@app.get("/security-questions", response_model=List[SecurityQuestionResponse])
async def get_security_questions(db: AsyncSession = Depends(get_database)):
    """Get all available security questions."""
    result = await db.execute(select(SecurityQuestion).where(SecurityQuestion.is_active == True))
    questions = result.scalars().all()
    return questions


@app.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, db: AsyncSession = Depends(get_database)):
    """Register a new user."""
    # Check if user already exists
    existing_user = await get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Verify security question exists
    result = await db.execute(
        select(SecurityQuestion).where(SecurityQuestion.id == user_data.security_question_id)
    )
    security_question = result.scalar_one_or_none()
    if not security_question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid security question"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    hashed_answer = get_password_hash(user_data.security_answer.lower().strip())
    
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        security_question_id=user_data.security_question_id,
        security_answer_hash=hashed_answer
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user


@app.post("/login", response_model=Token)
async def login_user(user_data: UserLogin, db: AsyncSession = Depends(get_database)):
    """Authenticate user and return access token."""
    user = await authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user already has a character
    result = await db.execute(
        select(Character).where(Character.user_id == user.id)
    )
    character = result.scalar_one_or_none()
    
    access_token = create_access_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "has_character": character is not None
    }


@app.post("/verify-security-answer")
async def verify_security_answer_endpoint(reset_data: PasswordReset, db: AsyncSession = Depends(get_database)):
    """Verify security answer without resetting password."""
    user = await get_user_by_email(db, reset_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify security answer
    if not await verify_security_answer(user, reset_data.security_answer):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect security answer"
        )
    
    return {"message": "Security answer verified"}


@app.post("/reset-password")
async def reset_password(reset_data: PasswordReset, db: AsyncSession = Depends(get_database)):
    """Reset user password using security question."""
    user = await get_user_by_email(db, reset_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify security answer
    if not await verify_security_answer(user, reset_data.security_answer):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect security answer"
        )
    
    # Update password
    user.hashed_password = get_password_hash(reset_data.new_password)
    await db.commit()
    
    return {"message": "Password reset successfully"}


@app.get("/user/{email}/security-question")
async def get_user_security_question(email: str, db: AsyncSession = Depends(get_database)):
    """Get user's security question for password reset."""
    from sqlalchemy.orm import selectinload
    
    # Load user with security question relationship
    result = await db.execute(
        select(User).options(selectinload(User.security_question)).where(User.email == email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.security_question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No security question set for this user"
        )
    
    return {"question": user.security_question.question_text}


@app.post("/characters", response_model=CharacterResponse)
async def create_character(character_data: CharacterCreate, db: AsyncSession = Depends(get_database)):
    """Create a new character for a user."""
    # Look up the user by email
    user = await get_user_by_email(db, character_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if user already has a character
    result = await db.execute(
        select(Character).where(Character.user_id == user.id)
    )
    existing_for_user = result.scalar_one_or_none()
    if existing_for_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has a character"
        )
    
    # Check if nickname is already taken
    result = await db.execute(
        select(Character).where(Character.nickname == character_data.nickname)
    )
    existing_character = result.scalar_one_or_none()
    if existing_character:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nickname already taken"
        )
    
    # Determine starting map based on race
    race_enum = Race(character_data.race)
    starting_map = RACE_STARTING_MAP.get(race_enum, "Settlement of Klesva")
    
    # Create the character with the correct user_id
    new_character = Character(
        user_id=user.id,
        nickname=character_data.nickname,
        race=character_data.race,
        gender=character_data.gender,
        current_map=starting_map
    )
    
    db.add(new_character)
    await db.commit()
    await db.refresh(new_character)
    
    return new_character


@app.get("/characters/by-email/{email}", response_model=CharacterResponse)
async def get_character_by_email(email: str, db: AsyncSession = Depends(get_database)):
    """Get a user's character by their email address."""
    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    result = await db.execute(
        select(Character).where(Character.user_id == user.id)
    )
    character = result.scalar_one_or_none()
    
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )
    
    return character


@app.post("/characters/travel", response_model=TravelResponse)
async def travel_character(travel_data: TravelRequest, db: AsyncSession = Depends(get_database)):
    """Move a character to an adjacent region (instant move, server-side cooldown)."""
    from datetime import datetime as dt, timezone as tz, timedelta

    user = await get_user_by_email(db, travel_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    result = await db.execute(
        select(Character).where(Character.user_id == user.id)
    )
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )
    
    # --- Server-side cooldown enforcement ---
    if character.cooldown_remaining > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Travel cooldown active. "
                   + str(character.cooldown_remaining)
                   + "s remaining before you can travel again."
        )
    
    # Validate travel is allowed (adjacent region)
    if not is_valid_travel(character.current_map, travel_data.destination):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot travel from '"
                   + character.current_map
                   + "' to '"
                   + travel_data.destination
                   + "'. Regions are not connected."
        )
    
    # Calculate cooldown duration
    cooldown_seconds = get_travel_time(character.level)
    
    # Move immediately + set cooldown
    old_map = character.current_map
    character.current_map = travel_data.destination
    character.travel_cooldown_until = dt.now(tz.utc) + timedelta(seconds=cooldown_seconds)
    await db.commit()
    await db.refresh(character)
    
    return {
        "message": "Arrived at " + travel_data.destination + " from " + old_map,
        "destination": travel_data.destination,
        "cooldown_seconds": cooldown_seconds,
        "cooldown_remaining": character.cooldown_remaining,
        "current_map": character.current_map,
    }


@app.get("/world/regions/{region_name}", response_model=RegionResponse)
async def get_region_info(region_name: str):
    """Get region info including connected regions."""
    connected = get_connected_regions(region_name)
    if not connected and region_name not in HUMAN_MAP_GRAPH:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Region '{region_name}' not found"
        )
    return {"name": region_name, "connected_regions": connected}


@app.get("/world/npcs/{region_name}", response_model=List[NPCResponse])
async def get_region_npcs(region_name: str):
    """Get NPCs in a specific region."""
    if region_name not in HUMAN_MAP_GRAPH:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Region '{region_name}' not found"
        )
    return get_npcs_for_region(region_name)


@app.get("/items", response_model=List[ItemResponse])
async def list_all_items():
    """Return the complete item catalog."""
    return get_all_items()


def _merge_inventory_row(row: InventoryItem) -> dict:
    """Merge a DB inventory row with its catalog data."""
    catalog = ITEMS_BY_ID.get(row.item_catalog_id, {})
    return {
        "instance_id": row.id,
        "item_catalog_id": row.item_catalog_id,
        "quantity": row.quantity,
        "name": catalog.get("name", "Unknown"),
        "slot": catalog.get("slot", ""),
        "required_level": catalog.get("required_level", 0),
        "character_class": catalog.get("character_class", ""),
        "rarity": catalog.get("rarity", "common"),
        "color": catalog.get("color", "white"),
        "inventory_category": catalog.get("inventory_category", "other"),
        "damage": catalog.get("damage", 0),
        "defense": catalog.get("defense", 0),
        "hp_bonus": catalog.get("hp_bonus", 0),
        "mana_bonus": catalog.get("mana_bonus", 0),
        "crit_chance": catalog.get("crit_chance", 0),
        "evasion": catalog.get("evasion", 0),
        "block_chance": catalog.get("block_chance", 0),
        "damage_reduction": catalog.get("damage_reduction", 0),
        "description": catalog.get("description", ""),
    }


@app.get("/inventory/{email}", response_model=List[InventoryItemResponse])
async def get_inventory(email: str, db: AsyncSession = Depends(get_database)):
    """Get all inventory items for a character by email."""
    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    result = await db.execute(select(Character).where(Character.user_id == user.id))
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    result = await db.execute(
        select(InventoryItem).where(InventoryItem.character_id == character.id)
    )
    rows = result.scalars().all()
    return [_merge_inventory_row(r) for r in rows]


@app.post("/inventory/add", response_model=InventoryItemResponse)
async def add_inventory_item(req: AddInventoryItemRequest, db: AsyncSession = Depends(get_database)):
    """Add an item to a character's inventory."""
    if req.item_catalog_id not in ITEMS_BY_ID:
        raise HTTPException(status_code=400, detail="Invalid item catalog ID")

    user = await get_user_by_email(db, req.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    result = await db.execute(select(Character).where(Character.user_id == user.id))
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    new_row = InventoryItem(
        character_id=character.id,
        item_catalog_id=req.item_catalog_id,
        quantity=1,
    )
    db.add(new_row)
    await db.commit()
    await db.refresh(new_row)
    return _merge_inventory_row(new_row)


@app.post("/inventory/delete")
async def delete_inventory_item(req: DeleteInventoryItemRequest, db: AsyncSession = Depends(get_database)):
    """Delete an item instance from a character's inventory."""
    user = await get_user_by_email(db, req.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    result = await db.execute(select(Character).where(Character.user_id == user.id))
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    result = await db.execute(
        select(InventoryItem).where(
            InventoryItem.id == req.instance_id,
            InventoryItem.character_id == character.id,
        )
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Item not found in inventory")

    await db.delete(row)
    await db.commit()
    return {"message": "Item deleted"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time game communication."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Echo message back for now (will implement game logic later)
            await manager.send_personal_message(
                json.dumps({"type": "echo", "data": message_data}),
                websocket
            )
    except WebSocketDisconnect:
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)