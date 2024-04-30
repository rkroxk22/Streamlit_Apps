import streamlit as st
import pickle
import requests
from io import BytesIO

# Set dark theme using Streamlit theming
st.markdown(
    """
    <style>
    .reportview-container {
        background-color: #121212;
        color: #FFFFFF;
    }
    .stTextInput>div>div>input {
        background-color: #333333;
        color: #FFFFFF;
        caret-color: #FFFFFF; /* Color of the cursor */
    }
    .stTextInput>div>div>input:focus {
        box-shadow: none; /* Remove the focus border */
    }
    .stButton>button {
        background-color: #4CAF50;
        color: #FFFFFF;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .stButton>button:active {
        background-color: #3e8e41;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Download the pickle file
url = 'https://github.com/rkroxk22/Streamlit_Apps/raw/main/NLP_Sentimental_analysis/IMDB_sentiment_analysis.pkl'
response = requests.get(url)
pickle_bytes = BytesIO(response.content)

# Load model
model = pickle.load(pickle_bytes)

# Create title
st.title('Sentiment Analysis Model')

# Text input for review with reduced spacing between the heading and the input
st.markdown('<p style="font-weight:bold; margin-bottom: 5px;">Enter your review:</p>', unsafe_allow_html=True)
review = st.text_input('')

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
