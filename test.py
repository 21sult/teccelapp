import random
import string
import smtplib
import re
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import requests
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
distributos_emails = df_dist['Email'].tolist()

## Get subtypes
subtypes = ['TB','TecLight','TecGreen','Premium']

## Define reCAPTCHA site and secret keys
RECAPTCHA_SITE_KEY = st.secrets['recaptcha_site_key']
RECAPTCHA_SECRET_KEY = st.secrets['recaptcha_secret_key']

## Initialise session states
if 'order_reviewed' not in st.session_state:
    st.session_state['order_reviewed'] = False
if 'order_text' not in st.session_state:
    st.session_state['order_text'] = ''
if 'price' not in st.session_state:
    st.session_state['price'] = 0


## Function to verify reCAPTCHA response
def verify_recaptcha(response):
    payload = {
        'secret': RECAPTCHA_SECRET_KEY,
        'response': response
    }
    verification = requests.post('https://www.google.com/recaptcha/api/siteverify', data=payload)
    result = verification.json()
    return result.get('success')

## Function to validate email
def is_valid_email(email):
    
    # Define regex pattern
    email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    
    # Check if email fits regex pattern
    if re.match(email_pattern, email):
        return True
    else:
        return False


## Function to send email
def send_email(sender_email, sender_password, recipient_emails, subject, message):
    
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To']	= ','.join(recipient_emails)
        msg['Subject'] = subject
        
        msg.attach(MIMEText(message, 'html'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        
        server.send_message(msg)
        server.quit()
        
        st.success('Pedido enviado com sucesso.')
        
    except Exception as e:
        
        st.error(f'Falha ao enviar o pedido: {e}')


## Function to generate order number
def gen_order_code(length=15):
    
    # List of possible characters
    characters = string.ascii_uppercase + string.digits
    
    # Generate random string of specified length
    order_code = ''.join(random.choices(characters, k=length))
    
    return order_code

## Function to send order
def send_order(client_name, selected_distributor, order_text, recipient_emails):
    
    # Order text
    order_code = gen_order_code()
    total_price = st.session_state['price']
    new_order_text = (
        f'<p>Pedido <b>#{order_code}</b></p>'
        f'De <b>{client_name}</b> para <b>{selected_distributor}</b>'
        #f'<p>&nbsp;</p>' # emtpy line
        f'<ul>'
        f'{order_text}'
        f'</ul>'
        f'<b>Total</b>: R&#36; {total_price}'
    )
    
    # Sending email
    sender_email = st.secrets['email_address']
    sender_password = st.secrets['email_password']
    subject = f'Pedido Teccel #{order_code}'
    send_email(sender_email, sender_password, recipient_emails, subject, new_order_text)


# --- UI --- #
# TAB: Enviar pedido
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
        
        # Select client email
        client_email = st.text_input('Seu Email')
        
        # Select distributor
        selected_distributor = st.selectbox('Seu Distribuidor (Digite ou Selecione)', distributors) 
        
        # Select items
        st.write('Digite a quantidade que deseja de cada item.')
        df_order_editor = st.experimental_data_editor(df_order, width=500, height=500)
        
        if st.button('Revisar Pedido'):
            
            # Update session state
            st.session_state['order_reviewed'] = True
            
            # Initialise order_text
            order_text = ''
            
            # Calculate price
            df_order_price = df_order_editor.copy()
            price = df_order_price * df_prices
            price = price.sum().sum()
            st.session_state['price'] = price
            
            # Get order text
            product_amount = 0
            for blank, row in df_order_editor.iterrows():
                
                for blank_type, amount in row.items():
                    
                    if amount > 0:
                        
                        product_price = df_prices.loc[blank, blank_type]
                        text = f'{blank} {blank_type} x{amount} (R&#36; {product_price})'
                        order_text += text + '<br>'
                        
                        product_amount += 1
            
            if product_amount > 0:
                
                st.session_state['order_text'] = order_text
        
            else:
                
                st.session_state['order_text'] = 'O usuário não escolheu nenhum produto.'
        
        # Order review
        if st.session_state['order_reviewed']:
            
            # Receipt (sort of)
            st.markdown('---')
            st.subheader('Seu Pedido:')
            st.markdown(st.session_state['order_text'], unsafe_allow_html=True)
            st.subheader('Total: R&#36; ' + str(st.session_state['price']))
            st.markdown('---')
            
            # Emails: teccel, distributor, recipient
            teccel_email = st.secrets['email_address']
            distributor_email = df_dist.loc[df_dist['Nome'] == selected_distributor, 'Email'].values[0]
            recipient_emails = [teccel_email, distributor_email, client_email]
            
            # Render reCAPTCHA widget
            components.html(
                f"""
                <script src="https://www.google.com/recaptcha/api.js" async defer></script>
                <div class="g-recaptcha" data-sitekey="{RECAPTCHA_SITE_KEY}"></div>
                """,
                height=200
            )
            
            # Send order
            if st.button('Enviar Pedido'):
                
                # Verify reCAPTCHA
                recaptcha_response_token = st.experimental_get_query_params().get('g-recaptcha-response', [None])[0]
                if recaptcha_response_token and verify_recaptcha(recaptcha_response_token):
                    
                    # Verify client email
                    if is_valid_email(client_email):
                        send_order(client_name, selected_distributor, st.session_state['order_text'], recipient_emails)
                    else:
                        st.warning('O email inserido é inválido.')
                        
                else:
                    st.error('Verificação CAPTCHA falhou. Favor tentar novamente.')
    
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
                
    
    
    