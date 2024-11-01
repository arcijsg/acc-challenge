from datetime import date, datetime, timedelta
from typing import List

import pytz

from grid_connection import GridConnection, PredictionType
from historic_consumption_service import HistoricConsumptionService
from prediction import PredictionService
from solar_forecast import SolarForecastService


def main():
    solar_forecast_service = SolarForecastService()
    historic_consumption_service = HistoricConsumptionService()

    prediction_service = PredictionService(solar_forecast_service, historic_consumption_service)

    connections = get_example_connections()

    today = date.today()
    days = [today + timedelta(days=i) for i in range(1, 3)]

    for day in days:
        for connection in connections:
            print(day, connection)
            predictions = prediction_service.make_prediction_for_day(connection, day)
            print(predictions)


def get_example_connections() -> List[GridConnection]:
    """

    Returns:
        one connection of each type
    """
    return [GridConnection('example regular connection',
                           '123456789012345678',
                           pytz.utc.localize(datetime(2020, 1, 1)),
                           pytz.utc.localize(datetime(2025, 1, 1)),
                           PredictionType.regular,
                           12324
                           ),
            GridConnection('example solar connection',
                           '234567890123456789',
                           pytz.utc.localize(datetime(2020, 1, 1)),
                           pytz.utc.localize(datetime(2025, 1, 1)),
                           PredictionType.solar,
                           -12324,
                           52.5,
                           5.5,
                           11,
                           -10,
                           987
                           ),
            GridConnection('example mixed connection',
                           '345678901234567890',
                           pytz.utc.localize(datetime(2020, 1, 1)),
                           pytz.utc.localize(datetime(2025, 1, 1)),
                           PredictionType.mixed_solar_regular,
                           101,
                           51.1,
                           4.5,
                           15,
                           45,
                           112
                           ),
            ]


if __name__ == "__main__":
    main()
