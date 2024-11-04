from datetime import datetime

from pandas import Series, date_range

from grid_connection import GridConnection


class HistoricConsumptionService:
    def __init__(self):
        pass

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def get_consumption(
        self, connection: GridConnection, time_start: datetime, time_end: datetime
    ) -> Series:
        """
        Gets the historic consumption of a connection using a market & measurement platform.

        Since this is a stub, there is no check on whether data exists, and an answer is always returned.

        Args:
            connection:
            time_start: (assumed by Artūrs) beginning of first hour
                to look for historic consumption (inclusive)
            time_end: (assumed by Artūrs) end of the last hour of period
                of interest (inclusive)
                Both time_start and time_end are expected to be timezone-aware
                and express moments in the same time zone.
        Returns:
            Consumption (kWh) values for a connection, per 15 minutes
            Indexed by intervals of the same timezone as the time_start and
            time_end was in.
        """

        # NOTE: [Artūrs] as mocked data is based upon day of week and numeric hour,
        #   we would get confusing results when passing for the same time period
        #   expressed in different time zones (e.g., in CET and UTC).
        #
        # TODO: [Artūrs] replace freq="15T" with "15min"
        #  With pandas 2.2.3 results in
        #  FutureWarning: 'T' is deprecated and will be removed in a future version, please use 'min' instead.
        ix_range = date_range(time_start, time_end, freq="15T")

        # data is mocked for now
        data = [ix.dayofweek + (ix.hour / 2) for ix in ix_range]

        return Series(index=ix_range, data=data)
