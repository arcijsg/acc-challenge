from datetime import date
from enum import Enum
from typing import Optional


class PredictionType(Enum):
    regular = 1
    solar = 2
    mixed_solar_regular = 3


class GridConnection:
    """
    Model class for a single (EAN) connection to the grid.
    """

    def __init__(self, name: str,
                 ean_code: str,
                 active_from: date,
                 active_until: date,
                 prediction_type: PredictionType,
                 standard_yearly_consumption: float,
                 latitude: Optional[float] = None,
                 longitude: Optional[float] = None,
                 solar_plane_declination: Optional[float] = None,
                 solar_plane_azimuth: Optional[float] = None,
                 solar_rated_power: Optional[float] = None):
        """

        Args:
            name:
            ean_code: EAN (registration) number
            active_from: (inclusive) First date for which orders should be made
            active_until: Marks the first date for which orders shouldn't be sent anymore
            prediction_type:
            standard_yearly_consumption: kWh used/produced by this connection per year
            latitude: (degrees) of physical location
            longitude: (degrees) of physical location
            solar_plane_declination: (degrees) of solar installation
            solar_plane_azimuth: (degrees) of solar installation
            solar_rated_power: (kWp) of solar installation
        """
        self.name = name
        self.ean_code = ean_code
        self.active_from = active_from
        self.active_until = active_until
        self.prediction_type = prediction_type
        self.standard_yearly_consumption = standard_yearly_consumption
        self.latitude = latitude
        self.longitude = longitude
        self.solar_plane_declination = solar_plane_declination
        self.solar_plane_azimuth = solar_plane_azimuth
        self.solar_rated_power = solar_rated_power
