from datetime import date

from pandas import Series

from grid_connection import GridConnection
from historic_consumption_service import HistoricConsumptionService
from solar_forecast import SolarForecastService


class PredictionService:
    """
    Service for making a prediction for the hourly consumption/production of a grid connection
    """

    def __init__(
        self,
        solar_forecast_service: SolarForecastService,
        historic_consumption_service: HistoricConsumptionService,
    ):
        self.solar_forecast_service = solar_forecast_service
        self.historic_consumption_service = historic_consumption_service

    def make_prediction_for_day(
        self, connection: GridConnection, prediction_day: date
    ) -> Series:
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

        # Rough first thoughts:
        # ---------------------

        # >>> [API contract] preconditions & args:
        #
        # prediction_day:
        # - a naive datetime - assume to be a calendar day in Europe/Amsterdam tzone (CET or CEST)?
        #
        if prediction_day < date.today():
            # TODO: allow to cross-check predictions with past consumption records?
            #   -> yes: assert prediction_day falls within self.connection [active_from; active_until] date range
            #   -> no: raise ValueError("Prediction day should be in future")
            #)
            pass

        if prediction_day == date.today():
            # TODO: allow partial predictions? It would kind of make sense...
            #   -> yes:
            #      - fill hours already passed with historical data (for regular; available for solar connections?)
            #      - predict future hours using:
            #        - regular consumer: partial datetime range (just hours still to come today) for efficiency?
            #   -> no: raise ValueError("Prediction day should be in future")
            pass

        if not self.connection.is_active_on(prediction_day):
            # TODO: would it make sense to offer consumption predictions outside
            #   of contract period for the consumer?
            #   It kind of makes sense when:
            #   - grid connection is expired, but might consider to reopen contract in future?
            #   - self.connection.active_from is still in future (not active yet)
            #
            #   -> no: raise ValueError("GridConnection {self.connection} is not active on {prediction_day}")
            pass

        # prediction_day:
        # - prediction_range (from..to) for historical data (nonsolar/regular) derived from it, in UTC
        #   ( --> prediction_range, passed to prediction services, would span at least 2 dates when converted to tz-aware UTC range)
        #
        # - prediction_day falls in a DST flip/flop date in Netherlands?
        #   -> no: prediction_range = [-1|-2h previous date; 21:59:59|22:59:59] in UTC
        #   -> yes: for historical data - check day weekday by weekday, going back in time by a week?
        #       - for solar consumption forecast:
        #           - CET -> CEST: prediction_range - shorter by 1h
        #           - CEST -> CET: prediction_range - longer by 1h (25h timespan in UTC)

        # Main algo - predict based on connection type (regular/solar/mixed).

        # TODO: properly create new empty Pandas time series
        # TODO: Should we Return empty series, or full list of hours with no-data marker?
        predicted = Series(dtype=float) # Based upon: https://stackoverflow.com/a/69275860

        if connection.prediction_type == PredictionType.regular:
            # As defined in epic:
            #
            # Companies usually follow a repetitive, weekly pattern
            # -> use historic data of similar weekdays to make a prediction:
            #   • (1) For predicting a Monday, average the values of the past 3 Mondays (same for Tuesday, Wednesday, etc.)
            #   • (2) If not available, use as many Mondays as available)
            #   • (3) If no Mondays are present at all, use average yearly value (from GridConnection)

            # Thoughts:
            # - if self.connection has active_from: ensure we do not request
            #       historical weekday consumption before that
            # - if self.connection has active_until:
            #       - if connection expired before last weekday_of(prediction_day):
            #           -> skip (1) and begin with (2), beginning from last weekday_of(prediction_day) before self.connection.active_until

            # (i) HistoricConsumptionService returns time series with step of 15 minutes -
            #     should we aggregate in pandas DataFrame, and apply a process like
            #     groupBy [split-apply-combine](https://pandas.pydata.org/pandas-docs/stable/user_guide/groupby.html#group-by-split-apply-combine)
            #     to returned historical consumoption data
            #     to get expected time granuality of 60 minutes?

            # (i) fallback to average yearly consumption -> calculate avg hourly consumption:
            #   - Assume 365 days per year, as GridConnection has no info of
            #     how many leap years had contributed to calculating annual consumption
            #   - avg_hourly_consumption = self.connection.standard_yearly_consumption / (365 * 24)

            # TODO: implement:
            # predicted = self.predict_regular_connection_consumption(prediction_day)

        elif connection.prediction_type == PredictionType.solar:
            # TODO: calculate prediction_range in UCT

            # Can be returned as result - SolarForecastService already indexes
            # series as expected in API contract
            predicted = self.solar_forecast(
                prediction_range.from,
                prediction_range.to,
                self.connection.latitude,
                self.connection.longitude,
                self.connection.solar_plane_declination,
                self.connection.solar_plane_azimuth,
                self.connection.solar_rated_power
            )

        elif connection.prediction_type == PredictionType.mixed_solar_regular:
            # As defined in epic:
            # • Collect solar forecast data from last 4 weeks
            # • Collect historic consumption values
            #   ^ suggests to extract previous two conditional branches to methods or classes!
            # • Subtract solar forecast from historic values
            # • Use remainder to make prediction as is done in “Regular”
            # • Do a separate “Solar” prediction (see previous slide)
            # • Add the two for the resulting prediction

        else:
            raise ValueError(f"Unexpected value for GridConnection.prediction_type: {connection.prediction_type}")


        # >>> [API contract] Return value:
        #
        # "Index datetimes are localized in UTC"
        #   ^ suggests time series to be indexed by full datetimes, not just by hours,
        #      as what's in Netherlands happens to be [00:00 - 00:59] during winter
        #      is last hour of previous date in UTC.
        return predicted
