from flask import Flask, render_template, request, jsonify
import json
from datetime import datetime
import numpy as np
import re
from operator import itemgetter

app = Flask(__name__)

# Initialize PC information
pc_data = []
pc_number = 21
# Load existing PC data from JSON file


def sorted_nicely(l, key):
    """ Sort the given iterable in the way that humans expect."""
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda item: [ convert(c) for c in re.split('([0-9]+)', key(item)) ]
    return sorted(l, key = alphanum_key)

def load_pc_data():
    
    with open('pc_data.json', 'r') as file:
        data = json.load(file)
        return data.get('items', []), data.get('pcs', [])
    
def update_pc_status(pc_data, pc_details):
    checked_in = {}
    checked_out = {}
    
    for pc_detail in pc_details:
        pc_name = pc_detail[0]
        checked_in[pc_name] = []
        checked_out[pc_name] = []
    
    for item in pc_data:
        pc_name = item[0]
        # print (item)
        if pc_name in checked_in or pc_name in checked_out:
            if item[2] != '' and item[3] == '':
                checked_in[pc_name].append(item)
            else:
                checked_out[pc_name].append(item)

    # print ('1: ', checked_in)
    # print ('2: ',checked_out)
    return checked_in, checked_out

# Save PC data to JSON file
def save_pc_data():
    with open('pc_data.json', 'w') as file:
        json.dump({'items': pc_data}, file, indent=2)


# Custom JSON encoder
def custom_json_encoder(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj

# Custom JSON decoder
def custom_json_decoder(obj):
    if 'checkintime' in obj and obj['jmn'] != '':
        obj['checkintime'] = datetime.fromisoformat(obj['checkintime'])
    if 'checkouttime' in obj and obj['checkouttime'] != '':
        obj['checkouttime'] = datetime.fromisoformat(obj['checkouttime'])
    return obj

# Home page
@app.route('/')
def home():
    global pc_data
    pc_data, pc_details = load_pc_data()
    pc_data = sorted_nicely(pc_data, itemgetter(0))
    pc_details = sorted_nicely(pc_details, itemgetter(0))

    checked_in_data, checked_out_data = update_pc_status(pc_data, pc_details)
    #print("PC Data:", pc_data)
    return render_template('home.html', pc_data=pc_data, pc_details = pc_details, checked_in=checked_in_data, checked_out=checked_out_data, pc_number=len(pc_details))

# PC Usage page
@app.route('/pc_usage')
def pc_usage():
    
    pc_data, pc_info = load_pc_data()
    
    pc_dict = {}
   
    owners = set() 
    for info in pc_info:
        pc_dict[info[0]] = info
        
    pc_data_for_display = []
    for data in pc_data:
        if data[0] in pc_dict:
            owners.add(data[1])
            pc_data_for_display.append([data[0]]+[pc_dict[data[0]][1]]+data[1:])
   
    
    #print("PC Data for display:", pc_data_for_display)
    
    pc_data_for_display.insert(0,["#", "Resource", "Platform", "Owner", "Reserved at", "Returned at", "Purpose"])
    
    return render_template('pc_usage.html', pc_data=pc_data_for_display, pc_info = pc_info, owner_data = list(owners), pc_number=pc_number)

# PC Details page
@app.route('/pc_details')
def pc_details():
    global pc_data
    pc_data, pc_info = load_pc_data()

    pc_info = sorted_nicely(pc_info, itemgetter(0))
    pc_info.insert(0,["#", "Resource", "Platform", "Resource IP", "SUT IP"])
    #print ('pc_info:', pc_info)
    return render_template('pc_details.html', pc_details=pc_info)

@app.route('/add_pc', methods=['POST'])
def add_pc():
    try:
        data = request.get_json()

        # Debug statement
        #print("Received form data:", data)

        # Extract data fields
        hostname = data[1]
        platform = data[2]
        resourceip_address = data[3]
        sutip_address = data[4]

        # Update pc_data.json with the new reservation
        pc_data, pc_info = load_pc_data()
        pc_info.append([hostname, platform, resourceip_address, sutip_address])

        data = {}
        data["pcs"] = pc_info
        data["items"] = pc_data
        # Save the updated data to pc_data.json
        with open('pc_data.json', 'w') as file:
            json.dump(data, file)

        return jsonify({'success': True, 'message': 'Add successful!'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/edit_pc', methods=['POST'])
def edit_pc():
    try:
        pc_info = request.get_json()[1:]
        print ('pc_info: ', pc_info)
        pc_info  = [ info[1:] for info in pc_info]
        # Debug statement
        #print("Received form data:", pc_info)

        # Update pc_data.json with the new reservation
        pc_data, _ = load_pc_data()

        data = {}
        
        data["pcs"] = pc_info
        data["items"] = pc_data
        # Save the updated data to pc_data.json'
        
        with open('pc_data.json', 'w') as file:
            json.dump(data, file)

        return jsonify({'success': True, 'message': 'Edit successful!'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    

@app.route('/remove_pc', methods=['POST'])
def remove_pc():
    try:
        pc_info = request.get_json()[1:]
        pc_info  = [ info[1:] for info in pc_info]
        # Debug statement
        #print("Received form data:", pc_info)

        # Update pc_data.json with the new reservation
        pc_data, _ = load_pc_data()

        data = {}
        
        data["pcs"] = pc_info
        data["items"] = pc_data
        # Save the updated data to pc_data.json'
        
        with open('pc_data.json', 'w') as file:
            json.dump(data, file)

        return jsonify({'success': True, 'message': 'Remove successful!'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    
@app.route('/reserve_pc', methods=['POST'])
def reserve_pc():
    try:
        # Get form data from the request
        hostname = request.form.get('hostname')
        owner = request.form.get('owner')
        checkintime = request.form.get('checkintime').replace('T','')
        print ('checkintime:', checkintime)
        purpose = request.form.get('purpose')
        
        #print(f"Received form data: Hostname={hostname}, Owner={owner}, Checkintime={checkintime}, Purpose={purpose}")


        # Validate the data (implement your own validation logic)

        # Update pc_data.json with the new reservation
        pc_data.insert(0,[hostname, owner, checkintime, '', purpose])
        
        _, pc_info = load_pc_data()


        data = {}
        data["pcs"] = pc_info
        data["items"] = pc_data
        # Save the updated data to pc_data.json
        with open('pc_data.json', 'w') as file:
            json.dump(data, file)

        # Update checked_in and checked_out dictionaries
        update_pc_status(pc_data, pc_info)

        return jsonify({'success': True, 'message': 'Reservation successful!'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    
# Return PC endpoint
@app.route('/return_pc', methods=['POST'])
def return_pc():
    
    
    global pc_data
    hostname = request.form.get('hostname')
    checkouttime = request.form.get('checkouttime')
    
    
    print(f"Received form data: Hostname={hostname}, Checkouttime={checkouttime}")


    # Find the PC in pc_data and update checkouttime and other details
    for i,pc in enumerate(pc_data):
        if pc_data[i][0] == hostname and pc_data[i][-2] == '':
            pc_data[i][-2] = checkouttime
            break
    
    _, pc_info = load_pc_data()
    data = {}
    data["pcs"] = pc_info
    data["items"] = pc_data
    # Other updates as needed
    
    with open('pc_data.json', 'w') as file:
        json.dump(data, file)

    return jsonify({'success': True})

    

if __name__ == '__main__':
    app.run(debug=True)

