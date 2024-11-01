from datetime import datetime

from pandas import Series, date_range


class SolarForecastService:
    """
    Service for obtaining solar (PV) forecasts. Can be used on future and historic ranges.
    """

    def __init__(self):
        pass

    # noinspection PyUnusedLocal,PyMethodMayBeStatic
    def predict(self,
                time_start: datetime,
                time_end: datetime,
                latitude: float,
                longitude: float,
                plane_declination: float,
                plane_azimuth: float,
                solar_rated_power: float) -> Series:
        """
        Gets prediction for a specified connection and time range. Time range can be in the future and in the past.

        The result is a time series with kWh values, per 60 minutes.

        Args:
            time_start: (inclusive, UTC) marks the start of the first hour in the range
            time_end: (exclusive, UTC) marks the end of the last hour in the range
            latitude: see GridConnection
            longitude: see GridConnection
            plane_declination: see GridConnection
            plane_azimuth: see GridConnection
            solar_rated_power: see GridConnection

        Returns:

        """
        ix_range = date_range(time_start, time_end, freq='60T')

        # data is mocked for now
        data = [ix.hour for ix in ix_range]

        return Series(index=ix_range, data=data)
