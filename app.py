import streamlit as st
from rag import generate_answer

st.title("🚀 NeuroSeek: AI-Powered Knowledge Retrieval & Search")

# # Search Query Input
query = st.text_input("Enter your search query:")
# relevance = st.slider("Adjust Search Relevance", 0, 100, 50)  # Adjust relevance weight

if st.button("Search"):
    if query:
        with st.spinner("Fetching results..."):
            try:
                # Generate answer
                response = generate_answer(query)
                
                # Display response
                st.write("### Answer:")
                st.write(response)

                # Human-in-the-Loop Feedback
                st.write("### 🤖 Improve AI Responses")
                feedback = st.radio("Was this answer helpful?", ["👍 Yes", "👎 No"], index=None)
                
                if feedback == "👎 No":
                    user_feedback = st.text_area("What could be improved?", "")
                    
                    if st.button("Submit Feedback"):
                        st.success("Thank you for your feedback! We'll use it to improve future results.")

                # Refinement Button
                if st.button("🔄 Regenerate Response"):
                    st.experimental_rerun()

            except Exception as e:
                st.error(f"Error: {str(e)}")
    else:
        st.warning("Please enter a search query.")
