OBA ANALYSIS WITH NLP - VS CODE PROJECT

FILES
- app.py: Main Streamlit application
- sample_students.csv: Sample student marks and feedback dataset
- requirements.txt: Required Python packages
- README.txt: Run instructions

RUN ON WINDOWS
1. Extract this ZIP file.
2. Open the extracted oba_analysis_nlp_project folder in VS Code.
3. Open Terminal > New Terminal.
4. Install packages:
   python -m pip install -r requirements.txt
5. Run the app:
   python -m streamlit run app.py
6. Open the local URL printed in the terminal.

If "python" does not work, try using "py" instead:
   py -m pip install -r requirements.txt
   py -m streamlit run app.py

HOW TO USE
- Open the app in the browser.
- Click the sample CSV download button, or upload sample_students.csv from this folder.
- The dashboard calculates CO attainment, example PO attainment, and English feedback sentiment.
- Download the generated CSV reports from the app.

IMPORTANT
- PO mapping is an example. Update it to your institution's official CO-PO mapping.
- TextBlob is a basic English sentiment tool and may not understand Tamil/Tanglish feedback reliably.
