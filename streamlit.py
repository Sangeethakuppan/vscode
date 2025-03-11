import streamlit as st
import pymysql
import pandas as pd

# Try to connect to the MySQL database
try:
    conn = pymysql.connect(
        host='127.0.0.1',
        user='root',
        passwd='Lakshmi@123',
        db='red_bus'  # Ensure the database exists
    )
    
    # Query to fetch data
    query = "SELECT * FROM bus_routes"
    
    # Use pandas to read the SQL query into a DataFrame
    data = pd.read_sql(query, conn)
    
    # Close the connection after fetching the data
    conn.close()

except pymysql.MySQLError as e:
    st.error(f"Error connecting to MySQL database: {e}")
    data = pd.DataFrame()  # Create an empty DataFrame in case of error

# Streamlit App layout
st.title('Redbus Routes Data Filtering and Analysis')

if not data.empty:
    # Filters
    bustype_filter = st.multiselect('Select Bus Type:', options=data['bustype'].unique())
    route_filter = st.multiselect('Select Route:', options=data['route_name'].unique())
    price_filter = st.slider('Select Price Range:', min_value=int(data['price'].min()), max_value=int(data['price'].max()), value=(int(data['price'].min()), int(data['price'].max())))
    star_filter = st.slider('Select Star Rating Range:', min_value=float(data['star_rating'].min()), max_value=float(data['star_rating'].max()), value=(float(data['star_rating'].min()), float(data['star_rating'].max())))
    availability_filter = st.slider('Select Seat Availability Range:', min_value=int(data['seats_available'].min()), max_value=int(data['seats_available'].max()), value=(int(data['seats_available'].min()), int(data['seats_available'].max())))

    # Apply filters
    filtered_data = data

    if bustype_filter:
        filtered_data = filtered_data[filtered_data['bustype'].isin(bustype_filter)]

    if route_filter:
        filtered_data = filtered_data[filtered_data['route_name'].isin(route_filter)]

    filtered_data = filtered_data[(filtered_data['price'] >= price_filter[0]) & (filtered_data['price'] <= price_filter[1])]
    filtered_data = filtered_data[(filtered_data['star_rating'] >= star_filter[0]) & (filtered_data['star_rating'] <= star_filter[1])]
    filtered_data = filtered_data[(filtered_data['seats_available'] >= availability_filter[0]) & (filtered_data['seats_available'] <= availability_filter[1])]

    # Display filtered data
    st.write('Filtered Data:')
    st.dataframe(filtered_data)

    # Download button
    if not filtered_data.empty:
        st.download_button(
            label="Download Filtered Data",
            data=filtered_data.to_csv(index=False),
            file_name="filtered_data.csv",
            mime="text/csv"
        )
    else:
        st.warning("No data available with the selected filters.")
else:
    st.warning("Failed to connect to the database or no data available.")
