import streamlit as st
import network
import regional
import city
import assortment
import ip
from streamlit_option_menu import option_menu
import login


def add_custom_css():
    st.markdown(
        """
        <style>
        .st-emotion-cache-bm2z3a {
            background-image: linear-gradient(to right top, #051937, #004d7a, #008793, #00bf72, #a8eb12);
        }
        .st-emotion-cache-13ln4jf {
            padding: 20px 1rem 1rem;
        }
        h1 {
            font-family: "Source Sans Pro", sans-serif;
            font-weight: 700;
            color: rgb(49, 51, 63);
            padding: 6rem 0px 1rem;
            margin: 0px;
            line-height: 1.2;
        }
        .stSelectbox {
            z-index: 1000 !important;
        }
        .stButton>button {
            width: 100%;
            margin: 5px 0;
            background: linear-gradient(to right top, #051937, #004d7a, #008793, #00bf72, #a8eb12);
            color: white;
            border: none;
            padding: 10px;
            font-size: 16px;
            text-align: left;
        }
        .stButton>button:hover {
            background-color: green;
        }
        .navbar-container {
            display: flex;
            flex-direction: column;
            width: 250px;
            height: 100vh;
            background-color: #0e1117;
            padding: 1rem;
            position: fixed;
            top: 0;
            left: 0;
        }
        .content-container {
            margin-left: 270px;
            padding: 1rem;
        }
        .st-emotion-cache-6qob1r {
    position: relative;
    height: 100%;
    width: 100%;
    overflow: overlay;
    background: black;
}
.st-emotion-cache-12fmjuu {
    position: unset !important;
     Uncomment and adjust the following lines if you want to override other styles */
    top: unset !important; 
    left: unset !important; 
    right: unset !important; 
     height: unset !important; 
    background: unset !important; 
     outline: unset !important; 
     z-index: unset !important; 
     display: unset !important; 
}
        </style>
        """,
        unsafe_allow_html=True
    )

def home():
    st.title('Home🎢')
    st.write('Welcome to the Internal Store Transfer Data Processing and Analysis App📈')

def handle_navigation():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if not st.session_state['logged_in']:
        login.login()
    else:
        add_custom_css()
        
        with st.sidebar:
            selected = option_menu(
                menu_title=None,
                options=["Home", "Internal Store Transfer", "Assortment", "IP"],
                icons=['house', 'box', 'box', 'gear'],
                menu_icon="cast",
                default_index=0,
                orientation="vertical",
                styles={
                    "container": {"padding": "0!important", "background-color": "black"},
                    "icon": {"color": "orange", "font-size": "25px"},
                    "nav-link": {
                        "font-size": "20px",
                        "text-align": "left",
                        "margin": "0px",
                        "--hover-color": "#eee",
                    },
                    "nav-link-selected": {"background-color": "green"},
                }
            )

        st.markdown('<div class="content-container">', unsafe_allow_html=True)
        if selected == 'Home':
            home()
        elif selected == 'Internal Store Transfer':
            ist_option = st.selectbox("Select an option", ["Network", "Regional", "City"], key="ist_selectbox")
            if ist_option == 'Network':
                network.main()
            elif ist_option == 'Regional':
                regional.main()
            elif ist_option == 'City':
                city.main()
        elif selected == 'Assortment':
            assortment.main()
        elif selected == 'IP':
            ip.main()
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    handle_navigation()
