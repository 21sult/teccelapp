import streamlit as st
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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
tabs = st.tabs(['Efetuar Pedido', 'Contatos'])

## Get distributors
distributors = df_dist['Nome'].tolist()
distributors.insert(0, '---') # placeholder for selectbox

## Get subtypes
subtypes = ['TB','TecLight','TecGreen','Premium']

## Function to send email
def send_email(sender_email, sender_password, recipient_email, subject, message):
    
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To']	= recipient_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(message, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        
        server.send_message(msg)
        server.quit()
        
        st.success('Pedido enviado com sucesso.')
        
    except Exception as e:
        
        sr.error('Falha ao enviar o pedido.')

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
        
        order_text = ''
        
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
                        text = f'{blank} {blank_type} x{amount} (R$ {product_price})'
                        order_text += text + '\n'
                        st.write(text)
            
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
    
    st.subheader('Contato')
    
    st.markdown("[Site Oficial](%s)" % 'https://surfteccel.com.br/en')
    st.write('Endereço: Av. Fernando Simões Barbosa, 558, Salas 1103 e 1104, Boa Viagem - CEP 51021-060')
    st.write('Telefone: (81) 3338-4610')
    st.write('Email: contato@surfteccell.com.br')
    st.write('Monday - Friday: 8:00 - 17:00')
                
    
    
    