"""
Game screen for Legend of Dragon's Legacy
"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal, VerticalScroll
from textual.screen import Screen, ModalScreen
from textual.widgets import Button, Static

from dragons_legacy.frontend.api_client import APIClient

# Inventory category display names (keep in sync with item_data.py)
_CAT_DISPLAY = {
    "consumables": "🧪 Consumables",
    "equipment": "⚔️ Equipment",
    "moroks_mount": "🐴 Moroks & Mount",
    "quest": "📋 Quest",
    "other": "📦 Other",
    "gifts": "🎁 Gifts",
}

_CAT_ORDER = ["consumables", "equipment", "moroks_mount", "quest", "other", "gifts"]


def _sanitize_id(text: str) -> str:
    """Turn a display name into a safe widget-id fragment (no quotes, no spaces)."""
    return text.replace(" ", "_").replace("'", "")


# ============================================================
# Item Detail Modal (proper Textual ModalScreen)
# ============================================================

class ItemDetailModal(ModalScreen):
    """A true modal overlay showing item details with Close/Delete/Sell."""

    CSS = """
    ItemDetailModal {
        align: center middle;
    }
    #modal-dialog {
        width: 60;
        max-height: 80%;
        border: solid $accent;
        background: $surface;
        padding: 2;
    }
    #modal-title {
        text-style: bold;
        color: $accent;
        text-align: center;
        margin-bottom: 1;
    }
    #modal-body {
        color: $text;
        margin: 1 0;
        width: 100%;
    }
    .modal-btn-row {
        layout: horizontal;
        height: auto;
        width: 100%;
        margin-top: 1;
    }
    .modal-btn-row Button {
        width: 1fr;
        margin: 0 1;
    }
    """

    def __init__(self, item: dict):
        super().__init__()
        self.item = item

    def compose(self) -> ComposeResult:
        item = self.item
        slot_display = (
            item.get("slot", "")
            .replace("weapon_left", "Left Hand")
            .replace("weapon_right", "Right Hand")
            .replace("consumable", "Consumable")
            .capitalize()
        )

        lines = [
            "Rarity: " + item.get("rarity", "").capitalize(),
            "Class: " + item.get("character_class", ""),
            "Slot: " + slot_display,
            "Required Level: " + str(item.get("required_level", 0)),
            "",
        ]

        stat_map = [
            ("damage", "⚔️  Damage"),
            ("defense", "🛡️  Defense"),
            ("hp_bonus", "❤️  HP Bonus"),
            ("mana_bonus", "💧 Mana Bonus"),
            ("crit_chance", "💥 Crit Chance"),
            ("evasion", "💨 Evasion"),
            ("block_chance", "🔰 Block Chance"),
            ("damage_reduction", "🪨 Damage Reduction"),
        ]
        for key, label in stat_map:
            val = item.get(key, 0)
            if val:
                suffix = "%" if key in ("crit_chance", "evasion", "block_chance", "damage_reduction") else ""
                lines.append(label + ": " + str(val) + suffix)

        if item.get("description"):
            lines.append("")
            lines.append(item["description"])

        with Container(id="modal-dialog"):
            yield Static("🎒 " + item.get("name", "Unknown"), id="modal-title")
            yield Static("\n".join(lines), id="modal-body")
            with Horizontal(classes="modal-btn-row"):
                yield Button("Close", variant="default", id="modal_close")
                yield Button("Delete", variant="error", id="modal_delete")
                yield Button("Sell (TODO)", variant="default", id="modal_sell", disabled=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "modal_close":
            self.dismiss(None)
        elif event.button.id == "modal_delete":
            self.dismiss("delete")
        elif event.button.id == "modal_sell":
            pass  # TODO


class GameScreen(Screen):
    """Main game screen with character HUD and action menu."""

    CSS_PATH = None  # Will use main CSS

    def __init__(self, api_client: APIClient):
        super().__init__()
        self.api_client = api_client
        self.character_data = None
        # Cooldown display state — seeded from server, ticked locally for display
        self._cooldown_remaining: int = 0
        self._cooldown_timer = None
        self._current_npcs: dict = {}
        # Server-side inventory (list of InventoryItemResponse dicts with instance_id)
        self._player_inventory: list[dict] = []
        # Cache of all catalog items (for debug add-item)
        self._all_items_cache: list[dict] = []

    def compose(self) -> ComposeResult:
        """Compose the game screen."""
        with Container(classes="game-layout"):
            # Top bar: map name + debug button
            with Horizontal(classes="game-top-bar"):
                yield Static("📍 Loading...", id="map_name", classes="game-map-name")
                yield Button("+ Add Item", variant="default", id="btn_debug_add", classes="debug-add-btn")

            # Main content area
            with Horizontal(classes="game-main"):
                # Left panel: character stats
                with Vertical(classes="game-stats-panel"):
                    yield Static("⚔️ CHARACTER", classes="game-panel-title")
                    yield Static("", id="char_nickname", classes="game-stat-name")
                    yield Static("", id="char_race_gender", classes="game-stat-detail")
                    yield Static("", classes="game-stat-separator")
                    yield Static("", id="char_level", classes="game-stat")
                    yield Static("", id="char_exp", classes="game-stat")
                    yield Static("", id="char_hp", classes="game-stat-hp")
                    yield Static("", id="char_mana", classes="game-stat-mana")
                    yield Static("", classes="game-stat-separator")
                    yield Static("", id="char_cooldown", classes="game-stat-cooldown")

                # Center: main game area — dynamic content
                with Vertical(classes="game-center-panel"):
                    yield Static(
                        "🐉 LEGEND OF DRAGON'S LEGACY 🐉",
                        classes="game-center-title",
                    )
                    with VerticalScroll(classes="game-center-content"):
                        yield Static("", id="game_area_text", classes="game-area-text")
                        # Dynamic buttons / content mounted here at runtime
                        yield Vertical(id="dynamic_area")

                # Right panel: action menu
                with Vertical(classes="game-action-panel"):
                    yield Static("📜 ACTIONS", classes="game-panel-title")
                    yield Button("🎒 Inventory", variant="default", id="btn_inventory", classes="game-action-btn")
                    yield Button("📍 Location", variant="default", id="btn_location", classes="game-action-btn")
                    yield Button("⚔️ Hunt", variant="default", id="btn_hunt", classes="game-action-btn")
                    yield Button("📬 Mailbox", variant="default", id="btn_mailbox", classes="game-action-btn")
                    yield Button("📋 Quests", variant="default", id="btn_quests", classes="game-action-btn")
                    yield Button("🧙 NPC List", variant="default", id="btn_npc", classes="game-action-btn")

            # Bottom bar
            with Horizontal(classes="game-bottom-bar"):
                yield Button("Logout", variant="default", id="back_btn", classes="game-logout-btn")

    # ----------------------------------------------------------
    # Lifecycle
    # ----------------------------------------------------------

    async def on_show(self) -> None:
        """Load character data when screen is shown."""
        await self.load_character_data()

    async def load_character_data(self) -> None:
        """Fetch and display character data from the API."""
        try:
            email = self.app.user_email
            if not email:
                self._show_text("⚠️ No user session found. Please log in again.")
                return
            self.character_data = await self.api_client.get_character_by_email(email)
            # Seed cooldown from server-authoritative value
            self._start_cooldown_display(self.character_data.get("cooldown_remaining", 0))
            self._update_hud()
        except Exception:
            self._show_text(
                "⚠️ Failed to load character data.\n"
                "Please try logging in again."
            )

    # ----------------------------------------------------------
    # HUD helpers
    # ----------------------------------------------------------

    def _update_hud(self) -> None:
        """Update all HUD elements with character data."""
        if not self.character_data:
            return
        data = self.character_data

        current_map = data["current_map"]
        nickname = data["nickname"]
        race_display = data["race"].capitalize()
        gender_display = data["gender"].capitalize()

        self.query_one("#map_name", Static).update("📍 " + current_map)
        self.query_one("#char_nickname", Static).update("🛡️ " + nickname)
        self.query_one("#char_race_gender", Static).update(
            race_display + " • " + gender_display
        )
        self.query_one("#char_level", Static).update("⭐ Level: " + str(data["level"]))
        self.query_one("#char_exp", Static).update("✨ EXP: " + str(data["experience"]))
        hp = str(data["health"])
        mana = str(data["mana"])
        self.query_one("#char_hp", Static).update("❤️  HP: " + hp + " / " + hp)
        self.query_one("#char_mana", Static).update("💧 Mana: " + mana + " / " + mana)
        self._update_cooldown_display()

        self._clear_dynamic()
        self._show_text(
            "Welcome to " + current_map + ", " + nickname + "!\n\n"
            "You stand at the heart of the settlement.\n"
            "Use the action menu on the right to explore."
        )

    def _update_cooldown_display(self) -> None:
        """Update the cooldown line in the left stats panel."""
        widget = self.query_one("#char_cooldown", Static)
        if self._cooldown_remaining > 0:
            widget.update("⏳ Cooldown: " + str(self._cooldown_remaining) + "s")
        else:
            widget.update("")

    def _start_cooldown_display(self, seconds: int) -> None:
        """Start (or restart) the local cooldown display timer from a server value."""
        # Stop any existing timer
        if self._cooldown_timer is not None:
            self._cooldown_timer.stop()
            self._cooldown_timer = None

        self._cooldown_remaining = max(0, seconds)
        self._update_cooldown_display()

        if self._cooldown_remaining > 0:
            self._cooldown_timer = self.set_interval(1.0, self._tick_cooldown)

    # ----------------------------------------------------------
    # Center panel helpers
    # ----------------------------------------------------------

    def _show_text(self, message: str) -> None:
        """Show a text message in the center panel."""
        self.query_one("#game_area_text", Static).update(message)

    def _clear_dynamic(self) -> None:
        """Remove all dynamically-mounted widgets from #dynamic_area."""
        container = self.query_one("#dynamic_area", Vertical)
        container.remove_children()

    def _mount_dynamic(self, *widgets) -> None:
        """Mount widgets into the dynamic area."""
        self._clear_dynamic()
        container = self.query_one("#dynamic_area", Vertical)
        container.mount_all(widgets)

    # ----------------------------------------------------------
    # Location panel
    # ----------------------------------------------------------

    async def _show_location(self) -> None:
        """Show current location and connected regions as travel buttons."""
        if not self.character_data:
            return

        current = self.character_data["current_map"]

        try:
            region_info = await self.api_client.get_region_info(current)
            connected = region_info.get("connected_regions", [])
        except Exception:
            connected = []

        if self._cooldown_remaining > 0:
            header = (
                "📍 LOCATION: " + current + "\n\n"
                "⏳ Travel cooldown active: " + str(self._cooldown_remaining) + "s remaining\n\n"
                "Accessible regions:"
            )
        else:
            header = (
                "📍 LOCATION: " + current + "\n\n"
                "Accessible regions:"
            )

        self._show_text(header)

        buttons = []
        for region in connected:
            btn_id = "travel_" + _sanitize_id(region)
            btn = Button(
                "🚶 Travel to " + region,
                variant="default",
                id=btn_id,
                classes="game-travel-btn",
            )
            buttons.append(btn)

        if not buttons:
            buttons.append(Static("No connected regions.", classes="game-area-text"))

        self._mount_dynamic(*buttons)

    # ----------------------------------------------------------
    # NPC list panel
    # ----------------------------------------------------------

    async def _show_npc_list(self) -> None:
        """Show NPCs in the current region."""
        if not self.character_data:
            return

        current = self.character_data["current_map"]

        try:
            npcs = await self.api_client.get_region_npcs(current)
        except Exception:
            npcs = []

        if not npcs:
            self._show_text(
                "🧙 NPCs in " + current + "\n\nNo NPCs found in this region."
            )
            self._clear_dynamic()
            return

        self._show_text("🧙 NPCs in " + current + "\n")

        widgets = []
        for npc in npcs:
            npc_name = npc["name"]
            npc_role = npc["role"]
            btn_id = "npc_" + _sanitize_id(npc_name)
            btn = Button(
                npc_name + " — " + npc_role,
                variant="default",
                id=btn_id,
                classes="game-npc-btn",
            )
            widgets.append(btn)

        self._mount_dynamic(*widgets)
        # Store NPC data for interaction look-ups
        self._current_npcs = {npc["name"]: npc for npc in npcs}

    # ----------------------------------------------------------
    # Inventory panel (sectioned, server-side)
    # ----------------------------------------------------------

    async def _load_inventory_from_server(self) -> None:
        """Fetch inventory from the server."""
        try:
            email = self.app.user_email
            if email:
                self._player_inventory = await self.api_client.get_inventory(email)
        except Exception:
            pass  # keep whatever we had

    async def _show_inventory(self) -> None:
        """Show inventory category buttons."""
        await self._load_inventory_from_server()
        self._show_text("🎒 INVENTORY\n\nSelect a category:")

        buttons = []
        for cat_key in _CAT_ORDER:
            cat_label = _CAT_DISPLAY.get(cat_key, cat_key)
            count = sum(1 for i in self._player_inventory if i.get("inventory_category") == cat_key)
            label = cat_label + " (" + str(count) + ")"
            btn = Button(
                label,
                variant="default",
                id="invcat_" + cat_key,
                classes="game-action-btn",
            )
            buttons.append(btn)

        self._mount_dynamic(*buttons)

    def _show_inventory_category(self, category: str) -> None:
        """Show items in a specific inventory category."""
        cat_label = _CAT_DISPLAY.get(category, category)
        items = [i for i in self._player_inventory if i.get("inventory_category") == category]

        if not items:
            self._show_text("🎒 " + cat_label + "\n\nNo items in this category.")
            widgets = [
                Button("← Back to Inventory", variant="default", id="btn_inv_back", classes="game-action-btn")
            ]
            self._mount_dynamic(*widgets)
            return

        self._show_text("🎒 " + cat_label + "\n")

        rarity_order = {"common": 0, "uncommon": 1, "rare": 2, "epic": 3}
        items_sorted = sorted(
            items,
            key=lambda i: (rarity_order.get(i.get("rarity", "common"), 0), i.get("required_level", 0), i.get("name", "")),
        )

        widgets = []
        widgets.append(
            Button("← Back to Inventory", variant="default", id="btn_inv_back", classes="game-action-btn")
        )
        for item in items_sorted:
            color = item.get("color", "white")
            slot_short = (
                item.get("slot", "")
                .replace("weapon_left", "L.Hand")
                .replace("weapon_right", "R.Hand")
                .replace("consumable", "Use")
                .capitalize()
            )
            label = (
                "[Lv" + str(item.get("required_level", 0)) + "] "
                + item.get("name", "Unknown")
                + " (" + slot_short + ")"
            )
            # Use instance_id (unique DB PK) — never duplicates
            inst_id = item.get("instance_id", 0)
            btn = Button(
                label,
                variant="default",
                id="invitem_" + str(inst_id),
                classes="game-item-btn item-color-" + color,
            )
            widgets.append(btn)

        self._mount_dynamic(*widgets)

    def _open_item_modal(self, item: dict) -> None:
        """Open a proper Textual modal for item detail."""
        def on_modal_result(result) -> None:
            if result == "delete":
                self._delete_item_from_inventory(item)
        self.app.push_screen(ItemDetailModal(item), callback=on_modal_result)

    def _delete_item_from_inventory(self, item: dict) -> None:
        """Delete an item instance from the server and refresh."""
        inst_id = item.get("instance_id")
        if not inst_id:
            return

        async def _do_delete():
            try:
                email = self.app.user_email
                await self.api_client.delete_inventory_item(email, inst_id)
                self.app.show_toast("🗑️ Deleted: " + item.get("name", "Unknown"), severity="information")
                # Refresh the category view
                cat = item.get("inventory_category", "equipment")
                await self._load_inventory_from_server()
                self._show_inventory_category(cat)
            except Exception:
                self.app.show_toast("⚠️ Failed to delete item.", severity="warning")

        self.run_worker(_do_delete())

    # ----------------------------------------------------------
    # Debug: Add Item panel
    # ----------------------------------------------------------

    async def _show_debug_add_item(self) -> None:
        """Show all catalog items so the user can add them to inventory (server-side)."""
        if not self._all_items_cache:
            try:
                self._all_items_cache = await self.api_client.get_all_items()
            except Exception:
                self._all_items_cache = []

        if not self._all_items_cache:
            self._show_text("⚠️ Could not load item catalog.")
            self._clear_dynamic()
            return

        self._show_text("🛠️ DEBUG: Add Item to Inventory\n\nClick an item to add it.\n")

        rarity_order = {"common": 0, "uncommon": 1, "rare": 2, "epic": 3}
        items_sorted = sorted(
            self._all_items_cache,
            key=lambda i: (
                i["character_class"],
                rarity_order.get(i["rarity"], 0),
                i["required_level"],
                i["slot"],
            ),
        )

        widgets = []
        current_group = ""
        for item in items_sorted:
            group_key = item["character_class"] + " — " + item["rarity"].capitalize()
            if group_key != current_group:
                current_group = group_key
                color = item["color"]
                widgets.append(Static(
                    "── " + group_key + " ──",
                    classes="item-group-header item-color-" + color,
                ))

            color = item["color"]
            slot_short = (
                item["slot"]
                .replace("weapon_left", "L.Hand")
                .replace("weapon_right", "R.Hand")
                .replace("consumable", "Use")
                .capitalize()
            )
            label = (
                "[Lv" + str(item["required_level"]) + "] "
                + item["name"]
                + " (" + slot_short + ")"
            )
            btn = Button(
                label,
                variant="default",
                id="dbgadd_" + str(item["id"]),
                classes="game-item-btn item-color-" + color,
            )
            widgets.append(btn)

        self._mount_dynamic(*widgets)

    async def _debug_add_item_to_inventory(self, item_catalog_id: str) -> None:
        """Add an item to inventory via the server."""
        try:
            email = self.app.user_email
            result = await self.api_client.add_inventory_item(email, int(item_catalog_id))
            cat = _CAT_DISPLAY.get(result.get("inventory_category", "other"), "Inventory")
            self.app.show_toast(
                "✅ Added: " + result.get("name", "Unknown") + " → " + cat,
                severity="information",
            )
        except Exception:
            self.app.show_toast("⚠️ Failed to add item.", severity="warning")

    # ----------------------------------------------------------
    # Travel + cooldown logic (server-authoritative)
    # ----------------------------------------------------------

    async def _initiate_travel(self, destination: str) -> None:
        """Travel immediately via the server; cooldown is enforced server-side."""
        # The server will reject if cooldown is still active, but we can
        # give instant client feedback too.
        if self._cooldown_remaining > 0:
            self._clear_dynamic()
            self._show_text(
                "⏳ Travel cooldown active!\n\n"
                "You must wait " + str(self._cooldown_remaining) + "s before traveling again."
            )
            return

        # Ask the server to travel (it enforces the cooldown authoritatively)
        try:
            result = await self.api_client.travel(
                email=self.app.user_email,
                destination=destination,
            )
        except Exception as e:
            error_str = str(e).lower()
            if "cooldown" in error_str:
                # Server rejected — extract remaining seconds from error
                self._show_text(
                    "⏳ Travel cooldown active!\n\n"
                    "The server says you must wait before traveling again."
                )
            elif "not connected" in error_str:
                self._show_text("❌ Cannot travel there — regions are not connected.")
            else:
                self._show_text("❌ Travel failed. Please try again.")
            self._clear_dynamic()
            return

        # --- Arrived immediately (server confirmed) ---
        cooldown_seconds = result["cooldown_seconds"]
        self.character_data["current_map"] = result["current_map"]

        # Update top bar right away
        self.query_one("#map_name", Static).update("📍 " + destination)

        self.app.show_toast("📍 Arrived at " + destination + "!", severity="information")

        # Start cooldown display from server value
        self._start_cooldown_display(result["cooldown_remaining"])

        self._clear_dynamic()
        self._show_text(
            "✅ You have arrived at " + destination + "!\n\n"
            "⏳ Travel cooldown: " + str(cooldown_seconds) + "s\n"
            "You can explore this area, but cannot travel\n"
            "to another region until the cooldown expires."
        )

    def _tick_cooldown(self) -> None:
        """Called every second to decrement the local cooldown display."""
        self._cooldown_remaining = max(0, self._cooldown_remaining - 1)
        self._update_cooldown_display()

        if self._cooldown_remaining <= 0:
            if self._cooldown_timer is not None:
                self._cooldown_timer.stop()
                self._cooldown_timer = None
            self.app.show_toast("✅ Travel cooldown expired — you may travel again!", severity="information")

    # ----------------------------------------------------------
    # Button handler
    # ----------------------------------------------------------

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        # --- Logout ---
        if button_id == "back_btn":
            if self._cooldown_timer is not None:
                self._cooldown_timer.stop()
                self._cooldown_timer = None
            self._cooldown_remaining = 0
            while len(self.app.screen_stack) > 1:
                self.app.pop_screen()
            if not any(screen.name == "login" for screen in self.app.screen_stack):
                self.app.push_screen("login")
            login_screen = self.app.get_screen("login")
            if hasattr(login_screen, "clear_inputs"):
                login_screen.clear_inputs()
            return

        # --- Action buttons ---
        if button_id == "btn_inventory":
            await self._show_inventory()

        elif button_id == "btn_inv_back":
            await self._show_inventory()

        elif button_id == "btn_location":
            await self._show_location()

        elif button_id == "btn_hunt":
            self._clear_dynamic()
            self._show_text(
                "⚔️ HUNT\n\n"
                "🚧 Coming Soon 🚧\n\n"
                "Venture into the wild to battle creatures,\n"
                "earn experience, and collect loot."
            )

        elif button_id == "btn_mailbox":
            self._clear_dynamic()
            self._show_text(
                "📬 MAILBOX\n\n"
                "🚧 Coming Soon 🚧\n\n"
                "Send and receive messages from other\n"
                "adventurers in the realm."
            )

        elif button_id == "btn_quests":
            self._clear_dynamic()
            self._show_text(
                "📋 QUESTS\n\n"
                "🚧 Coming Soon 🚧\n\n"
                "Accept quests from NPCs, track your\n"
                "progress, and claim rewards."
            )

        elif button_id == "btn_npc":
            await self._show_npc_list()

        elif button_id == "btn_debug_add":
            await self._show_debug_add_item()

        # --- Inventory category buttons (invcat_<category>) ---
        elif button_id.startswith("invcat_"):
            cat = button_id[len("invcat_"):]
            self._show_inventory_category(cat)

        # --- Inventory item buttons (invitem_<instance_id>) — open real modal ---
        elif button_id.startswith("invitem_"):
            raw = button_id[len("invitem_"):]
            for itm in self._player_inventory:
                if str(itm.get("instance_id")) == raw:
                    self._open_item_modal(itm)
                    break

        # --- Debug add item buttons (dbgadd_<catalog_id>) ---
        elif button_id.startswith("dbgadd_"):
            raw = button_id[len("dbgadd_"):]
            await self._debug_add_item_to_inventory(raw)

        # --- Dynamic travel buttons (id starts with "travel_") ---
        elif button_id.startswith("travel_"):
            raw = button_id[len("travel_"):]
            if self.character_data:
                current_map = self.character_data["current_map"]
                try:
                    region_info = await self.api_client.get_region_info(current_map)
                    connected = region_info.get("connected_regions", [])
                    for region in connected:
                        if _sanitize_id(region) == raw:
                            await self._initiate_travel(region)
                            return
                except Exception:
                    pass
            self._show_text("❌ Travel failed. Please try again.")
            self._clear_dynamic()

        # --- Dynamic NPC buttons (id starts with "npc_") ---
        elif button_id.startswith("npc_"):
            raw = button_id[len("npc_"):]
            npc_data = None
            for name, data in self._current_npcs.items():
                if _sanitize_id(name) == raw:
                    npc_data = data
                    break
            if npc_data:
                npc_name = npc_data["name"]
                npc_role = npc_data["role"]
                npc_desc = npc_data["description"]
                self._clear_dynamic()
                self._show_text(
                    "🧙 " + npc_name + "\n"
                    "Role: " + npc_role + "\n\n"
                    + npc_desc + "\n\n"
                    "🚧 Interaction Coming Soon 🚧\n\n"
                    "Trading, quests, and dialogue will\n"
                    "be available in a future update."
                )
            else:
                self._clear_dynamic()
                self._show_text("🧙 NPC not found.")