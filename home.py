import streamlit as st
from datetime import datetime
import pandas as pd
from glob import glob
from utils import get_config_data
st.set_page_config(layout="wide")

def process_file():
        st.title("GT-Motive")
        tab1, tab2 = st.tabs(["Single Record", "Multi Records"])
        log_datetime = datetime.now().strftime("%d-%m-%y::%H:%M:%S")
        org_labels = df_label.split("\n")
        current_stamp = datetime.now().strftime("%d%m%y%H%M%S")
## ----------------------------------------------Single Record-----------------------------------------------
        with tab1:
            try:
                with st.form("get_data"):
                    txt = st.text_input("Please enter the input for prediction")
                    submitted = st.form_submit_button("Predict")
                    if submitted:
                        form_data = txt.split("\t")
                        if len(form_data) == len(org_labels):
                            write_log(f"{log_datetime} - Input - {form_data}","INFO")
                            # form_data = ["Unknown" if value.strip() == "" else value for value in form_data]
                            form_dict = dict(zip(org_labels,form_data))
                            df = pd.DataFrame([form_dict])
                            prep_status,df = preprocess_input(df,org_labels)
                            status, result_data = quantity_rules(df,org_labels,"text")
                            if status:
                                write_log(f"{log_datetime} - Output - {list(result_data['Predicted_CUPI_Code'])}","INFO")
                                st.write(f'## Predicted CUPI code')
                                st.write(result_data)

                            else:
                                write_log(result_data,"ERROR")
                                st.error(result_data)
                        else:
                            st.error("Please enter the valid string (length mismatched)...")

            except:
                error = get_except_report(sys.exc_info())
                write_log(error,"ERROR")
                st.error(error)
## ----------------------------------------------Multiple Records-----------------------------------------------

        with tab2:
            radio_val = None
            data_status = False
            mode = "file"
            uploaded_file = st.file_uploader("Choose a file",type="xlsx")
            submitted = st.button("Predict",type="primary")
            mode = "file"
            labels = org_labels
            if (uploaded_file is not None) and submitted:
                org_df = pd.ExcelFile(uploaded_file).parse(0)
                data_status = True
                
            # if radio_val != None or not db_status:
            if data_status:
                try:
                    prep_status,df = preprocess_input(org_df,labels,mode)
                    if not prep_status:
                        raise Exception(df)
                    process_date = datetime.now().strftime("%d-%m-%y")
                    upload_path = excel_path+process_date
                    os.makedirs(upload_path, exist_ok=True)
                    if len(glob(f"{upload_path}/*.xlsx")) < int(request_limit):
                        file_name = "Processed_Output_"
                        if sorted(labels) == sorted(df.columns.to_list()):
                            if len(df) > 500 or len(df) < 1:
                                write_log(f"{file_name} - Excel has no records or has more than 500 records...","ERROR")
                                st.error("Excel has no records or has more than 500 records...")
                            else:
                                with st.spinner("Processing please wait..."):
                                    write_log(f"{log_datetime} - {file_name} - Total records - {len(df)}","INFO")
                                    status, result_data = quantity_rules(df,org_labels,'file')

                                    if not status:
                                        write_log(result_data,"ERROR")
                                        st.error(result_data)
                                    else:
                                        st.success("Process Completed", icon="✅")
                                        st.header("Processed Data")
                                        st.download_button(label='📥 Download',
                                                                data=to_excel(result_data) ,
                                                                file_name= f"{file_name}_{current_stamp}.xlsx")
                                        st.write(result_data)
                                        ## saving excel in host machine
                                        result_data.to_excel(f"{upload_path}/{file_name}_{current_stamp}.xlsx",index=False)

                        else:
                            write_log(f"{file_name} - Column names mismatched...","ERROR")
                            st.error("Column names mismatched...")
                    else:
                        write_log(f"The daily request limit has been reached....","ERROR")
                        st.error("The daily request limit has been reached....")
                except:
                    error = get_except_report(sys.exc_info())
                    write_log(error,"ERROR")
                    st.error(error)


if __name__ == "__main__":
    config_status, msg = get_config_data()
    if config_status:
        from utils import *
        write_log("------------------------------------------------------------------","INFO")
        process_file()
    else:
        st.error(msg)


    