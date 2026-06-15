import os
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
from chaosmanager import ChaosManager
from chaos import Equipment

app = Flask(__name__)
manager = ChaosManager()

UPLOAD_FOLDER = os.path.join('static', 'img')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    search_query = request.args.get('search_query', '')
    search_results = None
    if search_query:
        equip_list = search_query.split(',')
        search_results = manager.search_farm_locations(equip_list)
    return render_template('index.html', search_results=search_results, search_query=search_query)

@app.route('/chaos')
def chaos_list():
    return render_template('chaos_list.html', chaos_maps=manager.data["chaos_maps"])

@app.route('/chaos/add', methods=['POST'])
def add_chaos():
    location = request.form.get('location')
    if location:
        manager.add_chaos(location.strip())
    return redirect(url_for('chaos_list'))

@app.route('/chaos/update-view')
def update_chaos_view():
    return render_template('update_chaos.html', chaos_maps=manager.data["chaos_maps"])

@app.route('/chaos/update', methods=['POST'])
def update_chaos():
    old_location = request.form.get('old_location')
    new_location = request.form.get('new_location')
    if old_location and new_location:
        manager.update_chaos(old_location.strip(), new_location.strip())
    return redirect(url_for('chaos_list'))

@app.route('/chaos/delete/<location>')
def delete_chaos(location):
    manager.delete_chaos(location)
    return redirect(url_for('chaos_list'))

# --- TRANG DANH SÁCH VẬT PHẨM ---
@app.route('/equipment')
def equipment_list():
    # Chuẩn bị dữ liệu hiển thị lồng: Đổi từ Danh sách Tên vật phẩm thành Object đầy đủ thuộc tính
    full_mapped_data = {}
    for loc, item_names in manager.data["chaos_maps"].items():
        full_mapped_data[loc] = []
        for name in item_names:
            eq_detail = manager.get_equipment_by_name(name)
            if eq_detail:
                full_mapped_data[loc].append(eq_detail)

    return render_template('equipment_list.html', data=full_mapped_data, all_equipments=manager.data["equipments"])

@app.route('/equipment/add', methods=['POST'])
def add_equipment():
    # Lấy toàn bộ danh sách các Map được tích chọn
    locations = request.form.getlist('locations') 
    name = request.form.get('name')
    eq_type = request.form.get('type')
    level = request.form.get('level')
    effect = request.form.get('effect')
    
    img_path = ""
    if 'img' in request.files:
        file = request.files['img']
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            img_path = f"/{app.config['UPLOAD_FOLDER']}/{filename}"

    # Kiểm tra người dùng phải điền tên vật phẩm và tích ít nhất 1 ô map
    if name and locations:
        equip = Equipment(name.strip(), eq_type, effect.strip(), level, img_path)
        
        # Vòng lặp chạy qua từng map được tích chọn để lưu liên kết rớt đồ
        for location in locations:
            manager.add_equipment(location, equip)
            
    return redirect(url_for('equipment_list'))

# --- TRANG SỬA VẬT PHẨM TẬP TRUNG ---
@app.route('/equipment/update-view/<name>')
def update_equipment_view(name):
    target_item = manager.get_equipment_by_name(name)
    return render_template('update_equipment.html', item=target_item)

@app.route('/equipment/update', methods=['POST'])
def update_equipment():
    old_name = request.form.get('old_name')
    name = request.form.get('name')
    eq_type = request.form.get('type')
    level = request.form.get('level')
    effect = request.form.get('effect')
    current_img = request.form.get('current_img', '')
    
    if 'img' in request.files:
        file = request.files['img']
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            current_img = f"/{app.config['UPLOAD_FOLDER']}/{filename}"

    if old_name and name:
        updated_equip = Equipment(name.strip(), eq_type, effect.strip(), level, current_img)
        manager.update_equipment(old_name, updated_equip)
    return redirect(url_for('equipment_list'))

@app.route('/equipment/delete/<location>/<name>')
def delete_equipment(location, name):
    manager.delete_equipment_from_map(location, name)
    return redirect(url_for('equipment_list'))

if __name__ == '__main__':
    app.run(debug=True)