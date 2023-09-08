from flask import Blueprint,request,render_template,redirect,url_for
from openpyxl import load_workbook
from website import db_connect
from .views import get_data
from datetime import datetime

imports = Blueprint('imports',__name__)

def get_partial_amount(percent,total):
    return round((float(percent)/100)*float(total),2)

@imports.route("/excel",methods=['GET','POST'])
def excel_import():
    if request.method == 'POST':
        upload_file = request.files['upload_serivce_datas']
        excel_file_type = request.form.get('selectExcelFile')
        view_type = request.form.get('selectView')

        if upload_file.filename != '' and upload_file.filename.endswith(".xlsx"):
            workbook = load_workbook(filename=upload_file,data_only=True,read_only=True)
            try:
                worksheet = workbook[excel_file_type]
            except:
                return redirect(url_for('views.show_service_datas',typ=view_type,mgs=f'The sheet name of excel import file must be <strong>{excel_file_type}..<&#47;strong>'))
            conn = db_connect()
            cur = conn.cursor()
            if excel_file_type == 'Jobs Data':
                eachJob_insert_query = """INSERT INTO eachJob (job_date,job_no,business_unit_id,shop_id,invoice_no,customer_id,vehicle_id,job_name,
                job_type_id,total_amt,fst_pic_id,fst_pic_amt,sec_pic_id,sec_pic_amt,thrd_pic_id,thrd_pic_amt,frth_pic_id,
                frth_pic_amt,lst_pic_id,lst_pic_amt,eachJob_concatenated,pic_rate_id,ownership_id) VALUES """
                cur.execute("SELECT id,name FROM technicians;")
                technicians = cur.fetchall()
                technicians = {data[1].lower():data[0] for data in technicians}
                cur.execute("SELECT id,name FROM jobType;")
                job_types = cur.fetchall()
                job_types = {data[1].lower():data[0] for data in job_types}
                cur.execute("SELECT fst_rate,sec_rate,thrd_rate,frth_rate,lst_rate,unique_rate,id FROM pic ORDER BY id;")
                all_rates = {data[5]:[data[:5],data[6]] for data in cur.fetchall()}
                cur.execute("SELECT shop.business_unit_id,shop.id as shop_id,LOWER(unit.name),LOWER(shop.name) FROM res_partner AS unit INNER JOIN shop ON shop.business_unit_id = unit.id;")
                unit_shop_datas = cur.fetchall()
                print(unit_shop_datas)
                unit_shop_dct = {data[2:]:data[:2] for data in unit_shop_datas}
                conflict_unique_column = "eachJob_concatenated"
                for row_counter,row in enumerate(worksheet.iter_rows(min_row=3),start=2):
                    if None in (row[1].value,row[2].value,row[3].value,row[4].value,row[5].value,row[6].value,row[7].value,
                                row[8].value,row[9].value,row[10].value,row[11].value,row[12].value,row[13].value,
                                row[14].value,row[15].value,row[16].value,row[17].value,row[18].value,row[19].value) or "" in (row[1].value,row[2].value,row[3].value,row[4].value,row[5].value,row[6].value,row[7].value,
                                row[8].value,row[9].value,row[10].value,row[11].value,row[12].value,row[13].value,
                                row[14].value,row[15].value,row[16].value,row[17].value,row[18].value,row[19].value):
                        return redirect(url_for('views.show_service_datas',typ=view_type,mgs=f"Invalid or Blank field at row {row_counter}"))
                    if row[19].value.strip() not in all_rates:
                        return redirect(url_for('views.show_service_datas',typ=view_type,mgs=f"Invalid or Unregistered PIC Rate at row {row_counter}"))                        
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
                    cus_id = cur.fetchall()[0][0]
                    unit_shop_ids = unit_shop_dct.get((row[17].value.strip().lower(),row[18].value.strip().lower()))
                    if not unit_shop_ids:
                        return redirect(url_for('views.show_service_datas',typ=view_type,mgs=f"Invalid or Blank Business Unit at row {row_counter}"))
                    elif unit_shop_ids[1] not in request.cookies.get("user_roles").split(","):
                        return redirect(url_for('views.show_service_datas',typ=view_type,mgs=f"You don't have enough access to import for {row[18].value.strip()}"))
                    cur.execute("SELECT id,brand_id FROM vehicle_model WHERE name = %s;",(row[6].value.strip(),))
                    idds = cur.fetchone()
                    if not idds:
                        return redirect(url_for('views.show_service_datas',typ=view_type,mgs=f"Invalid or Unregistered Vehicle Model at row {row_counter}"))                        
                    cur.execute(""" WITH inserted AS (
                                        INSERT INTO vehicle (plate,model_id,brand_id,year)
                                        VALUES (%s,%s,%s,%s)
                                        ON CONFLICT (plate) DO NOTHING 
                                        RETURNING id
                                    )
                                    SELECT id FROM inserted
                                    UNION ALL
                                    SELECT id FROM vehicle WHERE LOWER(plate) = %s 
                                    LIMIT 1;""",(row[5].value.strip().upper(),idds[0],idds[1],row[7].value,row[5].value.strip().lower()))
                    vehicle_id = cur.fetchall()[0][0]
                    print(vehicle_id,cus_id)
                    cur.execute(""" WITH inserted AS (
                                        INSERT INTO ownership (vehicle_id,customer_id,unique_owner)
                                        VALUES (%s,%s,%s)
                                        ON CONFLICT (unique_owner) DO NOTHING 
                                        RETURNING id
                                    )
                                    SELECT id FROM inserted
                                    UNION ALL
                                    SELECT id FROM ownership WHERE unique_owner = %s 
                                    LIMIT 1;""",(vehicle_id,cus_id,f"{vehicle_id}-{cus_id}",f"{vehicle_id}-{cus_id}"))
                    ownership_id = cur.fetchall()[0][0]
                    cur.execute("INSERT INTO psfu (job_no,job_date,shop_id,psfu_concatenated) VALUES (%s,%s,%s,%s) ON CONFLICT (psfu_concatenated) DO NOTHING;",(row[3].value,row[2].value.strftime("%Y/%m/%d"),unit_shop_ids[1],row[3].value+row[2].value.strftime("%Y/%m/%d")+unit_shop_ids[1]))
                    if row[10].value.strip().lower() not in job_types:
                        return redirect(url_for('views.show_service_datas',typ=view_type,mgs=f"Invalid Job Type at row -  {row_counter}"))                    
                    fst_tech,sec_tech,thrd_tech,frth_tech,lst_tech = row[12].value.strip().lower(),row[13].value.strip().lower(),row[14].value.strip().lower(),row[15].value.strip().lower(),row[16].value.strip().lower()
                    if fst_tech not in technicians or sec_tech not in technicians or thrd_tech not in technicians or frth_tech not in technicians or lst_tech not in technicians:
                        return redirect(url_for('views.show_service_datas',typ=view_type,mgs=f"Invalid PIC Name at row - {row_counter}"))
                    rate = all_rates[row[19].value.strip()]
                    eachJob_concatenated = row[2].value.strftime("%Y/%m/%d") + row[3].value + row[9].value + str(unit_shop_ids[1])
                    print(eachJob_concatenated)
                    eachJob_insert_query += f"""('{row[2].value}','{row[3].value}','{unit_shop_ids[0]}','{unit_shop_ids[1]}','{row[8].value}','{cus_id}','{vehicle_id}','{row[9].value}','{job_types[row[10].value.strip().lower()]}','{int(row[11].value):.2f}','{technicians[fst_tech]}','{get_partial_amount(rate[0][0],row[11].value)}','{technicians[sec_tech]}','{get_partial_amount(rate[0][1],row[11].value)}','{technicians[thrd_tech]}','{get_partial_amount(rate[0][2],row[11].value)}','{technicians[frth_tech]}','{get_partial_amount(rate[0][3],row[11].value)}','{technicians[lst_tech]}','{get_partial_amount(rate[0][4],row[11].value)}','{eachJob_concatenated}','{rate[1]}','{ownership_id}'),"""
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
            elif excel_file_type == 'brand-model':
                eachJob_insert_query = "INSERT INTO vehicle_model(brand_id,name) VALUES"
                for row_counter,row in enumerate(worksheet.iter_rows(min_row=2),start=2):
                    if None in (row[0].value,row[1].value) or row[0].value.strip() == "" or row[1].value.strip() == "":
                        return redirect(url_for('views.show_service_datas',typ=view_type,mgs=f"Invalid or Blank field at row {row_counter}"))        
                    cur.execute(f"INSERT INTO vehicle_brand (name) VALUES('{row[0].value.strip()}') ON CONFLICT (name) DO UPDATE set name = '{row[0].value.strip()}' RETURNING id;")
                    eachJob_insert_query += f"({cur.fetchall()[0][0]},'{row[1].value}'),"
                conflict_unique_column = "name"
            cur.execute(eachJob_insert_query[:-1] + f" ON CONFLICT ({conflict_unique_column}) DO NOTHING;")
            conn.commit()
            cur.close()
            conn.close()
        else:
            return redirect(url_for('views.show_service_datas',typ=view_type,mgs=f'<strong> Invalid Excel File Type.. <&#47;strong>'))
    return redirect(url_for('views.show_service_datas',typ=view_type))

@imports.route("/create-form/<typ>")
def show_create_form(typ,mgs=None):
    conn = db_connect()
    cur = conn.cursor()
    result = ["","",""]
    if typ == 'service-datas':
        user_roles = tuple(request.cookies.get("user_roles").split(","))
        cur.execute("SELECT id,name FROM technicians WHERE shop_id in %s;",(user_roles,))
        result.append(cur.fetchall())
        cur.execute("SELECT id,name FROM jobType;")
        result.append(cur.fetchall())
        cur.execute("SELECT unique_rate FROM pic;")
        result.append(cur.fetchall())
        cur.execute("SELECT id,short_name,name FROM state;")
        result.append(cur.fetchall())
        cur.execute("SELECT id,name FROM vehicle_brand;")
        result.append(cur.fetchall())
        result.append(datetime.now().year)
        cur.execute("SELECT name FROM customer;")
        result.append(cur.fetchall())
    elif typ == 'customers-create':
        result = [datetime.now().strftime("%Y-%m-%d")]
        cur.execute("SELECT 'CUS'||LPAD((id+1)::text,7,'0') FROM customer ORDER BY id DESC LIMIT 1;")
        result.append(cur.fetchall()[0][0])
        cur.execute("SELECT id,name FROM state;")
        result.append(cur.fetchall())
        return render_template('registration_form.html',result=result,typ=typ)
    elif typ == 'vehicles-create':
        result = [datetime.now().strftime("%Y-%m-%d")]
        cur.execute("SELECT name FROM vehicle_brand;")
        result.append(cur.fetchall())
        cur.execute("SELECT short_name FROM state;")
        result.append(cur.fetchall())
        result.append(datetime.now().year)
        return render_template('registration_form.html',result=result,typ=typ)  

    return render_template('input_form.html',result=result,mgs=mgs)

@imports.route("/keep-in-import/<typ>",methods=['POST'])
def keep_in_import(typ):
    if request.method == 'POST':
        mgs = None
        conn = db_connect()
        cur = conn.cursor()
        if typ == 'service-datas':
            conflict_unique_column = 'eachjob_concatenated'
            eachJob_insert_query = """ INSERT INTO eachJob (job_date,job_no,business_unit_id,shop_id,invoice_no,customer_id,vehicle_id,job_name,
                job_type_id,total_amt,fst_pic_id,fst_pic_amt,sec_pic_id,sec_pic_amt,thrd_pic_id,thrd_pic_amt,frth_pic_id,
                frth_pic_amt,lst_pic_id,lst_pic_amt,eachJob_concatenated,pic_rate_id,ownership_id) VALUES """
            edit = request.form.get("newOrEdit")
            #
            job_no = request.form.get("jobNo")
            invoice_no = request.form.get("invoiceNo")
            job_date = request.form.get("jobDate")
            shop_id = request.form.get("shop")
            cur.execute("SELECT business_unit_id FROM shop WHERE id = %s;",(shop_id,))
            unit_id = cur.fetchall()[0][0]
            #
            descriptions = request.form.getlist("description")[1:]
            job_types = [data.strip() for data in request.form.getlist('jobType')[1:]]
            cur.execute("SELECT fst_rate,sec_rate,thrd_rate,frth_rate,lst_rate,unique_rate,id FROM pic;")
            all_rates = {data[5]:[data[:5],data[6]] for data in cur.fetchall()}
            cur.execute("SELECT id,name FROM technicians;")
            all_technicians = {data[1]:data[0] for data in cur.fetchall()}
            #
            pic_ones = [data for data in request.form.getlist("picOne")[1:] ]
            pic_twos = [data for data in request.form.getlist("picTwo")[1:] ]
            pic_threes = [data for data in request.form.getlist("picThree")[1:] ]
            pic_fours = [data for data in request.form.getlist("picFour")[1:] ]
            pic_fives = [data for data in request.form.getlist("picFive")[1:] ]
            pic_rates = [data.split(",") for data in request.form.getlist("pic-rate")]
            #
            job_costs = request.form.getlist("jobCost")[1:]
            #
            if edit:
                old_job_no = request.form.get("oldJobNo")
                print(get_data('eachJobDelForm',old_job_no))

            vehicle_id = request.form.get("vehicleInformation")
            new_onwership = False
            if request.form.get("vehicleInformation") == "None":
                plate = request.form.get("regState") + request.form.get("regPrefix") + request.form.get("regDigits")
                model = request.form.get("model_id")
                brand = request.form.get("brand_id")
                year = request.form.get("year")
                cur.execute("INSERT INTO vehicle (plate,model_id,brand_id,year) VALUES (%s,%s,%s,%s) RETURNING id;",(plate,model,brand,year)) 
                vehicle_id = cur.fetchall()[0][0]     
                new_onwership = True    
            customer_id = request.form.get("customerInformation")
            if request.form.get("customerInformation") == "None":
                cus_name = request.form.get("customerName")
                address = request.form.get("fullAddress")
                state_id = request.form.get("state")
                phone = request.form.get("phone")
                cur.execute("INSERT INTO customer (name,address,phone,state_id) VALUES (%s,%s,%s,%s) RETURNING id;",(cus_name,address,phone,state_id))
                customer_id = cur.fetchall()[0][0]
                new_onwership = True
            if new_onwership:
                cur.execute("INSERT INTO ownership (customer_id,vehicle_id,start_date,unique_owner) VALUES (%s,%s,%s,%s) RETURNING id;",(customer_id,vehicle_id,datetime.now().strftime("%Y-%m-%d"),str(vehicle_id)+'-'+str(customer_id)))
            else:
                cur.execute("SELECT id FROM ownership WHERE customer_id = %s and vehicle_id = %s;",(customer_id,vehicle_id))                
            ownership_id = cur.fetchall()[0][0]
            cur.execute("INSERT INTO psfu (job_no,job_date,shop_id,psfu_concatenated) VALUES (%s,%s,%s,%s) ON CONFLICT (psfu_concatenated) DO NOTHING;",(job_no,job_date,shop_id,job_no+job_date+shop_id))
            # print(descriptions)
            # print(job_types)
            # print(pic_ones)
            # print(pic_twos)
            # print(pic_threes)
            # print(pic_fours)
            # print(pic_fives)
            # print(pic_rates)            
            #
            for data in zip(descriptions,job_types,pic_ones,pic_twos,pic_threes,pic_fours,pic_fives,job_costs,pic_rates):
                print(data)
                eachJob_concatenated = job_date.replace("-","/") + job_no + data[0]
                eachJob_insert_query += f"""('{job_date}','{job_no}','{unit_id}','{shop_id}','{invoice_no}','{customer_id}','{vehicle_id}','{data[0]}',
                '{data[1]}','{data[7]}','{all_technicians.get(data[2],0)}','{get_partial_amount(data[8][0],data[7])}','{all_technicians.get(data[3],0)}','{get_partial_amount(data[8][1],data[7])}','{all_technicians.get(data[4],0)}','{get_partial_amount(data[8][2],data[7])}','{all_technicians.get(data[5],0)}','{get_partial_amount(data[8][3],data[7])}','{all_technicians.get(data[6],0)}','{get_partial_amount(data[8][4],data[7])}','{eachJob_concatenated}','{all_rates[",".join(data[8])][1]}','{ownership_id}'),"""
            cur.execute(eachJob_insert_query[:-1] + f" ON CONFLICT ({conflict_unique_column}) DO NOTHING;")
            conn.commit()
            return redirect(url_for('imports.show_create_form',typ='service-datas'))
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
            shop_name = request.form.getlist("shop")
            shop_name = shop_name[1] if idd else shop_name[0] 
            cur.execute("SELECT business_unit_id,id FROM shop WHERE name = %s;",(shop_name,))
            data = cur.fetchall()
            if idd:
                if len(data) == 0:
                    mgs = 'Invalid Shop / Business Unit'
                else:
                    cur.execute(f""" UPDATE technicians SET name = '{tech_name[1]}',business_unit_id = '{data[0][0]}',shop_id = '{data[0][1]}' WHERE id = '{idd}' and NOT EXISTS ( SELECT 1 FROM technicians WHERE name = '{tech_name[1]}' and business_unit_id = '{data[0][0]}' and shop_id = '{data[0][1]}') ;""")
            else:
                if len(data) == 0:
                    mgs = 'Invalid Shop / Business Unit'
                else:
                    cur.execute(f""" INSERT INTO technicians (name,business_unit_id,shop_id) VALUES ('{tech_name[0]}','{data[0][0]}','{data[0][1]}') ON CONFLICT (name) DO NOTHING;""")
        elif typ == 'jobType':
            idd = request.form.get("idd")
            job_type = request.form.getlist("jobType")
            if idd:
                cur.execute(f""" UPDATE jobType SET name = '{job_type[1]}' WHERE id = '{idd}' and NOT EXISTS ( SELECT 1 FROM jobtype WHERE name = '{job_type[1]}');""")
            else:
                 cur.execute(f""" INSERT INTO jobType (name) VALUES ('{job_type[0]}') ON CONFLICT (name) DO NOTHING;""")
        elif typ == 'customers':
            reg_date = request.form.get("register-date")
            name = request.form.get("name")
            state = request.form.get("state")
            address = request.form.get("address")
            phone = request.form.get("phone")
            vehicle_ids = request.form.getlist("vehicleIds")
            customer_id = request.form.get("customerId")
            unique_phone_query = f"AND id <> '{customer_id}'" if customer_id else ""
            cur.execute(f"SELECT id FROM customer WHERE phone = '{phone}' {unique_phone_query};")     
            if customer_id:
                if len(cur.fetchall()) == 0:
                    cur.execute("UPDATE customer SET name = %s,state_id = %s,address = %s,phone = %s,registered_date = %s WHERE id = %s;",(name,state,address,phone,reg_date,customer_id))
                else:
                    mgs = f"Phone - {phone} is already existed.."                    
                for vehicle_id in vehicle_ids:
                    cur.execute("INSERT INTO customer (vehicle_id,customer_id,unique_owner) VALUES (%s,%s,%s) ON CONFLICT (unique_owner) DO NOTHING;",(vehicle_id,customer_id,vehicle_id + '-' +customer_id))     
            else:
                if len(cur.fetchall()) == 0:
                    cur.execute("INSERT INTO customer (name,address,phone,state_id,registered_date) VALUES (%s,%s,%s,%s,%s);",(name,address,phone,state,reg_date))
                else:
                    mgs = f"Phone - {phone} is already existed.."
        elif typ == 'vehicles':
            vehicle_id = request.form.get("vehicle-id")
            reg_date = request.form.get("register-date")
            plate = request.form.get("fst-part") + request.form.get("sec-part") + request.form.get("thrd-part")
            brand_id = request.form.get("brand_id")
            model_id = request.form.get("model_id")
            year = request.form.get("year")
            unique_plate_query = f"AND id <> '{vehicle_id}'" if vehicle_id else ""
            cur.execute(f"SELECT id FROM vehicle WHERE plate = '{plate}' {unique_plate_query};")  
            if vehicle_id:
                if len(cur.fetchall()) == 0:
                    cur.execute("UPDATE vehicle SET register_date = %s,plate = %s,brand_id = %s,model_id = %s,year = %s WHERE id = %s;",(reg_date,plate,brand_id,model_id,year,vehicle_id))
                else:
                    mgs = f"Plate - {plate} is already registered in our system.."
            else:
                if len(cur.fetchall()) == 0:
                    cur.execute("INSERT INTO vehicle (plate,brand_id,model_id,year,register_date) VALUES (%s,%s,%s,%s,%s);",(plate,brand_id,model_id,year,reg_date))
                else:
                    mgs = f"Plate - {plate} is already registered in our system.."
        elif typ == 'brand':
            brand_name = request.form.get("brand")
            model_name = request.form.get("model")
            cur.execute("INSERT INTO vehicle_brand(name) VALUES(%s) ON CONFLICT (name) DO UPDATE SET name = %s RETURNING id;",(brand_name,brand_name))
            brand_id = cur.fetchall()[0][0]
            cur.execute("SELECT id FROM vehicle_model WHERE brand_id = %s AND name = %s;",(brand_id,model_name))
            if len(cur.fetchall()) == 0:
                cur.execute("INSERT INTO vehicle_model(brand_id,name) VALUES (%s,%s);",(brand_id,model_name))
        conn.commit()
    return redirect(url_for('views.show_service_datas',typ=typ,mgs=mgs))
