import json
import glob
import os
import hashlib
from pathlib import Path
from databasestore import DBConnect
from models import TestRecord
from datetime import datetime, timedelta
from templatestore import Template, GenerateTemplate
from utils import getConfig
from argparse import ArgumentParser

PROJECT_PATH = Path(__file__).parents[1]

def gatherdataAndSave(input_folder_path,db_config):
    
    db_connection_obj = DBConnect(db_config)
    TestRecord.set_database_connector_object(db_connection_obj)
    TestRecord.createTable_if_not_exists()

    walking = os.walk(input_folder_path)
    available_modules = next(walking)[1]
    rec_list = []
    for a_module in available_modules:
        module_path = Path(input_folder_path) / a_module
        consolidated_module_data = {}
        consolidated_module_data['module'] = a_module

        for file in glob.iglob(f"{module_path}/**/*.json",recursive=True):
            with open(file,'r') as fd:
                data = json.load(fd)['stats']
                consolidated_module_data['passes'] = consolidated_module_data.get('passes',0) + data.get('passes')
                consolidated_module_data['pending'] = consolidated_module_data.get('pending',0) + data.get('pending')
                consolidated_module_data['failures'] = consolidated_module_data.get('failures',0) + data.get('failures')
                consolidated_module_data['duration'] = consolidated_module_data.get('duration',0) + data.get('duration')
        
        # Create a new record 
        
        record = TestRecord()
        record.module = consolidated_module_data.get('module')
        record.passes = consolidated_module_data.get('passes')
        record.pending = consolidated_module_data.get('pending')
        record.failures = consolidated_module_data.get('failures')
        record.duration = consolidated_module_data.get('duration')
        record.total = record.passes + record.pending + record.failures
        # curr_date = datetime.now().strftime('%Y-%m-%d')
        curr_date = "2022-07-01"
        record.rec_creation_data = curr_date
        unique_key = record.module.replace(" ","") + record.rec_creation_data

        hs = hashlib.md5(unique_key.encode())
        record.id = hs.hexdigest()
        record.fetch_details(where = 'id',eq=[record.id])

        if len(record.fetch_details(where = 'id',eq=[record.id])) == 0:
            record.save()
        else:            
            record.update(where='id',eq=record.id)
        print(f"saved record:-- {record}")
        rec_list.append(record)
    


def createhtmlReport(db_config,output_dir=None,last_n_days=4,template_env_path=None,tables_per_row=4):
    if not template_env_path:
        template_env_path = PROJECT_PATH / 'src/templates'

    template_processor = GenerateTemplate(template_env_path)
    db_connection_obj = DBConnect(db_config)
    TestRecord.set_database_connector_object(db_connection_obj)
    today= datetime.now()
    cal_dates = [(today-timedelta(days= day)).strftime('%Y-%m-%d') for day in range(0,last_n_days)]


    recs = TestRecord.fetch_details(where='rec_creation_data',eq=cal_dates)

    parsed__rec_data = {}

    for rec in recs:
        total = rec['total']
        module_dict = {}
        module_dict['pass%'] = round((rec['passes'] / total) * 100,2)
        module_dict['norun%'] = round((rec['pending'] / total) * 100,2)
        module_dict['fail%']= round((rec['failures'] / total) * 100,2)
        module_dict['#tt in min'] =  round((rec['duration']/1000)/60,2)
        module_dict['date'] = rec["rec_creation_data"]
        module_dict['#tc'] = total
        parsed__rec_data.setdefault(rec['module'],{}).update({rec['rec_creation_data']:module_dict})

    labels = cal_dates

    template_list = []
    for mod_name,m_data in parsed__rec_data.items():
        pass_data = [0 for i in range(len(labels))]
        pending_data = [0 for i in range(len(labels))]
        failed_data = [0 for i in range(len(labels))]

        temp_obj = Template("js_templates/bar_chart.j2")
        temp_obj.id_name = mod_name.replace(" ","")
        for index in range(len(labels)):
            if m_data.get(labels[index]):
                data = m_data[labels[index]]
                # breakpoint()
                pass_data[index] = data['pass%']
                pending_data[index] = data['norun%']
                failed_data[index] = data['fail%']

        dataset = f"""[
             {{
            label: 'pass',
            data: {pass_data},
            backgroundColor: '#50C878'
        }},{{
            label: 'fail',
            data: {pending_data},
            backgroundColor: '#F75D59'
        }},{{
            label: 'pending',
            data: {failed_data},
            backgroundColor: '#F4A460'
            }}
        ]"""

        temp_obj.data = dataset
        temp_obj.labels = labels
        temp_obj.heading = mod_name

        template_list.append(temp_obj)

    

    chart_js_code = template_processor.template_2_singleStream(template_obj_list=template_list)
    html_template_obj =  Template('html_templates/index.html')
    html_template_obj.id_name = [names.id_name for names in template_list]
    html_template_obj.today_date = datetime.now().strftime("%Y-%m-%d")
    html_template_obj.script_data = chart_js_code
    
    ### saving to file index.html

    save_to = Path(output_dir) / 'charts.html'

    ################################
    template_processor.render_and_save(html_template_obj,save_to)
    html_table = Template('html_templates/tables.html')
    html_table.records = []


    mod_seg_arr = [[0,0] for i in parsed__rec_data.keys()]
    print(len(mod_seg_arr))
    mod_seg_arr[0][0] = 1
    mod_seg_arr[-1][1] = 1
    print(len(mod_seg_arr))
    c = 0

    per_row_tables = tables_per_row

    for ind in range(len(mod_seg_arr)):
        if c == per_row_tables:
            mod_seg_arr[ind][0] = 1
            mod_seg_arr[ind-1][1] = 1
            c = 0
        c +=1


    print(mod_seg_arr)
 
    m_index=0
    header_structure = ['date','#tc','pass%', 'fail%','norun%', '#tt in min']
    for module_name,data in parsed__rec_data.items():
        # print(module_name,isnewrow,shouldrowend)
        rec_data = {
            "headers":header_structure,
            "rows":[['NA' for i in header_structure] for _ in range(len(cal_dates))],
            "module_name":module_name,
            "isnewrow": mod_seg_arr[m_index][0],
            "shouldrowend": mod_seg_arr[m_index][1]
        }
        m_index += 1

        for d_index, date in enumerate(cal_dates):
            
            val = data.get(date)
            if not val:
                date_index = header_structure.index('date')

                rec_data['rows'][d_index][date_index]= date
                continue
            for el_index,el in enumerate(header_structure):

                rec_data["rows"][d_index][el_index] = val[el]
        html_table.records.append(rec_data)

    # html_table.

    html_table.today_date = datetime.now().strftime("%Y-%m-%d")
    save_to_file = Path(output_dir) / 'tables.html'
    template_processor.render_and_save(html_table,save_to_file)
    
    

def getcli():
    parser = ArgumentParser()
    group_parser = parser.add_mutually_exclusive_group(required=True)
    group_parser.add_argument("-sv","--save2db",action="store_true",help="Fetches the data in teh input directory and stores in the set Database")
    group_parser.add_argument("-gen","--genhtml",action="store_true",help="Genereates the html report from the configured templates getting data from DB")
    group_parser.add_argument("-svgen","--saveAndGen",action="store_true",help="Fetches the data in teh input directory and stores in the set Database")

    args = parser.parse_args()
    return args 


if __name__ == "__main__":

    cli_args = getcli()
    
    config = getConfig(PROJECT_PATH/'settings.ini','global')


    # get configurations

    input_file_dir = config['input_file_dir'].strip()
    output_report_dir = config['output_report_dir'].strip()
    use_db = config['use_db'].strip()
    last_n_days = int(config['last_n_days'])
    tables_per_row = int(config['tables_per_row'].strip())
    db_conf = getConfig(PROJECT_PATH/'settings.ini',use_db)

    if input_file_dir.strip() == '':
        input_file_dir = PROJECT_PATH / 'input_data'

    if output_report_dir.strip() == '':
        output_report_dir = PROJECT_PATH / 'OUTPUT_REPORTS'
        os.makedirs(output_report_dir,exist_ok=True)
    
    ############### TODO can chenge htis into a plugin strategy pattern #########################

    if cli_args.save2db:
        gatherdataAndSave(input_file_dir,db_conf)
    elif cli_args.genhtml:
        createhtmlReport(db_conf,output_dir=output_report_dir,last_n_days=last_n_days,tables_per_row=tables_per_row)
    elif cli_args.saveAndGen:
        gatherdataAndSave(input_file_dir,db_conf)
        createhtmlReport(db_conf,output_dir=output_report_dir,last_n_days=last_n_days,tables_per_row=tables_per_row)

    ##################################################################################
