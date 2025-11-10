"""BlueprintEntity class."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION
from .coordinator import APRSWSDataUpdateCoordinator

if TYPE_CHECKING:
    from homeassistant.helpers.entity import EntityDescription


class APRSWSEntity(CoordinatorEntity[APRSWSDataUpdateCoordinator]):
    """APRSWSEntity class."""

    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        coordinator: APRSWSDataUpdateCoordinator,
        entity_description: EntityDescription,
        device_id: str,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_unique_id = entity_description.key
        self._attr_device_info = DeviceInfo(
            identifiers={
                (
                    coordinator.config_entry.domain,
                    device_id,
                ),
            },
        )
