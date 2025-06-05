"""Common data manipulation functions for educational data analysis."""

from sklearn.model_selection import train_test_split


def remove_outliers(df, column, lower_quantile=0.01, upper_quantile=0.99):
    """Remove outliers from a DataFrame column based on quantiles.

    Args:
        df (pd.DataFrame): Input DataFrame.
        column (str): Column name to filter.
        lower_quantile (float): Lower quantile threshold.
        upper_quantile (float): Upper quantile threshold.

    Returns:
        pd.DataFrame: DataFrame with outliers removed.
    """
    lower = df[column].quantile(lower_quantile)
    upper = df[column].quantile(upper_quantile)
    return df[(df[column] >= lower) & (df[column] <= upper)]


def normalize_column(df, column):
    """Normalize a DataFrame column to the 0-1 range.

    Args:
        df (pd.DataFrame): Input DataFrame.
        column (str): Column name to normalize.

    Returns:
        pd.DataFrame: DataFrame with normalized column.
    """
    df = df.copy()
    min_val = df[column].min()
    max_val = df[column].max()
    df[column] = (df[column] - min_val) / (max_val - min_val)
    return df


def split_dataset(df, test_size=0.2, random_state=42):
    """Split a DataFrame into train and test sets.

    Args:
        df (pd.DataFrame): Input DataFrame.
        test_size (float): Proportion for test set.
        random_state (int): Random seed.

    Returns:
        (pd.DataFrame, pd.DataFrame): Train and test DataFrames.
    """
    train_df, test_df = train_test_split(df, test_size=test_size, random_state=random_state)
    return train_df, test_df
