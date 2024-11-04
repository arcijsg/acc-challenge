import pytz
from datetime import date, datetime

from pandas import concat as df_concat, DataFrame, Series, date_range

from grid_connection import GridConnection, PredictionType
from historic_consumption_service import HistoricConsumptionService
from solar_forecast import SolarForecastService
from utils.datetime import get_prediction_range, last_weekday_before
from utils.general import is_empty_series


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
            (pandas.date_range(...).tz_convert("UTC"))
        """

        # Rough first thoughts:
        # ---------------------

        today = date.today()
        # >>> [API contract] preconditions & args:
        #
        # prediction_day:
        # - a naive datetime - assume to be a calendar day in Europe/Amsterdam tzone (CET or CEST)?
        #
        # TODO: extract preconditions to assertion method
        # TODO: clarify policy or assume it, documenting my assumptions!
        if prediction_day < today:
            # TODO: allow to cross-check predictions with past consumption records?
            #   -> yes: assert prediction_day falls within connection [active_from; active_until] date range
            #   -> no: raise ValueError("Prediction day should be in future")
            # )
            pass

        if prediction_day == today:
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

        if connection.prediction_type == PredictionType.regular:
            return self.predict_regular_connection_consumption(
                prediction_day, connection
            )

        elif connection.prediction_type == PredictionType.solar:
            # TODO: extract to method
            full_day = get_prediction_range(prediction_day)
            predict_from, predict_to = full_day.tz_convert("UTC")

            # returned series already indexed by hour (as expected in API contract)
            return self.solar_forecast_service(
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
        #   ^ suggests time series to be indexed by full datetimes, not just by hours?
        #      as what's in Netherlands happens to be [00:00 - 00:59] during winter
        #      is last hour of previous date in UTC.

        # TODO: properly create new empty Pandas time series
        # TODO: Should we Return empty series, or full list of hours with no-data marker?
        # Based upon: https://stackoverflow.com/a/69275860
        nothing = Series(dtype=float)
        return nothing

    def predict_regular_connection_consumption(
        self, prediction_day: date, connection: GridConnection
    ) -> Series:
        """
        Algorithm as defined in epic:

        Companies usually follow a repetitive, weekly pattern
         -> use historic data of similar weekdays to make a prediction:
            (1) For predicting a Monday, average the values of the past 3 Mondays (same for Tuesday, Wednesday, etc.)
            (2) If not available, use as many Mondays as available)
            (3) If no Mondays are present at all, use average yearly value (from GridConnection)
        """

        # TODO: Refactor me, please!

        # TODO: preconditions
        # - if connection has active_from: ensure we do not request
        #       historical weekday consumption before that
        # - if connection has active_until:
        #       - if connection expired before last weekday_of(prediction_day):
        #           -> skip (1) and begin with (2), beginning from last weekday_of(prediction_day) before connection.active_until

        # (1) attempt to average hourly historical consumption from last 3
        #     weekdays the prediction_day falls in.
        last_weekday = last_weekday_before(prediction_day.weekday())
        last_3_weeks = [
            last_weekday - timedelta(weeks=weeks_ago) for weeks_ago in range(3)
        ]

        # FIXME: Intuition suggests a data frame with one of axes consisting of
        #   hourly periods (not anchored to date?) - but of the same hourly periods
        #   as the prediction_day contains, as there could be 23 to 25 data points,
        #   based on DST state of the day.
        #
        #   Other axis - labelled by...naive date the historical sample was taken from?
        #   and consisting of hourly consumption for that day?
        avg_consumption = DataFrame()

        for day in last_3_weeks:
            if not connection.is_active_on(day):
                # TODO: recheck the assumption by Artūrs that there would be
                #   no historical data for days when connection contract was
                #   not active (yet or anymore)?
                continue

            time_start, time_end = get_prediction_range(day)

            # Historical data gets sampled at granuality of 15 minutes.
            # We are looking for hourly consumption:
            hourly_consumption = (
                self.historic_consumption_service.get_consumption(
                    connection, time_start, time_end
                )
                .resample("1h")
                .sum()
            )

            if is_empty_series(hourly_consumption):
                continue

            # TODO: append to avg_consumption in a way that the data points
            #   could afterwards be averaged by hour
            #   using:
            #   (?) avg_consumption.groupby(...hourly component of all data points...).mean()

        # TODO:
        # if avg_consumption contains exactly 3 entries:
        #    - group avg_consumption by hourly component of all data points
        #    - avg_hourly_consumption =
        #        average the values within each hourly group (.mean())
        #    - build a new Series, indexed by hours in prediction_day, expfressed in UTC:
        #        predict_from, predict_to = get_prediction_range(day)
        #        hours = date_range(predict_from, predict_to, freq="1h")
        #        return Series(index=hours, data=avg_hourly_consumption)
        #
        #       NOTE: [split-apply-combine](https://pandas.pydata.org/pandas-docs/stable/user_guide/groupby.html#group-by-split-apply-combine)
        #
        # else:
        #    try as many weekdays as available of prediction_day.weekday() withing data period
        #    from connection.active_from to earliest_of(connection.active_from, date.today())
        #    (?) impose a sane limit on number of historical days to query for?

        # Fall back to roughly approximating hourly production/consumption
        # based upon avg yearly consumption for the grid connection in question.
        return self.approximate_yearly_consumption_as_prediction(
            connection, prediction_day
        )

    def approximate_yearly_consumption_as_prediction(
        self, connection: GridConnection, prediction_day: date
    ) -> Series:
        """
        Given a grid connection with a known annual consumption
        """
        predict_from, predict_to = get_prediction_range(prediction_day)
        hours = date_range(predict_from, predict_to, freq="1h")

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
        # NOTE: we assume that standard_yearly_consumption would contain zero
        #   if annual consumption is not known (yet) instead None or NaN
        return connection.standard_yearly_consumption / hours_per_year
