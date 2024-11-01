from datetime import datetime

from pandas import Series, date_range

from grid_connection import GridConnection


class HistoricConsumptionService:

    def __init__(self):
        pass

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def get_consumption(self, connection: GridConnection, time_start: datetime, time_end: datetime) -> Series:
        """
        Gets the historic consumption of a connection using a market & measurement platform.

        Since this is a stub, there is no check on whether data exists, and an answer is always returned.

        Args:
            connection:
            time_start:
            time_end:

        Returns:
            Consumption (kWh) values for a connection, per 15 minutes

        """
        ix_range = date_range(time_start, time_end, freq='15T')

        # data is mocked for now
        data = [ix.dayofweek + (ix.hour / 2) for ix in ix_range]

        return Series(index=ix_range, data=data)
