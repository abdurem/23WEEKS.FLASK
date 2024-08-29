import pandas as pd

# Load the CSV file into a DataFrame
df = pd.read_csv('app/models/names.csv')

def generate_name(gender='', origin='', category='', length='', letter=''):
    """
    Filters names based on provided criteria.

    Parameters:
    - gender (str): The gender to filter by (comma-separated for multiple values).
    - origin (str): The origin to filter by (comma-separated for multiple values).
    - category (str): The category to filter by (comma-separated for multiple values).
    - length (str): The length to filter by ('short', 'medium', or 'long').
    - letter (str): The starting letter to filter by.

    Returns:
    - List of filtered names.
    """
    # Ensure all inputs are strings
    if not all(isinstance(value, str) for value in [gender, origin, category, length, letter]):
        raise ValueError("All input values should be of type str")

    query = df.copy()

    if gender:
        genders = gender.split(',')
        query = query[query['Gender'].str.lower().isin([g.lower() for g in genders])]

    if origin:
        origins = origin.split(',')
        query = query[query['Origin'].str.lower().isin([o.lower() for o in origins])]

    if category:
        categories = category.split(',')
        query = query[query['Category'].str.lower().isin([c.lower() for c in categories])]

    if length:
        length_map = {
            'short': query['Name'].str.len() <= 4,
            'medium': (query['Name'].str.len() > 4) & (query['Name'].str.len() <= 7),
            'long': query['Name'].str.len() > 7
        }
        query = query[length_map.get(length.lower(), slice(None))]

    # Filter by first letter
        
    if letter:
        query = query[query['Name'].str.startswith(letter.upper())]

    # Select relevant columns to return
    result = query[['Name', 'Gender', 'Origin', 'Meaning']]

    # Convert the DataFrame to a list of dictionaries
    return result.to_dict(orient='records')