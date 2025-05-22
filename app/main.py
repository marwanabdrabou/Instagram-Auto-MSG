import streamlit as st
import time
import random
import threading
from datetime import datetime, time as dt_time
import pandas as pd
from config import DEFAULT_SETTINGS, RESULTS_FILE
from modules.browser import InstagramBrowser
from modules.file_Io import FileManager
from modules.scheduler import Scheduler

# Initialize session state
def init_session_state():
    if 'sent_profiles' not in st.session_state:
        st.session_state.sent_profiles = set()
    if 'messages_sent' not in st.session_state:
        st.session_state.messages_sent = 0
    if 'scheduled_tasks' not in st.session_state:
        st.session_state.scheduled_tasks = []
    if 'running' not in st.session_state:
        st.session_state.running = False
    if 'scheduler' not in st.session_state:
        st.session_state.scheduler = Scheduler()

# Custom CSS styling
def load_css():
    with open("app/assets/styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Main application
def main():
    init_session_state()
    load_css()

    st.title("Instagram Acquisition")
    st.markdown("Automate personalized messages to Instagram profiles with scheduling")
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["⚙️ Configuration", "⏰ Scheduler", "📊 Results"])
    
    with tab1:
        render_configuration_tab()
    
    with tab2:
        render_scheduler_tab()
    
    with tab3:
        render_results_tab()

def render_configuration_tab():
    """
    
    Render the configuration tab

    """
    with st.form("config_form"):
        st.subheader("Account Information")
        col1, col2 = st.columns(2)
        with col1:
            username = st.text_input("Instagram Username", placeholder="your_username")
        with col2:
            password = st.text_input("Instagram Password", type="password", placeholder="••••••••")
        
        st.subheader("Message Content")
        message_text = st.text_area("Message to Send", height=150,
                                  placeholder="Hi there! I wanted to reach out about...")
        
        st.subheader("Sending Settings")
        col1, col2, col3 = st.columns(3)
        with col1:
            max_messages = st.number_input("Max Messages/Day", min_value=1, value=DEFAULT_SETTINGS['max_messages'],
                                         help="Maximum messages to send in 24 hours")
        with col2:
            time_interval = st.number_input("Batch Interval (sec)", min_value=60, 
                                          value=DEFAULT_SETTINGS['time_interval'],
                                          help="Time between batches of messages")
        with col3:
            cooldown_min = st.number_input("Min Cooldown (min)", min_value=1, 
                                         value=DEFAULT_SETTINGS['cooldown_min'])
        
        col1, col2 = st.columns(2)
        with col1:
            cooldown_max = st.number_input("Max Cooldown (min)", min_value=cooldown_min, 
                                         value=DEFAULT_SETTINGS['cooldown_max'])
        with col2:
            uploaded_file = st.file_uploader("Upload Excel File", type=['xlsx', 'csv'],
                                           help="File must contain a 'URL' column with Instagram profile links")
        
        submitted = st.form_submit_button("🚀 Start Sending Messages")
    
    if submitted:
        handle_config_submission(username, password, message_text, max_messages, 
                               time_interval, cooldown_min, cooldown_max, uploaded_file)

def handle_config_submission(username, password, message_text, max_messages, 
                           time_interval, cooldown_min, cooldown_max, uploaded_file):
    """
    
    Handle form submission from configuration tab
    
    """
    if not all([username, password, message_text]):
        st.error("Please fill all required fields")
        return
    
    if uploaded_file is None:
        st.error("Please upload an Excel file with profile URLs")
        return
    
    try:
        profiles = FileManager.load_profiles(uploaded_file)
        st.session_state.profiles = profiles
        st.session_state.config = {
            'username': username,
            'password': password,
            'message': message_text,
            'max_messages': max_messages,
            'time_interval': time_interval,
            'cooldown_min': cooldown_min,
            'cooldown_max': cooldown_max,
            'message_delay': (10, 30)  # Default message delay
        }
        
        # Start sending in a separate thread
        threading.Thread(
            target=run_message_campaign,
            args=(profiles, st.session_state.config),
            daemon=True
        ).start()
        
        st.success("Message campaign started! Check the Results tab for progress.")
    
    except Exception as e:
        st.error(f"Error: {str(e)}")

def run_message_campaign(profiles, config):

    """
    Run the message sending campaign
    """
    
    browser = InstagramBrowser()
    try:
        FileManager.init_results_file()
        st.session_state.sent_profiles = FileManager.load_sent_profiles()
        st.session_state.messages_sent = 0
        st.session_state.running = True
        
        if not browser.login(config['username'], config['password']):
            st.error("Login failed - check your credentials")
            return
        
        start_time = time.time()
        
        for profile in profiles:
            if not st.session_state.running:
                break
                
            if st.session_state.messages_sent >= config['max_messages']:
                st.info(f"Reached daily message limit ({config['max_messages']})")
                break
                
            if profile not in st.session_state.sent_profiles:
                success = browser.send_message(profile, config['message'])
                status = "Success" if success else "Failed"
                FileManager.record_result(
                    profile,
                    status,
                    config['message'],
                    "" if success else "Failed to send message"
                )
                
                if success:
                    st.session_state.messages_sent += 1
                    st.session_state.sent_profiles.add(profile)
                
                # Update progress
                progress = (st.session_state.messages_sent / config['max_messages']) * 100
                st.session_state.progress = progress
                
                # Check if we need to cooldown
                if time.time() - start_time > config['time_interval']:
                    cooldown = random.uniform(config['cooldown_min']*60, config['cooldown_max']*60)
                    time.sleep(cooldown)
                    start_time = time.time()
                
                # Random delay between messages
                delay = random.uniform(*config['message_delay'])
                time.sleep(delay)
    
    finally:
        browser.close()
        st.session_state.running = False

def render_scheduler_tab():
    
    """
    Render the scheduler tab
    """
    
    st.subheader("Schedule Daily Runs")
    
    with st.form("schedule_form"):
        col1, col2 = st.columns(2)
        with col1:
            schedule_time = st.time_input("Run at this time daily", dt_time(9, 0))
        with col2:
            st.write("")  # Spacer
            st.write("")  # Spacer
            add_schedule = st.form_submit_button("➕ Add Schedule")
    
    if add_schedule:
        if 'config' not in st.session_state:
            st.error("Please configure and submit the settings first")
        else:
            new_task = {
                'time': schedule_time.strftime("%H:%M"),
                **st.session_state.config
            }
            st.session_state.scheduler.add_task(new_task)
            st.session_state.scheduled_tasks.append(new_task)
            st.success(f"Scheduled to run daily at {schedule_time.strftime('%H:%M')}")
    
    # Display current schedules
    st.subheader("Active Schedules")
    if not st.session_state.scheduled_tasks:
        st.info("No schedules set up yet")
    else:
        for i, task in enumerate(st.session_state.scheduled_tasks):
            with st.expander(f"Schedule {i+1} - {task['time']}"):
                st.write(f"⏰ Time: {task['time']}")
                st.write(f"👤 Account: {task['username']}")
                st.write(f"✉️ Message: {task['message'][:50]}...")
                st.write(f"🔢 Max messages: {task['max_messages']}")
                
                if st.button(f"❌ Remove Schedule {i+1}", key=f"remove_{i}"):
                    st.session_state.scheduler.remove_task(i)
                    st.session_state.scheduled_tasks.pop(i)
                    st.rerun()

def render_results_tab():
    
    """
    Render the results tab
    """
    
    st.subheader("Message Sending Results")
    
    # Display progress if running
    if st.session_state.get('running', False):
        progress = st.session_state.get('progress', 0)
        st.progress(int(progress))
        st.write(f"Messages sent: {st.session_state.get('messages_sent', 0)}")
    
    # Display results table
    results_df = FileManager.get_results_df()
    if not results_df.empty:
        st.dataframe(results_df, height=500)
        
        # Download button
        csv = results_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Full Results",
            data=csv,
            file_name='instagram_message_results.csv',
            mime='text/csv'
        )
    else:
        st.info("No results to display yet. Run the message sender to see results here.")
    
    # Stop button if running
    if st.session_state.get('running', False):
        if st.button("🛑 Stop Sending Messages"):
            st.session_state.running = False
            st.success("Message sending stopped")

if __name__ == "__main__":
    main()