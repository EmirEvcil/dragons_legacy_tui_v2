"""
API client for communicating with the FastAPI backend
"""

import httpx
import asyncio
from typing import Optional, Dict, Any, List


class APIClient:
    """Client for communicating with the Dragons Legacy API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.access_token: Optional[str] = None
        
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers
    
    async def get_security_questions(self) -> List[Dict[str, Any]]:
        """Get all available security questions."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/security-questions",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
    
    async def register_user(self, email: str, password: str, 
                          security_question_id: int, security_answer: str) -> Dict[str, Any]:
        """Register a new user."""
        data = {
            "email": email,
            "password": password,
            "security_question_id": security_question_id,
            "security_answer": security_answer
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/register",
                json=data,
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
    
    async def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """Login user and get access token."""
        data = {
            "email": email,
            "password": password
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/login",
                json=data,
                headers=self._get_headers()
            )
            response.raise_for_status()
            result = response.json()
            
            # Store access token
            self.access_token = result["access_token"]
            return result
    
    async def get_user_security_question(self, email: str) -> Dict[str, Any]:
        """Get user's security question for password reset."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/user/{email}/security-question",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
    
    async def verify_security_answer(self, email: str, security_answer: str) -> Dict[str, Any]:
        """Verify security answer without resetting password."""
        data = {
            "email": email,
            "security_answer": security_answer,
            "new_password": "temp"  # Required by schema but ignored
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/verify-security-answer",
                json=data,
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def reset_password(self, email: str, security_answer: str, 
                           new_password: str) -> Dict[str, Any]:
        """Reset user password using security question."""
        data = {
            "email": email,
            "security_answer": security_answer,
            "new_password": new_password
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/reset-password",
                json=data,
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def create_character(self, email: str, nickname: str, race: str, 
                              gender: str) -> Dict[str, Any]:
        """Create a new character."""
        data = {
            "email": email,
            "nickname": nickname,
            "race": race,
            "gender": gender
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/characters",
                json=data,
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def get_character_by_email(self, email: str) -> Dict[str, Any]:
        """Get a user's character data by email."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/characters/by-email/{email}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def travel(self, email: str, destination: str) -> Dict[str, Any]:
        """Travel to an adjacent region."""
        data = {
            "email": email,
            "destination": destination
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/characters/travel",
                json=data,
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def get_region_info(self, region_name: str) -> Dict[str, Any]:
        """Get region info including connected regions."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/world/regions/{region_name}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def get_region_npcs(self, region_name: str) -> List[Dict[str, Any]]:
        """Get NPCs in a specific region."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/world/npcs/{region_name}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def get_all_items(self) -> List[Dict[str, Any]]:
        """Get the complete item catalog."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/items",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def get_inventory(self, email: str) -> List[Dict[str, Any]]:
        """Get the player's inventory from the server."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/inventory/{email}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def add_inventory_item(self, email: str, item_catalog_id: int) -> Dict[str, Any]:
        """Add an item to the player's inventory on the server."""
        data = {"email": email, "item_catalog_id": item_catalog_id}
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/inventory/add",
                json=data,
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def delete_inventory_item(self, email: str, instance_id: int) -> Dict[str, Any]:
        """Delete an item instance from the player's inventory on the server."""
        data = {"email": email, "instance_id": instance_id}
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/inventory/delete",
                json=data,
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()