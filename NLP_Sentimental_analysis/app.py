import streamlit as st
import pickle
import requests
from io import BytesIO

# Set dark theme for Streamlit UI
st.set_page_config(page_title='Sentiment Analysis Model', layout='wide', initial_sidebar_state='auto', theme='dark')

# Download the pickle file
url = 'https://github.com/rkroxk22/Streamlit_Apps/raw/main/NLP_Sentimental_analysis/IMDB_sentiment_analysis.pkl'
response = requests.get(url)
pickle_bytes = BytesIO(response.content)

# Load model
model = pickle.load(pickle_bytes)

# Create title
st.title('Sentiment Analysis Model')

# Text input for review
review = st.text_input('Enter your review:')

# Submit button
submit = st.button('Predict')

# Check if the submit button is clicked and the review text input is not empty
if submit and review.strip() != '':
    prediction = model.predict([review])

    if prediction[0] == 'positive':
        st.success('Positive Review')
    else:
        st.warning('Negative Review')

# Check if the submit button is clicked but the review text input is empty
elif submit and review.strip() == '':
    st.warning('Please enter a review before predicting.')
