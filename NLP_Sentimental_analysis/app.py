import streamlit as st
import pickle
import requests
from io import BytesIO

# Custom CSS for dark theme
custom_css = """
<style>
body {
    background-color: #121212; /* Dark background color */
    color: #FFFFFF; /* Text color */
}

.stTextInput>div>div>input {
    background-color: #333333; /* Dark input field color */
    color: #FFFFFF; /* Text color for input field */
}

.stButton>button {
    background-color: #4CAF50; /* Green color for buttons */
    color: #FFFFFF; /* Text color for buttons */
    border-color: #4CAF50; /* Border color for buttons */
}

.stButton>button:hover {
    background-color: #45a049; /* Darker green color for buttons on hover */
}

.stButton>button:active {
    background-color: #3e8e41; /* Darker green color for buttons when clicked */
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

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
