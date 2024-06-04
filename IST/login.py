import streamlit as st
import plotly.express as px

# Dummy user credentials
USER_CREDENTIALS = {'admin': 'password'}

# Function to handle login
def login():
    st.markdown("""
        <style>
        @media (min-width: 576px) {
            .st-emotion-cache-13ln4jf {
                padding-left: 1rem;
                padding-right: 1rem;
                background: radial-gradient(black, transparent);
            }
        }
        .st-emotion-cache-13ln4jf {
            width: 60%;
            padding: 50px 120px 160px;
            max-width: 46rem;
           position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
}
        }
        *, ::before, ::after {
            box-sizing: border-box;
        }
        .st-emotion-cache-1r4qj8v {
            position: absolute;
            background: rgb(255, 255, 255);
            color: rgb(49, 51, 63);
            inset: 0px;
            color-scheme: light;
            overflow: hidden;
        }
        body {
            margin: 0px;
            font-family: "Source Sans Pro", sans-serif;
            font-weight: 400;
            line-height: 1.6;
            color: rgb(49, 51, 63);
            background-color: rgb(255, 255, 255);
            text-size-adjust: 100%;
            -webkit-tap-highlight-color: rgba(0, 0, 0, 0);
            -webkit-font-smoothing: auto;
        }
        html {
            font-size: 16px;
        }
        html {
            font-size: 1rem;
        .st-emotion-cache-1jmvea6 p {
    word-break: break-word;
    margin-bottom: 0px;
    font-size: 14px;
    color: white;
}
p, ol, ul, dl {
    margin: 0px 0px 1rem;
    padding: 0px;
    font-size: 1rem;
    font-weight: 400;
    color: white;
}
        }
        ::-webkit-scrollbar {
            background: transparent;
            border-radius: 100px;
            height: 6px;
            width: 6px;
        }
        /* Global styles */
        body {
            background-color: #f0f2f6;
            font-family: 'Arial', sans-serif;
        }
        .stApp {
            margin: 0 auto;
            padding: 20px;
        }
        /* Header styles */
        .header {
            text-align: center;
            margin-bottom: 20px;
            color: #333;
        }
        .header h1 {
            font-size: 2.5em;
        }
        /* Container styles */
        .container {
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            padding: 20px;
            margin-bottom: 20px;
        }
        /* Custom button styles */
        .stButton>button {
            background-color: black;
            color: white;
            border: solid;
            border-radius: 20px;
            padding: 5px 25px;
            border-color: black;     
        }
        .stButton>button:hover {
            background-color: white;
            color: black;
            border-color: white;
        }
        .st-b7 {
            background-color: transparent;
        }
        .st-ao {
            border-top-style: none;
        }
        .st-an {
            border-right-style: none;
        }
        .st-am {
            border-left-style: none;
        }
                .st-bu {
    line-height: 1.4;
    color: white;
}
        .st-emotion-cache-bm2z3a {
        width: 100%;
        overflow: auto;
        background-image: linear-gradient(to left bottom, #010002, #201d2b, #303753, #375480, #2874ae);
      }  
        </style>
    """, unsafe_allow_html=True)
    
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    remember_me = st.checkbox("Remember me")
    
    if st.button("Login"):
        if USER_CREDENTIALS.get(username) == password:
            st.session_state['logged_in'] = True
            st.session_state.page = 'Home'
        else:
            st.error("Invalid username or password")

# Main application
def main():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if not st.session_state['logged_in']:
        login()
    else:
        st.markdown('<div class="header"><h1>It\'s summer!</h1></div>', unsafe_allow_html=True)
        st.sidebar.header("Configuration")

        df = px.data.iris()

        for i in range(1, 5):
            with st.container():
                st.markdown(f'<div class="container"><h2>Big {i}</h2>', unsafe_allow_html=True)
                st.markdown(
                    """<div class="markdown-text-container">
                    Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. 
                    Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. 
                    Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. 
                    Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
                    </div>""", unsafe_allow_html=True)
                st.plotly_chart(px.scatter(df, x="sepal_width", y="sepal_length", color="species"))
                st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
