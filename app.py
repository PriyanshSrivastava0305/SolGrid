import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="CSV Visualizer", layout="centered")
st.title("📊 Smart CSV Visualizer")

uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success("CSV uploaded successfully!")
    st.write("Preview:")
    st.dataframe(df.head())
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    all_cols = df.columns.tolist()

    x_col = st.selectbox("Select X-axis column", all_cols)
    y_col = st.selectbox("Select Y-axis column (optional)", [None] + all_cols)

    if x_col:
        try:
            if y_col:
                if pd.api.types.is_numeric_dtype(df[x_col]) and pd.api.types.is_numeric_dtype(df[y_col]):
                    fig = px.scatter(df, x=x_col, y=y_col, title=f"Scatter: {x_col} vs {y_col}")
                elif pd.api.types.is_numeric_dtype(df[y_col]) and not pd.api.types.is_numeric_dtype(df[x_col]):
                    fig = px.box(df, x=x_col, y=y_col, title=f"Box Plot: {y_col} by {x_col}")
                else:
                    fig = px.histogram(df, x=x_col, color=y_col, title=f"Histogram: {x_col} grouped by {y_col}")
            else:
                if pd.api.types.is_numeric_dtype(df[x_col]):
                    fig = px.histogram(df, x=x_col, title=f"Histogram: {x_col}")
                else:
                    count_df = df[x_col].value_counts().reset_index()
                    count_df.columns = [x_col, "Count"]
                    fig = px.bar(count_df, x=x_col, y="Count", title=f"Bar Chart: {x_col}")
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error: {str(e)}")

else:
    st.info("Please upload a CSV file to visualize data.")
    st.markdown(
        """
        **Instructions:**
        1. Upload a CSV file using the file uploader.
        2. Select the columns for X and Y axes from the dropdowns.
        3. The visualization will be generated automatically.
        """
    )
