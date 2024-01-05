import pickle
from configparser import ConfigParser
import os
import sys
from io import BytesIO
import pandas as pd
from datetime import datetime
import numpy as np
import re

def write_log(msg,msg_level):
    log_date = datetime.now().strftime("%d-%m-%y")
    log_time = datetime.now().strftime("%H")
    log_file_path = f"{log_path}/{log_date}"
    os.makedirs(log_file_path, exist_ok=True)
    filename=f"{log_file_path}/{log_time}.txt"
    with open(filename,"a") as f:
        f.write(f"\n{msg_level}::{msg}")

def get_except_report(err_data):
    exc_type, exc_obj, exc_tb = err_data
    msg = exc_obj.args[0]
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    error_time = datetime.now().strftime("%d-%m-%y::%H:%M:%S")
    error = f"{error_time} | {msg} | {str(fname)} | {str(exc_tb.tb_lineno)}"
    return error


def get_config_data():
    try:
        config_file = "config.ini"
        if not os.path.isfile(config_file):
            raise Exception("Config file not found...")
        config = ConfigParser()
        config.read(config_file)
        for section in config.sections():
            for field in config.options(str(section)):
                globals()[field]= str(config.get(str(section),field))
        return 1, ""
    except:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        msg = exc_obj.args[0]
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        error = f"{config_file} - {msg} | {str(fname)} | line no. - {str(exc_tb.tb_lineno)}"
        return 0, error

def preprocess_input(df,labels,mode = None):
    try:
        df.fillna("",inplace = True)
        df['DIREF_CANT_FAB'] = df['DIREF_CANT_FAB'].apply(lambda x: 1 if (x == "" or int(x) == 0) else x)
        # df["INFOAUXFABRIC"] = df["INFOAUXFABRIC"].apply(lambda x: "INFOAUXFABRIC is " + str(x) if x != '' else x).astype(str)
        # df["NOTAS"] = df["NOTAS"].apply(lambda x: "NOTAS is " + str(x) if x != '' else x).astype(str)
        # df = df.astype(str)
        df = df[labels]
        if mode != "db":
            df[labels[:-1]] = df[labels[:-1]].astype(str)
        return 1,df
    except Exception as e:
        return 0,get_except_report(sys.exc_info())

def get_result(df,labels):
    try:
        model = pickle.load(open(model_path,'rb'))
        vectorizer = pickle.load(open(vectorizer_path,'rb'))
        df["predictions_by_model"] = ''
        # df['prob_score'] = 0
        for i, row in df[labels[:-1]].iterrows():
            try:
                concat_data = ", ".join(row)
                X_test_cv = vectorizer.transform([concat_data])
                predictions = model.predict(X_test_cv)
                df.loc[i,"predictions_by_model"] = predictions[0]
                # y_pred_proba = model.predict_proba(X_test_cv)
                # get_max_percentage = lambda scores: scores[np.argmax(scores)]
                # percentages = list(map(get_max_percentage, y_pred_proba))
                # df['prob_score'].iloc[i] = f"{int(percentages[0]*100)}%"
            except:
                df.loc[i,"predictions_by_model"] = ""
        return 1, df
    
    except:
        error = get_except_report(sys.exc_info())
        return 0, error

def process_row(pred,con_str):
    right_pattern = re.compile(right_words, flags=re.IGNORECASE)
    left_pattern = re.compile(left_words, flags=re.IGNORECASE)
    if pred.endswith(("L", "R")) and len(pred) == 5:
        if right_pattern.search(con_str):
            return pred[0:4] + "R"
        elif left_pattern.search(con_str):
            return pred[0:4] + "L"
        else:
            return pred
    else:
        return pred

def quantity_rules(input_df,labels,mode):
    status, df = get_result(input_df,labels)
    if status:
        try:
            # left_right_rules = list(map(process_row, df.itertuples(index=False)))
            rule_labels = rule_label.split(",")
            rule_df = pd.read_excel(rules_file)
            rule_df[rule_labels[1]] = rule_df[rule_labels[1]].apply(eval)
            rule_df[rule_labels[0]] = rule_df[rule_labels[0]].apply(str) #**********************
            output_values=[]
            mapping_dict = rule_df.set_index(rule_labels[0])[rule_labels[1]].to_dict()
            for index,row in df.iterrows():
                con_str = ", ".join(df[labels[:-1]].iloc[index])
                prediction = process_row(row["predictions_by_model"],con_str)
                possible_cupis= mapping_dict.get(prediction, prediction)
                quantity_sold = row[labels[-1]]
                duplication_frequency = min(len(possible_cupis),int(quantity_sold))
                if duplication_frequency==1:#*******************
                    output_values.append(prediction)
                else:
                    output_values.append(possible_cupis[0:int(duplication_frequency)])
            df["Predicted_CUPI_Code"] = output_values
            df.drop(columns = ['predictions_by_model'], inplace=True)
            df_exploded = df.explode('Predicted_CUPI_Code')
            df_exploded.reset_index(drop=True,inplace=True)
            df_exploded.rename(columns = {'DIREF_PIE_COD_CD':'Actual_CUPI_Code'}, inplace = True)
            # df_exploded['Prob_Distribution'] = df_exploded.pop('prob_score')
            return 1, df_exploded
        
        except:
            error = get_except_report(sys.exc_info())
            return 0, error
    else:
        return status, df

def to_excel(df):
    """
    Method : Convert the dataframe to byte object.
    Arguments : Dataframe.
    Return : returns byte value of the dataframe.
    """
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    writer.close()
    processed_data = output.getvalue()
    return processed_data
