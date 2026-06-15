def update_equipment(data, chaos_name, old_item_name, new_item_name):
    if chaos_name in data and old_item_name in data[chaos_name]:
        idx = data[chaos_name].index(old_item_name)
        data[chaos_name][idx] = new_item_name
    return data