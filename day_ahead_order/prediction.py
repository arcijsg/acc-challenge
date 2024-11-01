from datetime import date

from pandas import Series

from grid_connection import GridConnection
from historic_consumption_service import HistoricConsumptionService
from solar_forecast import SolarForecastService


class PredictionService:
    """
    Service for making a prediction for the hourly consumption/production of a grid connection
    """

    def __init__(self,
                 solar_forecast_service: SolarForecastService,
                 historic_consumption_service: HistoricConsumptionService):
        self.solar_forecast_service = solar_forecast_service
        self.historic_consumption_service = historic_consumption_service

    def make_prediction_for_day(self, connection: GridConnection, prediction_day: date) -> Series:
        """
        Makes a prediction for a grid connection for a specific day.

        Depending on the day, the result may contain 23, 24 or 25 values depending on Daylight Savings Time in the
        Netherlands.

        Args:
            connection:
            prediction_day:

        Returns:
            a time series containing hourly kWh values. Index datetimes are localized in UTC
        """
        # TODO implement this method for the coding challenge
        # Where applicable you can also make unit tests (in a separate file)
        pass
