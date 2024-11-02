import pytz
from datetime import date, datetime

from pandas import Series

from grid_connection import GridConnection, PredictionType
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
        # TODO: extract preconditions to assertion method
        # TODO: clarify policy or assume it, documenting my assumptions!
        if prediction_day < date.today():
            # TODO: allow to cross-check predictions with past consumption records?
            #   -> yes: assert prediction_day falls within connection [active_from; active_until] date range
            #   -> no: raise ValueError("Prediction day should be in future")
            # )
            pass

        if prediction_day == date.today():
            # TODO: allow partial predictions? It would kind of make sense...
            #   -> yes:
            #      - fill hours already passed with historical data (for regular; available for solar connections?)
            #      - predict future hours using:
            #        - regular consumer: partial datetime range (just hours still to come today) for efficiency?
            #   -> no: raise ValueError("Prediction day should be in future")
            pass

        if not connection.is_active_on(prediction_day):
            # TODO: would it make sense to offer consumption predictions outside
            #   of contract period for the consumer?
            #   It kind of makes sense when:
            #   - grid connection is expired, but might consider to reopen contract in future?
            #   - connection.active_from is still in future (not active yet)
            #
            #   -> no: raise ValueError("GridConnection {connection} is not active on {prediction_day}")
            pass

        # Main algo - predict based on connection type (regular/solar/mixed).

        # TODO: properly create new empty Pandas time series
        # TODO: Should we Return empty series, or full list of hours with no-data marker?
        predicted = Series(
            dtype=float
        )  # Based upon: https://stackoverflow.com/a/69275860

        if connection.prediction_type == PredictionType.regular:
            return self.predict_regular_connection_consumption(
                prediction_day, connection
            )

        elif connection.prediction_type == PredictionType.solar:
            # TODO: extract to method
            predict_from, predict_to = self.get_prediction_range(prediction_day)

            # SolarForecastService already indexes series by hour (as expected in API contract)
            return self.solar_forecast(
                predict_from,
                predict_to,
                connection.latitude,
                connection.longitude,
                connection.solar_plane_declination,
                connection.solar_plane_azimuth,
                connection.solar_rated_power,
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
            pass

        else:
            # TODO: include valid values of prediction_type in exception msg
            raise ValueError(
                f"Unexpected value for GridConnection.prediction_type: {connection.prediction_type}"
            )

        # >>> [API contract] Return value:
        #
        # "Index datetimes are localized in UTC"
        #   ^ suggests time series to be indexed by full datetimes, not just by hours,
        #      as what's in Netherlands happens to be [00:00 - 00:59] during winter
        #      is last hour of previous date in UTC.
        return predicted

    def predict_regular_connection_consumption(
        self, prediction_day: date, connection: GridConnection
    ) -> Series:
        # As defined in epic:
        #
        # Companies usually follow a repetitive, weekly pattern
        # -> use historic data of similar weekdays to make a prediction:
        #   • (1) For predicting a Monday, average the values of the past 3 Mondays (same for Tuesday, Wednesday, etc.)
        #   • (2) If not available, use as many Mondays as available)
        #   • (3) If no Mondays are present at all, use average yearly value (from GridConnection)

        # Thoughts:
        # - if connection has active_from: ensure we do not request
        #       historical weekday consumption before that
        # - if connection has active_until:
        #       - if connection expired before last weekday_of(prediction_day):
        #           -> skip (1) and begin with (2), beginning from last weekday_of(prediction_day) before connection.active_until

        # (i) HistoricConsumptionService returns time series with step of 15 minutes -
        #     should we aggregate in pandas DataFrame, and apply a process like
        #     groupBy [split-apply-combine](https://pandas.pydata.org/pandas-docs/stable/user_guide/groupby.html#group-by-split-apply-combine)
        #     to returned historical consumoption data
        #     to get expected time granuality of 60 minutes?

        # (i) fallback to average yearly consumption -> calculate avg hourly consumption:
        #   - Assume 365 days per year, as GridConnection has no info of
        #     how many leap years had contributed to calculating annual consumption
        #   - avg_hourly_consumption = connection.standard_yearly_consumption / (365 * 24)

        # TODO: implement:
        pass

    def approximate_yearly_consumption_as_prediction(
        self, connection: GridConnection, prediction_day: date
    ) -> Series:
        predict_from, predict_to = self.get_prediction_range(prediction_day)
        hours = date_range(predict_from, predict_to, freq="60T")

        avg_kwh_per_hour = self.avg_hourly_consumption(connection)
        return Series(index=hours, data=avg_kwh_per_hour)

    def avg_hourly_consumption(self, connection: GridConnection) -> float:
        """
        When no suitable historical data available for regular/mixed
        grid connections, approximate hourly consumption/production based
        upon historically recorded annual consumption (in kWh).

        Args:
            connection
        Returns:
            float (kWh consumed or produced on average per hour)
        """
        # TODO: could refine a bit by taking into account how many leap
        #   years happened to be during period of:
        #   [connection.active_from; active_until|today]
        hours_per_year = 8760  # 365 * 24
        return connection.standard_yearly_consumption / hours_per_year

        # TODO: return Pandas date_range instead? (https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#generating-ranges-of-timestamps)
        # TODO: extract to something like datetime_utils.py ?
        def get_prediction_range(
            self, day: date, tzone="Europe/Amsterdam"
        ) -> tuple[datetime, datetime]:
            """
            Args:
                day: (naive) calendar day, as experienced in assumed time zone
                tzone: by default, Amsterdam time - as product scoped for Dutch market
            Returns:
                a tuple with two datetimes in UTC ranging from with first and last second
                of the period to predict consumption for.

                Usually would span two dates in UTC, and contains a range of 23, 24 or 25 hours.
            """

            # TODO: adjust by +/- one extra hour if +day+ falls in date when
            #   DST gets adjusted in target time zone

            assumed_tz = pytz.timezone(tzone)
            tz_aware_day = datetime(day.year, day.month, day.day, tzinfo=assumed_tz)

            begins = datetime.combine(tz_aware_day, time.min)
            ends = datetime.combine(tz_aware_day, time.max)

            return (begins.astimezone(pytz.utc), ends.astimezone(pytz.utc))
