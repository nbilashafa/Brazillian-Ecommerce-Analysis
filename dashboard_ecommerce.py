import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency
sns.set(style='dark')

def create_daily_orders_df(df):
    daily_orders_df = df.resample(rule='D', on='order_purchase_timestamp_x').agg({
        "order_id": "nunique",
        "payment_value_x": "sum"
    })
    daily_orders_df = daily_orders_df.reset_index()
    daily_orders_df.rename(columns={
        "order_id": "order_count",
        "payment_value_x": "revenue"
    }, inplace=True)
    
    return daily_orders_df


def create_sum_order_items_df(df):
    sum_order_items_df = df.groupby("product_category_name_english").order_id.sum().sort_values(ascending=False).reset_index()
    return sum_order_items_df


def create_bystate_df(df):
    bystate_df = df.groupby(by="customer_state_x").customer_id_x.nunique().reset_index()
    bystate_df.rename(columns={
        "customer_id_x": "customer_count"
    }, inplace=True)
    
    return bystate_df

def create_byproduct_df(df):
        byproduct_df = df.groupby(by=["product_category_name_english"]).agg({
        "customer_id_x": "count",
        })
        byproduct_df.rename(columns={
            "customer_id_x": "customer_count"
        }, inplace=True)
        byproduct_df = byproduct_df.reset_index()  # Reset the index to make "product_category_name_english" a regular column
        byproduct_df = byproduct_df.sort_values(by="customer_count", ascending=False)
        return byproduct_df\
    
def create_rfm_df(df):
    rfm_df = df.groupby(by="customer_id_x", as_index=False).agg({
        "order_purchase_timestamp_x": "max", #mengambil tanggal order terakhir
        "order_id": "nunique",
        "payment_value_x": "sum"
    })
    rfm_df.columns = ["customer_id_x", "max_order_timestamp", "frequency", "monetary"]
    
    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"].dt.date
    recent_date = df["order_purchase_timestamp_x"].dt.date.max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)
    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)
    
    return rfm_df

#sortorder date
all_df = pd.read_csv("all_data.csv")
datetime_columns = ["order_purchase_timestamp_x", "order_estimated_delivery_date_y"]
all_df.sort_values(by="order_purchase_timestamp_x", inplace=True)
all_df.reset_index(inplace=True)
 
for column in datetime_columns:
    all_df[column] = pd.to_datetime(all_df[column])

min_date = all_df["order_purchase_timestamp_x"].min()
max_date = all_df["order_purchase_timestamp_x"].max()
 
with st.sidebar:
    
    # Mengambil start_date & end_date dari date_input
    start_date, end_date = st.date_input(
        label='Rentang Waktu',min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )
main_df = all_df[(all_df["order_purchase_timestamp_x"] >= str(start_date)) & 
                (all_df["order_purchase_timestamp_x"] <= str(end_date))]
# # Menyiapkan berbagai dataframe
daily_orders_df = create_daily_orders_df(main_df)
sum_order_items_df = create_sum_order_items_df(main_df)
bystate_df = create_bystate_df(main_df)
byproduct_df = create_byproduct_df(main_df)
rfm_df = create_rfm_df(main_df)


# plot number of daily orders (2021)
st.header('Brazillian Ecommerce Dashboard :plane:')
st.subheader('Orders')

col1, col2 = st.columns(2)

with col1:
    total_orders = daily_orders_df.order_count.sum()
    st.metric("Total orders", value=total_orders)

with col2:
    total_revenue = format_currency(daily_orders_df.revenue.sum(), "BRL ", locale='es_CO') 
    st.metric("Total Revenue", value=total_revenue)

fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(
    daily_orders_df["order_purchase_timestamp_x"],
    daily_orders_df["order_count"],
    marker='o', 
    linewidth=2,
    color="#90CAF9"
)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)

st.pyplot(fig)


# Product performance
st.subheader("Highest and Lowest State with Total Customer")

col1, col2 = st.columns(2)

with col1:
    fig, ax = plt.subplots(figsize=(20, 10))

    colors = ["#BD959F", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

    # Mengurutkan totalcust berdasarkan jumlah pelanggan
    bystate_df = bystate_df.sort_values(by="customer_count", ascending=False)

    sns.barplot(x="customer_count", y="customer_state_x", data=bystate_df.head(5), palette=colors, ax=ax)
    ax.set_ylabel(None)
    ax.set_xlabel(None)
    ax.set_title("Highest State with Total Customer", loc="center", fontsize=18)
    ax.tick_params(axis='y', labelsize=15)
    st.pyplot(fig)
with col2:
    fig, ax = plt.subplots(figsize=(20, 10))

    colors = ["#BD959F", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]    
    sns.barplot(x="customer_count", y="customer_state_x", data=bystate_df.sort_values(by="customer_count", ascending=True).head(5), palette=colors, ax=ax)
    ax.set_ylabel(None)
    ax.set_xlabel(None)
    ax.invert_xaxis()
    ax.yaxis.set_label_position("right")
    ax.yaxis.tick_right()
    ax.set_title("Lowest State with Total Customer", loc="center", fontsize=18)
    ax.tick_params(axis='y', labelsize=15)
    st.pyplot(fig)

st.subheader("Product Buying ")
# Filter out categories with customer_count less than 1,5%
threshold = 0.015 * byproduct_df["customer_count"].sum()
filtered_df = byproduct_df[byproduct_df["customer_count"] >= threshold]

# Create a new row for "Others" by summing up filtered categories
others_count = byproduct_df[byproduct_df["customer_count"] < threshold]["customer_count"].sum()
others_df = pd.DataFrame({"product_category_name_english": ["Others"], "customer_count": [others_count]})

# Concatenate filtered categories and "Others"
final_df = pd.concat([filtered_df, others_df])

# Create a pie chart
fig, ax = plt.subplots(figsize=(20, 10))
plt.pie(final_df["customer_count"], labels=final_df["product_category_name_english"], autopct='%1.1f%%', startangle=180)
plt.title('Customer Distribution by Product Category')
plt.axis('equal')  # Equal aspect ratio ensures that the pie chart is drawn as a circle.

st.pyplot(fig)


# Best Customer Based on RFM Parameters
st.subheader("Best Customer Based on RFM Parameters")

col1, col2, col3 = st.columns(3)

with col1:
    avg_recency = round(rfm_df.recency.mean(), 1)
    st.metric("Average Recency (days)", value=avg_recency)

with col2:
    avg_frequency = round(rfm_df.frequency.mean(), 2)
    st.metric("Average Frequency", value=avg_frequency)

with col3:
    avg_frequency = format_currency(rfm_df.monetary.mean(), "BRL", locale='es_CO') 
    st.metric("Average Monetary", value=avg_frequency)

fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(35, 15))
colors = ["#BD959F", "#BD959F", "#BD959F", "#BD959F", "#BD959F"]

sns.barplot(y="recency", x="customer_id_x", data=rfm_df.sort_values(by="recency", ascending=True).head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel("customer_id_x", fontsize=30)
ax[0].set_title("By Recency (days)", loc="center", fontsize=50)
ax[0].tick_params(axis='y', labelsize=30)
ax[0].tick_params(axis='x', labelsize=35)

sns.barplot(y="frequency", x="customer_id_x", data=rfm_df.sort_values(by="frequency", ascending=False).head(5), palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel("customer_id_x", fontsize=30)
ax[1].set_title("By Frequency", loc="center", fontsize=50)
ax[1].tick_params(axis='y', labelsize=30)
ax[1].tick_params(axis='x', labelsize=35)

sns.barplot(y="monetary", x="customer_id_x", data=rfm_df.sort_values(by="monetary", ascending=False).head(5), palette=colors, ax=ax[2])
ax[2].set_ylabel(None)
ax[2].set_xlabel("customer_id_x", fontsize=30)
ax[2].set_title("By Monetary", loc="center", fontsize=50)
ax[2].tick_params(axis='y', labelsize=30)
ax[2].tick_params(axis='x', labelsize=35)

st.pyplot(fig)

st.caption('Nabila Shafa Oktavia')