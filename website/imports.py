from flask import Blueprint,request,render_template,redirect,url_for
from openpyxl import load_workbook
from website import db_connect
from .views import get_data

imports = Blueprint('imports',__name__)

def get_partial_amount(percent,total):
    return round((float(percent)/100)*float(total),2)

@imports.route("/excel",methods=['GET','POST'])
def excel_import(mgs=None):
    if request.method == 'POST':
        upload_file = request.files['upload_serivce_datas']
        excel_file_type = request.form.get('selectExcelFile')
        view_type = request.form.get('selectView')

        conn = db_connect()
        cur = conn.cursor()

        if upload_file.filename != '' and upload_file.filename.endswith(".xlsx"):
            workbook = load_workbook(filename=upload_file,data_only=True,read_only=True)
            try:
                worksheet = workbook[excel_file_type]
            except:
                return redirect(url_for('views.show_service_datas',typ=view_type,mgs=f'The sheet name of excel import file must be <strong>{excel_file_type}..<&#47;strong>'))
            if excel_file_type == 'Jobs Data':
                eachJob_insert_query = """INSERT INTO eachJob (job_date,job_no,business_unit_id,shop_id,invoice_no,customer_id,vehicle_id,job_name,
                job_type_id,total_amt,fst_pic_id,fst_pic_amt,sec_pic_id,sec_pic_amt,thrd_pic_id,thrd_pic_amt,frth_pic_id,
                frth_pic_amt,lst_pic_id,lst_pic_amt,eachJob_concatenated) VALUES """
                cur.execute("SELECT id,name FROM technicians;")
                technicians = cur.fetchall()
                technicians = {data[1].lower():data[0] for data in technicians}
                cur.execute("SELECT id,name FROM jobType;")
                job_types = cur.fetchall()
                job_types = {data[1].lower():data[0] for data in job_types}
                cur.execute("SELECT fst_rate,sec_rate,thrd_rate,frth_rate,lst_rate FROM pic ORDER BY id DESC LIMIT 1;")
                all_rates = cur.fetchall()
                cur.execute("SELECT shop.business_unit_id,shop.id as shop_id,LOWER(unit.name),LOWER(shop.name) FROM res_partner AS unit INNER JOIN shop ON shop.business_unit_id = unit.id;")
                unit_shop_datas = cur.fetchall()
                unit_shop_dct = {data[2:]:data[:2] for data in unit_shop_datas}
                conflict_unique_column = "eachJob_concatenated"
                for row_counter,row in enumerate(worksheet.iter_rows(min_row=3),start=3):
                    if None in (row[1].value,row[2].value,row[3].value,row[4].value,row[5].value,row[6].value,row[7].value,
                                row[8].value,row[9].value,row[10].value,row[11].value,row[12].value,row[13].value,
                                row[14].value,row[15].value,row[16].value) or "" in (row[1].value,row[2].value,row[3].value,row[4].value,row[5].value,row[6].value,row[7].value,
                                row[8].value,row[9].value,row[10].value,row[11].value,row[12].value,row[13].value,
                                row[14].value,row[15].value,row[16].value,row[17].value,row[18].value):
                        return redirect(url_for('views.show_service_datas',mgs=f"Invalid or Blank field at row {row_counter}"))
                    cur.execute(""" WITH inserted AS (
                                        INSERT INTO customer (name)
                                        VALUES (%s)
                                        ON CONFLICT (name) DO NOTHING 
                                        RETURNING id
                                    )
                                    SELECT id FROM inserted
                                    UNION ALL
                                    SELECT id FROM customer WHERE LOWER(name) = %s
                                    LIMIT 1;""",(row[4].value.upper(),row[4].value.lower()))
                    cus_id = cur.fetchall()
                    unit_shop_ids = unit_shop_dct.get((row[17].value.strip().lower(),row[18].value.strip().lower()))
                    if not unit_shop_ids:
                        return redirect(url_for('views.show_service_datas',mgs=f"Invalid or Blank Business Unit at row {row_counter}"))
                    concatenated_vehicle = row[5].value.strip().upper() + row[6].value.strip().upper() + str(row[7].value).strip()
                    cur.execute(""" WITH inserted AS (
                                        INSERT INTO vehicle (customer_id,plate,model,year,vehicle_concatenated)
                                        VALUES (%s,%s,%s,%s,%s)
                                        ON CONFLICT (vehicle_concatenated) DO NOTHING 
                                        RETURNING id
                                    )
                                    SELECT id FROM inserted
                                    UNION ALL
                                    SELECT id FROM vehicle WHERE LOWER(vehicle_concatenated) = %s 
                                    LIMIT 1;""",(cus_id[0][0],row[5].value.strip().upper(),row[6].value.strip().upper(),row[7].value,concatenated_vehicle,concatenated_vehicle.lower()))
                    vehicle_id = cur.fetchall()
                    if row[10].value.strip().lower() not in job_types:
                        return redirect(url_for('views.show_service_datas',mgs=f"Invalid Job Type at row -  {row_counter}"))                    
                    fst_tech,sec_tech,thrd_tech,frth_tech,lst_tech = row[12].value.strip().lower(),row[13].value.strip().lower(),row[14].value.strip().lower(),row[15].value.strip().lower(),row[16].value.strip().lower()
                    if fst_tech not in technicians or sec_tech not in technicians or thrd_tech not in technicians or frth_tech not in technicians or lst_tech not in technicians:
                        return redirect(url_for('views.show_service_datas',mgs=f"Invalid PIC Name at row - {row_counter}"))
                    eachJob_concatenated = row[2].value.strftime("%d/%m/%Y") + row[3].value + row[9].value
                    eachJob_insert_query += f"""('{row[2].value}','{row[3].value}','{unit_shop_ids[0]}','{unit_shop_ids[1]}','{row[8].value}','{cus_id[0][0]}','{vehicle_id[0][0]}','{row[9].value}','{job_types[row[10].value.strip().lower()]}','{int(row[11].value):.2f}','{technicians[fst_tech]}','{get_partial_amount(all_rates[0][0],row[11].value)}','{technicians[sec_tech]}','{get_partial_amount(all_rates[0][1],row[11].value)}','{technicians[thrd_tech]}','{get_partial_amount(all_rates[0][2],row[11].value)}','{technicians[frth_tech]}','{get_partial_amount(all_rates[0][3],row[11].value)}','{technicians[lst_tech]}','{get_partial_amount(all_rates[0][4],row[11].value)}','{eachJob_concatenated}'),"""
                cur.execute(eachJob_insert_query[:-1] + f" ON CONFLICT ({conflict_unique_column}) DO NOTHING;")
                conn.commit()    
                cur.close()
                conn.close()
                return redirect(url_for('views.show_service_datas',typ='service-datas'))            
            elif excel_file_type == 'Types Data':
                eachJob_insert_query = "INSERT INTO jobType (name) VALUES "
                conflict_unique_column = "name"
                for row_counter,row in enumerate(worksheet.iter_rows(min_row=2),start=2):
                    eachJob_insert_query += f"('{row[0].value}'),"
            elif excel_file_type == 'Technicians': 
                eachJob_insert_query = "INSERT INTO technicians (name) VALUES "
                conflict_unique_column = "name"
                for row_counter,row in enumerate(worksheet.iter_rows(min_row=2),start=2):
                    eachJob_insert_query += f"('{row[0].value}'),"
            cur.execute(eachJob_insert_query[:-1] + f" ON CONFLICT ({conflict_unique_column}) DO NOTHING;")
            conn.commit()
        cur.close()
        conn.close()
    return "Successfully Imported Excel File"

@imports.route("/create-form/<typ>")
def show_create_form(typ,mgs=None):
    conn = db_connect()
    cur = conn.cursor()
    result = []
    if typ == 'service-datas':
        cur.execute("SELECT plate FROM vehicle;")
        result.append(cur.fetchall())
        cur.execute("SELECT id,name FROM res_partner;")
        result.append(cur.fetchall())
        cur.execute("SELECT id,name FROM shop;")
        result.append(cur.fetchall())
        cur.execute("SELECT id,name FROM technicians;")
        result.append(cur.fetchall())
        cur.execute("SELECT id,name FROM jobType;")
        result.append(cur.fetchall())
        cur.execute("SELECT id,unique_rate FROM pic;")
        result.append(cur.fetchall())
    return render_template('input_form.html',result=result,mgs=mgs)

@imports.route("/keep-in-import/<typ>",methods=['POST'])
def keep_in_import(typ):
    if request.method == 'POST':
        conn = db_connect()
        cur = conn.cursor()
        if typ == 'service-datas':
            conflict_unique_column = 'eachjob_concatenated'
            eachJob_insert_query = """ INSERT INTO eachJob (job_date,job_no,business_unit_id,shop_id,invoice_no,customer_id,vehicle_id,job_name,
                job_type_id,total_amt,fst_pic_id,fst_pic_amt,sec_pic_id,sec_pic_amt,thrd_pic_id,thrd_pic_amt,frth_pic_id,
                frth_pic_amt,lst_pic_id,lst_pic_amt,eachJob_concatenated) VALUES """
            edit = request.form.get("newOrEdit")
            if edit:
                print(get_data('eachJobDelForm',request.form.get("jobNo")))
            #
            vehicle_id = request.form.get("vehicleInformation")
            plate = request.form.get("plate")
            model = request.form.get("model")
            year = request.form.get("modelYear")
            cus_name = request.form.get("customerName")
            #
            if vehicle_id == '-100':
                print("nani")
                cur.execute(""" WITH inserted AS (
                    INSERT INTO customer (name)
                    VALUES (%s)
                    ON CONFLICT (name) DO NOTHING 
                    RETURNING id
                )
                SELECT id FROM inserted
                UNION ALL
                SELECT id FROM customer WHERE LOWER(name) = %s
                LIMIT 1;""",(cus_name.upper(),cus_name.lower()))
                cus_id = cur.fetchall()[0][0]
                concatenated_vehicle = plate.strip().upper() + model.strip().upper() + year.strip()
                cur.execute(""" WITH inserted AS (
                                    INSERT INTO vehicle (customer_id,plate,model,year,vehicle_concatenated)
                                    VALUES (%s,%s,%s,%s,%s)
                                    ON CONFLICT (vehicle_concatenated) DO NOTHING 
                                    RETURNING id
                                )
                                SELECT id FROM inserted
                                UNION ALL
                                SELECT id FROM vehicle WHERE LOWER(vehicle_concatenated) = %s 
                                LIMIT 1;""",(cus_id,plate.strip().upper(),model.strip().upper(),year.strip(),concatenated_vehicle,concatenated_vehicle.lower()))
                vehicle_id = cur.fetchall()[0][0]
            else:
                cur.execute("SELECT customer_id FROM vehicle WHERE id = %s;",(vehicle_id,))
                cus_id = cur.fetchall()[0][0]
            #
            job_no = request.form.get("jobNo")
            invoice_no = request.form.get("invoiceNo")
            job_date = request.form.get("jobDate")
            shop_id = request.form.get("shopID").split("|")[1].strip()
            unit_id = request.form.get("unitID").split("|")[1].strip()
            #
            descriptions = request.form.getlist("description")[1:]
            job_types = [data.strip() for data in request.form.getlist('jobType')[1:]]
            #
            # print(request.form.getlist("picOne"))
            # print(request.form.getlist("picTwo"))
            # print(request.form.getlist("picThree"))
            # print(request.form.getlist("picFour"))
            # print(request.form.getlist("picFive"))
            pic_ones = [data.split("|")[1].strip() if "|" in data else 0 for data in request.form.getlist("picOne")[1:] ]
            pic_twos = [data.split("|")[1].strip() if "|" in data else 0 for data in request.form.getlist("picTwo")[1:] ]
            pic_threes = [data.split("|")[1].strip() if "|" in data else 0 for data in request.form.getlist("picThree")[1:] ]
            pic_fours = [data.split("|")[1].strip() if "|" in data else 0 for data in request.form.getlist("picFour")[1:] ]
            pic_fives = [data.split("|")[1].strip() if "|" in data else 0 for data in request.form.getlist("picFive")[1:] ]
            pic_rates = [data.split(",") for data in request.form.getlist("pic-rate")[1:]]
            print(pic_rates)
            # print(pic_ones)
            # print(pic_twos)
            # print(pic_threes)
            # print(pic_fours)
            # print(pic_fives)
            #
            job_costs = request.form.getlist("jobCost")[1:]
            for data in zip(descriptions,job_types,pic_ones,pic_twos,pic_threes,pic_fours,pic_fives,job_costs,pic_rates):
                print(data)
                eachJob_concatenated = job_date.replace("-","/") + job_no + data[0]
                eachJob_insert_query += f"""('{job_date}','{job_no}','{unit_id}','{shop_id}','{invoice_no}','{cus_id}','{vehicle_id}','{data[0]}',
                '{data[1]}','{data[7]}','{data[2]}','{get_partial_amount(data[8][0],data[7])}','{data[3]}','{get_partial_amount(data[8][1],data[7])}','{data[4]}','{get_partial_amount(data[8][2],data[7])}','{data[5]}','{get_partial_amount(data[8][3],data[7])}','{data[6]}','{get_partial_amount(data[8][4],data[7])}','{eachJob_concatenated}'),"""
            cur.execute(eachJob_insert_query[:-1] + f" ON CONFLICT ({conflict_unique_column}) DO NOTHING;")
        elif typ == 'pic-rate':
            idd = request.form.get("idd")
            rates = request.form.getlist('rate')
            if idd:
                rates = rates[5:]
            rates = [rate.strip() for rate in rates]
            rates.append(','.join(rates))
            if not idd:
                cur.execute(f"INSERT INTO pic (fst_rate,sec_rate,thrd_rate,frth_rate,lst_rate,unique_rate) VALUES {tuple(rates)} ON CONFLICT (unique_rate) DO NOTHING;")
            else:
                cur.execute(f""" UPDATE pic SET fst_rate = {rates[0]},sec_rate = {rates[1]},thrd_rate = {rates[2]},frth_rate = {rates[3]},lst_rate = {rates[4]},unique_rate = '{rates[5]}' WHERE id = {idd} AND NOT EXISTS (SELECT 1 FROM pic WHERE unique_rate = '{rates[5]}'); """)
        elif typ == 'technician':
            idd = request.form.get("idd")
            tech_name  = request.form.getlist("tech")
            if idd:
                cur.execute(f""" UPDATE technicians SET name = '{tech_name[1]}' WHERE id = '{idd}' and NOT EXISTS ( SELECT 1 FROM technicians WHERE name = '{tech_name[1]}');""")
            else:
                 cur.execute(f""" INSERT INTO technicians (name) VALUES ('{tech_name[0]}') ON CONFLICT (name) DO NOTHING;""")
        elif typ == 'jobType':
            idd = request.form.get("idd")
            job_type = request.form.getlist("jobType")
            if idd:
                cur.execute(f""" UPDATE jobType SET name = '{job_type[1]}' WHERE id = '{idd}' and NOT EXISTS ( SELECT 1 FROM jobtype WHERE name = '{job_type[1]}');""")
            else:
                 cur.execute(f""" INSERT INTO jobType (name) VALUES ('{job_type[0]}') ON CONFLICT (name) DO NOTHING;""")
        conn.commit()
    return redirect(url_for('views.show_service_datas',typ=typ))