import streamlit as st
from sqlalchemy import create_engine
import pandas as pd
from urllib.parse import quote_plus

def run_streamlit_app():
    # Create a database engine with encoded password
    try:
        password = quote_plus('Lakshmi@123')  # URL encode password
        engine = create_engine(f'mysql+pymysql://root:{password}@127.0.0.1:3306/red_bus')
        conn = engine.connect()
        st.success("Connected to the database successfully!")
    except Exception as e:
        st.error(f"An error occurred while connecting to the database: {e}")
        return

    # Ensure the connection is established and handle exceptions
    try:
        # Read data from the database
        query = "SELECT * FROM bus_routes"  # Make sure the table name is correct
        data = pd.read_sql(query, conn)
        st.success("Data fetched successfully!")

        # Log column names for debugging
        st.write("Column names:", data.columns)

        # Ensure numeric columns are correctly typed
        data['price'] = pd.to_numeric(data['price'], errors='coerce')
        data['star_rating'] = pd.to_numeric(data['star_rating'], errors='coerce')
        data['seats_available'] = pd.to_numeric(data['seats_available'], errors='coerce')

        # Streamlit app title
        st.title('Redbus Routes Data Filtering and Analysis')

        # Create filters
        bustype_filter = st.multiselect('Select Bus Type:', options=data['bustype'].dropna().unique())
        route_filter = st.multiselect('Select Route:', options=data['route_name'].dropna().unique())
        price_filter = st.slider('Select Price Range:', min_value=int(data['price'].min()), max_value=int(data['price'].max()), value=(int(data['price'].min()), int(data['price'].max())))
        star_filter = st.slider('Select Star Rating Range:', min_value=float(data['star_rating'].min()), max_value=float(data['star_rating'].max()), value=(float(data['star_rating'].min()), float(data['star_rating'].max())))
        availability_filter = st.slider('Select Seat Availability Range:', min_value=int(data['seats_available'].min()), max_value=int(data['seats_available'].max()), value=(int(data['seats_available'].min()), int(data['seats_available'].max())))

        # Filter data
        filtered_data = data.copy()

        if bustype_filter:
            filtered_data = filtered_data[filtered_data['bustype'].isin(bustype_filter)]

        if route_filter:
            filtered_data = filtered_data[filtered_data['route_name'].isin(route_filter)]

        filtered_data = filtered_data[(filtered_data['price'] >= price_filter[0]) & (filtered_data['price'] <= price_filter[1])]
        filtered_data = filtered_data[(filtered_data['star_rating'] >= star_filter[0]) & (filtered_data['star_rating'] <= star_filter[1])]
        filtered_data = filtered_data[(filtered_data['seats_available'] >= availability_filter[0]) & (filtered_data['seats_available'] <= availability_filter[1])]

        # Display filtered data
        if filtered_data.empty:
            st.warning("No data available with the selected filters.")
        else:
            st.write('Filtered Data:')
            st.dataframe(filtered_data)

            st.download_button(
                label="Download Filtered Data",
                data=filtered_data.to_csv(index=False),
                file_name="filtered_data.csv",
                mime="text/csv"
            )

    except Exception as e:
        st.error(f"An error occurred while fetching the data: {e}")

    finally:
        conn.close()

# Run the Streamlit app
if __name__ == "__main__":
    run_streamlit_app()


