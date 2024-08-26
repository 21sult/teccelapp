import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection


# Setup
## Configure web page
st.set_page_config(
    page_title = 'Pedidos Teccel',
    page_icon = ':ocean:',
    layout = 'wide'
)

## Connect to Google Sheets
conn = st.experimental_connection('gsheets', type=GSheetsConnection)
df_blanks = conn.read(
            worksheet='Blocos',
            ttl=60
)
df_eps 	  = conn.read(
            worksheet='EPS FQ',
            ttl=60
)
df_dist = conn.read(
            worksheet='Distribuidores',
            ttl=60
)

## Title
st.title(':ocean: Plataforma de Pedidos Teccel')

## Tabs
tabs = st.tabs(['Efetuar Pedido', 'Catálogo', 'Contatos'])

## Get distributors
distributors = df_dist['Nome'].tolist()
distributors.insert(0, '---') # placeholder for selectbox

## Get subtypes
subtypes = ['TB','TecLight','TecGreen','Premium']

with tabs[0]:
    
    price = 0
    
    # Initialise orders DataFrame
    df_order = pd.DataFrame(index=df_blanks['Tipo'], columns=subtypes)
    df_order.fillna(0, inplace=True)
    
    # Initialise prices DataFrame
    df_prices = pd.DataFrame( df_blanks[['Tipo','TB','TecLight','TecGreen','Premium']] )	
    df_prices.set_index('Tipo', inplace=True)
    #st.dataframe(df_prices)
    
    col1, col2 = st.columns(2)
    
    with col1:
        
        st.subheader('Seu Pedido')
        
        # Select client name
        client_name = st.text_input('Seu Nome')
        
        # Select distributor
        selected_distributor = st.selectbox('Seu Distribuidor (Digite ou Selecione)', distributors) 
        
        # Select items
        st.write('Digite a quantidade que deseja de cada item.')
        df_order_editor = st.experimental_data_editor(df_order, width=500, height=500)
        
        if st.button('Revisar Pedido'):
            df_order_price = df_order_editor.copy()
            price = df_order_price * df_prices
            price = price.sum().sum()
            
            st.markdown('---')
            st.subheader('Seu Pedido:')
            for blank, row in df_order_editor.iterrows():
                
                for blank_type, amount in row.items():
                    
                    if amount > 0:
                        
                        product_price = df_prices.loc[blank, blank_type]
                        #st.write(f'{blank} {blank_type} x{amount} (R$ {product_price})')
                        st.write(blank, blank_type, f'x{amount}', f'(R$ {product_price*amount})')
            
            st.subheader('Total: R$ ' + str(price))
            st.markdown('---')
            
            st.button('Enviar Pedido')
    
    with col2:
        
        st.subheader('Catálogo')
        
        df_catalog = df_blanks.copy()
        for blank_type in subtypes:
            df_catalog[blank_type] = df_catalog[blank_type].astype(int)
            df_catalog[blank_type] = df_catalog[blank_type].apply(lambda x: f'R$ {x}')
        st.dataframe(df_catalog)
        
with tabs[1]:
    
    st.dataframe(df_blanks)
    
    