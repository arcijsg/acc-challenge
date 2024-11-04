"""
A bag of useful helpers to be sorted out to separate submodules in case
it grows either too big or too heterogenic.
"""

from pandas import Series


def is_empty_series(series: Series) -> bool:
    """
    Are time series empty (not containing any useful values)?
    """
    # As the contract was not specified fully for HistoricConsumptionService
    # and for SolarForecastService what the return value would be if
    # no historical data exists or solar consuption could not be predicted
    # (
    #  - empty Series? None?
    #  - Series with fewer data points than expected?
    #  - full time Series with NaN (NumPy.nan) or None as values?
    # )
    # introduce a helper to be easily replaced.
    return series.dropna().empty
