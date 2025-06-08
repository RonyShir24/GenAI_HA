import streamlit as st
import Phase1 as phase1

# ─── Initializtion ──────────────────────────────────────────────────

contentList = []

st.title("""
National Insurance Institute Information Extraction Platform
""")

st.markdown(
    """ 
    This is a platform to extrect information from the National Insurance Institute.
    Please upload a PDF/JPG file containing the information you want to extract.
    Make sure the file is in the correct format and contains the necessary information.
    The platform will return the extracted information in a Json format and eveluation metrics.
    """
)


# ─── Script pipline ──────────────────────────────────────────────────

uploaded_file = st.file_uploader("Please upload a PDF file", type=["jpg", "pdf"])

if uploaded_file is not None:
    st.write(f"File {uploaded_file.name} uploaded successfully!")
    with st.spinner("Thinking..."):
        pdf_bytes = uploaded_file.read()
        
        # Document Intelligence
        DataIntResult = phase1.readPDFfile(pdf_bytes)
                
        wordList = DataIntResult["pages"][0]["words"]

        LLM_JsonGen4O = phase1.JsonGen(DataIntResult, "gpt-4o")
        LLM_JsonGen4Omini = phase1.JsonGen(DataIntResult , "gpt-4o-mini")
        
        st.json(LLM_JsonGen4O)
        st.markdown("-------------------------------------------")
        
        
        #Validation metrics
        st.markdown("Validation Methods")
        
        
        for line in wordList:
            contentList.append(line["content"])
            
        metricRes = phase1.AccuracyCompleteness(LLM_JsonGen4O , LLM_JsonGen4Omini , contentList)
        
        st.markdown(f"Accuracy: {metricRes[0]:.2f}%")
        st.markdown(f"Completncess: {metricRes[1]:.2f}%")
        
        for error in metricRes[2]:
            if len(error) > 0:
                st.markdown(error)
    
